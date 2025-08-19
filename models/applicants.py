from utils.database import get_db_connection
from psycopg2.extras import RealDictCursor
import pandas as pd
from datetime import datetime, date
from models.test_scores import (
    process_toefl_scores,
    process_ielts_scores,
    process_other_test_scores,
)
from models.test_scores import (
    process_toefl_scores,
    process_ielts_scores,
    process_other_test_scores,
)
from models.institutions import process_institution_info


def calculate_age(birth_date):
    """Calculate age from birth date"""
    if not birth_date:
        return None

    today = date.today()
    age = today.year - birth_date.year

    # Check if birthday has occurred this year
    if today.month < birth_date.month or (
        today.month == birth_date.month and today.day < birth_date.day
    ):
        age -= 1

    return age


def create_or_get_sessions(cursor, program_code, program, session_abbrev):
    """Create or get session based on CSV data"""
    try:
        # Truncate values to fit database column limits
        program_code = program_code[:10]  # program_code VARCHAR(10)
        program = program[:20]  # program VARCHAR(20)
        session_abbrev = session_abbrev[:6]  # session_abbrev VARCHAR(6)

        # Extract year from session_abbrev (first 4 characters)
        if len(session_abbrev) < 4:
            return (
                None,
                f"Session abbreviation '{session_abbrev}' is too short (need at least 4 characters)",
            )

        year_str = session_abbrev[:4]

        if not year_str.isdigit():
            return (
                None,
                f"First 4 characters of session '{session_abbrev}' are not numeric: '{year_str}'",
            )

        year = int(year_str)

        # Create name in format "Session year - year+1" (truncate to 20 chars if needed)
        name = f"Session {year} - {year + 1}"
        if len(name) > 20:
            name = name[:20]

        # Check if session already exists
        cursor.execute(
            """
            SELECT id FROM sessions 
            WHERE program_code = %s AND year = %s AND session_abbrev = %s
            """,
            (program_code, year, session_abbrev),
        )

        existing_session = cursor.fetchone()
        if existing_session:
            return existing_session[0], f"Found existing session: {name}"

        # Create new session
        cursor.execute(
            """
            INSERT INTO sessions (program_code, program, session_abbrev, year, name, description, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                program_code,
                program,
                session_abbrev,
                year,
                name,
                "",  # Empty description
                datetime.now(),
                datetime.now(),
            ),
        )

        session_id = cursor.fetchone()[0]
        return session_id, f"Created new session: {name} (ID: {session_id})"

    except ValueError as e:
        return None, f"Error parsing year from session_abbrev '{session_abbrev}': {e}"
    except Exception as e:
        return None, f"Database error creating session: {e}"


def compute_english_status(user_code: str, not_required_rule=None):
    """
    Compute english_status/english_description/english for a single applicant,
    using the first test that meets the minimum requirements in this order:
    TOEFL -> IELTS -> MELAB -> PTE -> CAEL.

    english = TRUE iff english_status in ('Passed','Not Required').
    """

    # Thresholds
    TOEFL_LR_MIN = 22  # listening & reading
    TOEFL_WS_MIN = 21  # writing & speaking
    TOEFL_TOTAL_MIN = 90

    IELTS_EACH_MIN = 6.0
    IELTS_TOTAL_MIN = 6.5

    MELAB_TOTAL_MIN = 64
    PTE_TOTAL_MIN = 65

    CAEL_EACH_MIN = 60

    status = None
    desc = None
    failed_tests = []

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            # Optional “Not Required” rule hook
            if callable(not_required_rule):
                nr_ok, nr_reason = not_required_rule(cur, user_code)
                if nr_ok:
                    status = "Not Required"
                    desc = nr_reason or "Exempt from English requirement"
                    cur.execute(
                        """
                        UPDATE application_info
                           SET english_status = %s,
                               english_description = %s,
                               english = TRUE
                         WHERE user_code = %s
                        """,
                        (status, desc, user_code),
                    )
                    conn.commit()
                    return

            # 1) TOEFL (regular -> MyBest only if regular fails)
            cur.execute(
                """
                SELECT toefl_number, listening, structure_written, reading, speaking,
                       total_score, mybest_listening, mybest_writing,
                       mybest_reading, mybest_speaking, mybest_total
                  FROM toefl
                 WHERE user_code = %s
                 ORDER BY toefl_number
                """,
                (user_code,),
            )
            for row in cur.fetchall():
                L = (
                    int(row["listening"])
                    if row["listening"] not in (None, "")
                    else None
                )
                W = (
                    int(row["structure_written"])
                    if row["structure_written"] not in (None, "")
                    else None
                )
                R = int(row["reading"]) if row["reading"] not in (None, "") else None
                S = int(row["speaking"]) if row["speaking"] not in (None, "") else None
                T = (
                    int(row["total_score"])
                    if row["total_score"] not in (None, "")
                    else None
                )

                mL = (
                    int(row["mybest_listening"])
                    if row["mybest_listening"] not in (None, "")
                    else None
                )
                mW = (
                    int(row["mybest_writing"])
                    if row["mybest_writing"] not in (None, "")
                    else None
                )
                mR = (
                    int(row["mybest_reading"])
                    if row["mybest_reading"] not in (None, "")
                    else None
                )
                mS = (
                    int(row["mybest_speaking"])
                    if row["mybest_speaking"] not in (None, "")
                    else None
                )
                mT = (
                    int(row["mybest_total"])
                    if row["mybest_total"] not in (None, "")
                    else None
                )

                num = row["toefl_number"] or 1

                # Regular attempt
                if all(v is not None for v in (L, W, R, S, T)) and (
                    L >= TOEFL_LR_MIN
                    and R >= TOEFL_LR_MIN
                    and W >= TOEFL_WS_MIN
                    and S >= TOEFL_WS_MIN
                    and T >= TOEFL_TOTAL_MIN
                ):
                    status = "Passed"
                    desc = f"TOEFL{num}, score is above the minimum requirement (90)"
                    break

                # MyBest composite
                elif all(v is not None for v in (mL, mW, mR, mS, mT)) and (
                    mL >= TOEFL_LR_MIN
                    and mR >= TOEFL_LR_MIN
                    and mW >= TOEFL_WS_MIN
                    and mS >= TOEFL_WS_MIN
                    and mT >= TOEFL_TOTAL_MIN
                ):
                    status = "Passed"
                    desc = f"TOEFL{num} (MyBest), score is above the minimum requirement (90)"
                    break

                failed_tests.append(f"TOEFL{num}")

            if status == "Passed":
                cur.execute(
                    """
                    UPDATE application_info
                       SET english_status = %s,
                           english_description = %s,
                           english = TRUE
                     WHERE user_code = %s
                    """,
                    (status, desc, user_code),
                )
                conn.commit()
                return

            # 2) IELTS
            cur.execute(
                """
                SELECT ielts_number, listening, reading, writing, speaking, total_band_score
                  FROM ielts
                 WHERE user_code = %s
                 ORDER BY ielts_number
                """,
                (user_code,),
            )
            for row in cur.fetchall():
                L = (
                    float(row["listening"])
                    if row["listening"] not in (None, "")
                    else None
                )
                R = float(row["reading"]) if row["reading"] not in (None, "") else None
                W = float(row["writing"]) if row["writing"] not in (None, "") else None
                S = (
                    float(row["speaking"])
                    if row["speaking"] not in (None, "")
                    else None
                )
                T = (
                    float(row["total_band_score"])
                    if row["total_band_score"] not in (None, "")
                    else None
                )
                num = row["ielts_number"] or 1

                if all(v is not None for v in (L, R, W, S, T)) and (
                    min(L, R, W, S) >= IELTS_EACH_MIN and T >= IELTS_TOTAL_MIN
                ):
                    status = "Passed"
                    desc = f"IELTS{num}, score is above the minimum requirement (6.5 overall, 6.0 each)"
                    break

                failed_tests.append(f"IELTS{num}")

            if status == "Passed":
                cur.execute(
                    """
                    UPDATE application_info
                       SET english_status = %s,
                           english_description = %s,
                           english = TRUE
                     WHERE user_code = %s
                    """,
                    (status, desc, user_code),
                )
                conn.commit()
                return

            # 3) MELAB
            cur.execute("SELECT total FROM melab WHERE user_code = %s", (user_code,))
            melab = cur.fetchone()
            if melab is not None:
                total = (
                    int(melab["total"]) if melab["total"] not in (None, "") else None
                )
                if total is not None and total >= MELAB_TOTAL_MIN:
                    status = "Passed"
                    desc = "MELAB, score is above the minimum requirement (64)"
                else:
                    failed_tests.append("MELAB")

            if status == "Passed":
                cur.execute(
                    """
                    UPDATE application_info
                       SET english_status = %s,
                           english_description = %s,
                           english = TRUE
                     WHERE user_code = %s
                    """,
                    (status, desc, user_code),
                )
                conn.commit()
                return

            # 4) PTE
            cur.execute("SELECT total FROM pte WHERE user_code = %s", (user_code,))
            pte = cur.fetchone()
            if pte is not None:
                total = int(pte["total"]) if pte["total"] not in (None, "") else None
                if total is not None and total >= PTE_TOTAL_MIN:
                    status = "Passed"
                    desc = "PTE, score is above the minimum requirement (65)"
                else:
                    failed_tests.append("PTE")

            if status == "Passed":
                cur.execute(
                    """
                    UPDATE application_info
                       SET english_status = %s,
                           english_description = %s,
                           english = TRUE
                     WHERE user_code = %s
                    """,
                    (status, desc, user_code),
                )
                conn.commit()
                return

            # 5) CAEL
            cur.execute(
                """
                SELECT reading, listening, writing, speaking
                  FROM cael
                 WHERE user_code = %s
                """,
                (user_code,),
            )
            cael = cur.fetchone()
            if cael is not None:
                R = int(cael["reading"]) if cael["reading"] not in (None, "") else None
                L = (
                    int(cael["listening"])
                    if cael["listening"] not in (None, "")
                    else None
                )
                W = int(cael["writing"]) if cael["writing"] not in (None, "") else None
                S = (
                    int(cael["speaking"])
                    if cael["speaking"] not in (None, "")
                    else None
                )
                if (
                    all(v is not None for v in (R, L, W, S))
                    and min(R, L, W, S) >= CAEL_EACH_MIN
                ):
                    status = "Passed"
                    desc = "CAEL, all sections ≥ 60"
                else:
                    failed_tests.append("CAEL")

            # Finalize result
            if status == "Passed":
                cur.execute(
                    """
                    UPDATE application_info
                       SET english_status = %s,
                           english_description = %s,
                           english = TRUE
                     WHERE user_code = %s
                    """,
                    (status, desc, user_code),
                )
            else:
                if not failed_tests:  # no test rows found at all
                    cur.execute(
                        """
                        UPDATE application_info
                           SET english_status = 'Not Met',
                               english_description = 'No English tests submitted',
                               english = FALSE
                         WHERE user_code = %s
                        """,
                        (user_code,),
                    )
                else:
                    reason = ", ".join(failed_tests)
                    cur.execute(
                        """
                        UPDATE application_info
                           SET english_status = 'Not Met',
                               english_description = %s,
                               english = FALSE
                         WHERE user_code = %s
                        """,
                        (f"{reason} are below the minimum requirement", user_code),
                    )

        conn.commit()

    finally:
        try:
            conn.close()
        except Exception:
            pass


def compute_english_status_for_all(not_required_rule=None):
    """
    Recompute english_status/english_description/english for every row
    in application_info by calling compute_english_status(user_code).
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT user_code FROM application_info ORDER BY user_code")
            codes = [r["user_code"] for r in cur.fetchall()]
    finally:
        try:
            conn.close()
        except Exception:
            pass

    for code in codes:
        compute_english_status(code, not_required_rule=not_required_rule)


def process_csv_data(df):
    """Process CSV data and insert into sessions, applicant_info and applicant_status tables"""
    conn = get_db_connection()
    touched_user_codes = set()  # Track all applicants we update

    if not conn:
        return False, "Database connection failed", 0

    try:
        cursor = conn.cursor()
        records_processed = 0
        session_id = None

        # Get session info from first row (assuming all rows have same session info)
        if not df.empty:
            first_row = df.iloc[0]
            program_code = str(first_row.get("Program CODE", "")).strip()
            program = str(first_row.get("Program", "")).strip()
            session_abbrev = str(first_row.get("Session", "")).strip()

            # Check for empty or nan values
            if not program_code or program_code == "nan" or program_code == "":
                return (
                    False,
                    f"Invalid Program CODE: '{first_row.get('Program CODE', 'NOT_FOUND')}'",
                    0,
                )
            if not program or program == "nan" or program == "":
                return (
                    False,
                    f"Invalid Program: '{first_row.get('Program', 'NOT_FOUND')}'",
                    0,
                )
            if not session_abbrev or session_abbrev == "nan" or session_abbrev == "":
                return (
                    False,
                    f"Invalid Session: '{first_row.get('Session', 'NOT_FOUND')}'",
                    0,
                )

            sessions_result, message = create_or_get_sessions(
                cursor, program_code, program, session_abbrev
            )
            if sessions_result is None:
                return False, f"Session creation failed: {message}", 0

            session_id = sessions_result
        else:
            return False, "CSV file is empty", 0

        for _, row in df.iterrows():
            user_code = str(row.get("User Code", "")).strip()
            if not user_code or user_code == "nan":
                continue

            # Track if any data changed for this user
            data_changed = False

            # Parse date of birth
            date_birth = None
            if pd.notna(row.get("Date of Birth")):
                try:
                    date_birth = pd.to_datetime(row.get("Date of Birth")).date()
                except:
                    date_birth = None

            # Calculate age
            age = calculate_age(date_birth)

            # Get current timestamp
            current_time = datetime.now()

            # Get UBC Academic History data from CSV
            ubc_academic_history = row.get(
                "{ UBC Academic History List - eVision Record #; Start Date; End Date; Category; Program of Study; Degree Conferred?; Date Conferred; Credential Received; Withdrawal Reasons; Honours }",
                "",
            )

            # Clean up the UBC academic history data - handle NaN/null values
            if (
                pd.isna(ubc_academic_history)
                or str(ubc_academic_history).strip() == "nan"
            ):
                ubc_academic_history = ""
            else:
                ubc_academic_history = str(ubc_academic_history).strip()

            # Check if applicant_info changed by looking at the updated_at after the query
            cursor.execute(
                "SELECT updated_at FROM applicant_info WHERE user_code = %s",
                (user_code,)
            )
            old_info_updated = cursor.fetchone()

            # Insert into applicant_info table (now with session_id and ubc_academic_history)
            applicant_info_query = """
            INSERT INTO applicant_info (
                user_code, session_id, title, family_name, given_name, middle_name, preferred_name,
                former_family_name, gender_code, gender, date_birth, age, country_birth_code,
                country_citizenship_code, country_citizenship, dual_citizenship_code,
                dual_citizenship, primary_spoken_lang_code, primary_spoken_lang,
                other_spoken_lang_code, other_spoken_lang, visa_type_code, visa_type,
                country_code, country, address_line1, address_line2, city,
                province_state_region, postal_code, primary_telephone, secondary_telephone,
                email, aboriginal, first_nation, inuit, metis, aboriginal_not_specified,
                aboriginal_info, academic_history_code, academic_history, ubc_academic_history, interest_code, interest,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s)
            ON CONFLICT (user_code) DO UPDATE SET
                session_id = EXCLUDED.session_id,
                title = EXCLUDED.title,
                family_name = EXCLUDED.family_name,
                given_name = EXCLUDED.given_name,
                middle_name = EXCLUDED.middle_name,
                preferred_name = EXCLUDED.preferred_name,
                former_family_name = EXCLUDED.former_family_name,
                gender_code = EXCLUDED.gender_code,
                gender = EXCLUDED.gender,
                date_birth = EXCLUDED.date_birth,
                age = EXCLUDED.age,
                country_birth_code = EXCLUDED.country_birth_code,
                country_citizenship_code = EXCLUDED.country_citizenship_code,
                country_citizenship = EXCLUDED.country_citizenship,
                dual_citizenship_code = EXCLUDED.dual_citizenship_code,
                dual_citizenship = EXCLUDED.dual_citizenship,
                primary_spoken_lang_code = EXCLUDED.primary_spoken_lang_code,
                primary_spoken_lang = EXCLUDED.primary_spoken_lang,
                other_spoken_lang_code = EXCLUDED.other_spoken_lang_code,
                other_spoken_lang = EXCLUDED.other_spoken_lang,
                visa_type_code = EXCLUDED.visa_type_code,
                visa_type = EXCLUDED.visa_type,
                country_code = EXCLUDED.country_code,
                country = EXCLUDED.country,
                address_line1 = EXCLUDED.address_line1,
                address_line2 = EXCLUDED.address_line2,
                city = EXCLUDED.city,
                province_state_region = EXCLUDED.province_state_region,
                postal_code = EXCLUDED.postal_code,
                primary_telephone = EXCLUDED.primary_telephone,
                secondary_telephone = EXCLUDED.secondary_telephone,
                email = EXCLUDED.email,
                aboriginal = EXCLUDED.aboriginal,
                first_nation = EXCLUDED.first_nation,
                inuit = EXCLUDED.inuit,
                metis = EXCLUDED.metis,
                aboriginal_not_specified = EXCLUDED.aboriginal_not_specified,
                aboriginal_info = EXCLUDED.aboriginal_info,
                academic_history_code = EXCLUDED.academic_history_code,
                academic_history = EXCLUDED.academic_history,
                ubc_academic_history = EXCLUDED.ubc_academic_history,
                interest_code = EXCLUDED.interest_code,
                interest = EXCLUDED.interest,
                updated_at = CASE 
                    WHEN applicant_info.session_id IS DISTINCT FROM EXCLUDED.session_id
                      OR applicant_info.title IS DISTINCT FROM EXCLUDED.title
                      OR applicant_info.family_name IS DISTINCT FROM EXCLUDED.family_name
                      OR applicant_info.given_name IS DISTINCT FROM EXCLUDED.given_name
                      OR applicant_info.middle_name IS DISTINCT FROM EXCLUDED.middle_name
                      OR applicant_info.preferred_name IS DISTINCT FROM EXCLUDED.preferred_name
                      OR applicant_info.former_family_name IS DISTINCT FROM EXCLUDED.former_family_name
                      OR applicant_info.gender_code IS DISTINCT FROM EXCLUDED.gender_code
                      OR applicant_info.gender IS DISTINCT FROM EXCLUDED.gender
                      OR applicant_info.date_birth IS DISTINCT FROM EXCLUDED.date_birth
                      OR applicant_info.age IS DISTINCT FROM EXCLUDED.age
                      OR applicant_info.country_birth_code IS DISTINCT FROM EXCLUDED.country_birth_code
                      OR applicant_info.country_citizenship_code IS DISTINCT FROM EXCLUDED.country_citizenship_code
                      OR applicant_info.country_citizenship IS DISTINCT FROM EXCLUDED.country_citizenship
                      OR applicant_info.dual_citizenship_code IS DISTINCT FROM EXCLUDED.dual_citizenship_code
                      OR applicant_info.dual_citizenship IS DISTINCT FROM EXCLUDED.dual_citizenship
                      OR applicant_info.primary_spoken_lang_code IS DISTINCT FROM EXCLUDED.primary_spoken_lang_code
                      OR applicant_info.primary_spoken_lang IS DISTINCT FROM EXCLUDED.primary_spoken_lang
                      OR applicant_info.other_spoken_lang_code IS DISTINCT FROM EXCLUDED.other_spoken_lang_code
                      OR applicant_info.other_spoken_lang IS DISTINCT FROM EXCLUDED.other_spoken_lang
                      OR applicant_info.visa_type_code IS DISTINCT FROM EXCLUDED.visa_type_code
                      OR applicant_info.visa_type IS DISTINCT FROM EXCLUDED.visa_type
                      OR applicant_info.country_code IS DISTINCT FROM EXCLUDED.country_code
                      OR applicant_info.country IS DISTINCT FROM EXCLUDED.country
                      OR applicant_info.address_line1 IS DISTINCT FROM EXCLUDED.address_line1
                      OR applicant_info.address_line2 IS DISTINCT FROM EXCLUDED.address_line2
                      OR applicant_info.city IS DISTINCT FROM EXCLUDED.city
                      OR applicant_info.province_state_region IS DISTINCT FROM EXCLUDED.province_state_region
                      OR applicant_info.postal_code IS DISTINCT FROM EXCLUDED.postal_code
                      OR applicant_info.primary_telephone IS DISTINCT FROM EXCLUDED.primary_telephone
                      OR applicant_info.secondary_telephone IS DISTINCT FROM EXCLUDED.secondary_telephone
                      OR applicant_info.email IS DISTINCT FROM EXCLUDED.email
                      OR applicant_info.aboriginal IS DISTINCT FROM EXCLUDED.aboriginal
                      OR applicant_info.first_nation IS DISTINCT FROM EXCLUDED.first_nation
                      OR applicant_info.inuit IS DISTINCT FROM EXCLUDED.inuit
                      OR applicant_info.metis IS DISTINCT FROM EXCLUDED.metis
                      OR applicant_info.aboriginal_not_specified IS DISTINCT FROM EXCLUDED.aboriginal_not_specified
                      OR applicant_info.aboriginal_info IS DISTINCT FROM EXCLUDED.aboriginal_info
                      OR applicant_info.academic_history_code IS DISTINCT FROM EXCLUDED.academic_history_code
                      OR applicant_info.academic_history IS DISTINCT FROM EXCLUDED.academic_history
                      OR applicant_info.ubc_academic_history IS DISTINCT FROM EXCLUDED.ubc_academic_history
                      OR applicant_info.interest_code IS DISTINCT FROM EXCLUDED.interest_code
                      OR applicant_info.interest IS DISTINCT FROM EXCLUDED.interest
                    THEN EXCLUDED.updated_at 
                    ELSE applicant_info.updated_at 
                END
            """

            cursor.execute(
                applicant_info_query,
                (
                    user_code,  # user_code
                    session_id,  # session_id
                    row.get("Title"),
                    row.get("Family Name"),
                    row.get("Given Name"),
                    row.get("Middle Name"),
                    row.get("Preferred Name"),
                    row.get("Former Family Name"),
                    row.get("Gender CODE"),
                    row.get("Gender"),
                    date_birth,  # parsed date_birth
                    age,  # calculated age
                    row.get("Country of Birth CODE"),
                    row.get("Country of Current Citizenship CODE"),
                    row.get("Country of Current Citizenship"),
                    row.get("Dual Citizenship CODE"),
                    row.get("Dual Citizenship"),
                    row.get("Primary Spoken Language CODE"),
                    row.get("Primary Spoken Language"),
                    row.get("Other Spoken Language CODE"),
                    row.get("Other Spoken Language"),
                    row.get("Visa Type CODE"),
                    row.get("Visa Type"),
                    row.get("Country CODE"),
                    row.get("Country"),
                    row.get("Address Line 1"),
                    row.get("Address Line 2"),
                    row.get("City"),
                    row.get("Province, State or Region"),
                    row.get("Postal Code"),
                    row.get("Primary Telephone"),
                    row.get("Secondary Telephone"),
                    row.get("Email"),
                    row.get("Aboriginal"),  # aboriginal
                    row.get("Aboriginal Type First Nations"),  # first_nation
                    row.get("Aboriginal Type Inuit"),  # inuit
                    row.get("Aboriginal Type Métis"),  # metis
                    row.get(
                        "Aboriginal Type Not Specified"
                    ),  # aboriginal_not_specified
                    row.get("Aboriginal Info"),
                    row.get("Academic History Source CODE"),
                    row.get("Academic History Source Value"),  # Fixed typo: removed "I"
                    ubc_academic_history,  # Add the UBC Academic History data
                    row.get("Source of Interest in UBC CODE"),
                    row.get("Source of Interest in UBC"),
                    current_time,  # created_at
                    current_time,  # updated_at
                ),
            )

            # Check if applicant_info actually changed
            cursor.execute(
                "SELECT updated_at FROM applicant_info WHERE user_code = %s",
                (user_code,)
            )
            new_info_updated = cursor.fetchone()
            
            if old_info_updated is None:  # New record
                data_changed = True
            elif old_info_updated and new_info_updated:
                # Check if updated_at changed (meaning data changed)
                if old_info_updated[0] != new_info_updated[0]:
                    data_changed = True

            # Parse dates for student_status
            app_start = None
            submit_date = None

            if pd.notna(row.get("Application Started")):
                try:
                    app_start = pd.to_datetime(row.get("Application Started")).date()
                except:
                    pass

            if pd.notna(row.get("Submitted Date")):
                try:
                    submit_date = pd.to_datetime(row.get("Submitted Date")).date()
                except:
                    pass

            # Check if applicant_status changed
            cursor.execute(
                "SELECT updated_at FROM applicant_status WHERE user_code = %s",
                (user_code,)
            )
            old_status_updated = cursor.fetchone()

            # Insert into applicant_status table
            status_query = """
            INSERT INTO applicant_status (
                user_code, student_number, app_start, submit_date, 
                status_code, status, detail_status, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
             ON CONFLICT (user_code) DO UPDATE SET
                student_number = EXCLUDED.student_number,
                app_start = EXCLUDED.app_start,
                submit_date = EXCLUDED.submit_date,
                status_code = EXCLUDED.status_code,
                status = EXCLUDED.status,
                detail_status = EXCLUDED.detail_status,
                updated_at = CASE 
                    WHEN applicant_status.student_number IS DISTINCT FROM EXCLUDED.student_number 
                      OR applicant_status.app_start IS DISTINCT FROM EXCLUDED.app_start
                      OR applicant_status.submit_date IS DISTINCT FROM EXCLUDED.submit_date
                      OR applicant_status.status_code IS DISTINCT FROM EXCLUDED.status_code
                      OR applicant_status.status IS DISTINCT FROM EXCLUDED.status 
                      OR applicant_status.detail_status IS DISTINCT FROM EXCLUDED.detail_status 
                    THEN EXCLUDED.updated_at 
                    ELSE applicant_status.updated_at 
                END
            """

            cursor.execute(
                status_query,
                (
                    user_code,
                    row.get("Student Number"),
                    app_start,
                    submit_date,
                    row.get("Status CODE"),
                    row.get("Status"),
                    row.get("Detailed Status"),
                    current_time,  # created_at
                    current_time,  # updated_at
                ),
            )

            # Check if applicant_status actually changed
            cursor.execute(
                "SELECT updated_at FROM applicant_status WHERE user_code = %s",
                (user_code,)
            )
            new_status_updated = cursor.fetchone()
            
            if old_status_updated is None:  # New record
                data_changed = True
            elif old_status_updated and new_status_updated:
                # Check if updated_at changed (meaning data changed)
                if old_status_updated[0] != new_status_updated[0]:
                    data_changed = True

            # Process test scores
            process_toefl_scores(user_code, row, cursor, current_time)
            process_ielts_scores(user_code, row, cursor, current_time)
            process_other_test_scores(user_code, row, cursor, current_time)

            touched_user_codes.add(user_code)

            # Process institution information first
            process_institution_info(user_code, row, cursor, current_time)

            # Process application_info after institutions to calculate fields from institution data
            process_application_info(user_code, row, cursor, current_time)

            # If any data changed in applicant_info but applicant_status wasn't updated, 
            # force update the applicant_status.updated_at
            if data_changed:
                cursor.execute(
                    """
                    UPDATE applicant_status 
                    SET updated_at = %s 
                    WHERE user_code = %s
                    """,
                    (current_time, user_code)
                )

            records_processed += 1

        conn.commit()

        # Recompute English status for all applicants updated in this import
        for uc in touched_user_codes:
            compute_english_status(uc)

        cursor.close()
        conn.close()
        return True, "Data processed successfully", records_processed

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return False, f"Database error: {str(e)}", 0


def get_all_applicant_status():
    """Get all students from applicant_status joined with applicant_info and sessions"""
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT 
                ss.user_code,
                si.family_name,
                si.given_name,
                si.email,
                ss.student_number,
                ss.app_start,
                ss.submit_date,
                ss.status_code,
                ss.status,
                ss.detail_status,
                ss.updated_at,
                EXTRACT(EPOCH FROM (NOW() - ss.updated_at)) as seconds_since_update,
                ROUND(AVG(r.rating), 1) as overall_rating
            FROM applicant_status ss
            LEFT JOIN applicant_info si ON ss.user_code = si.user_code
            LEFT JOIN ratings r ON ss.user_code = r.user_code
            GROUP BY ss.user_code, si.family_name, si.given_name, si.email, 
                     ss.student_number, ss.app_start, ss.submit_date, 
                     ss.status_code, ss.status, ss.detail_status, ss.updated_at
            ORDER BY ss.submit_date DESC, si.family_name
        """
        )
        applicants = cursor.fetchall()
        cursor.close()
        conn.close()

        return applicants, None

    except Exception as e:
        return None, f"Database error: {str(e)}"


def get_all_sessions():
    """Get all sessions from the sessions table"""
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT 
                s.id,
                s.program_code,
                s.program,
                s.session_abbrev,
                s.year,
                s.name,
                s.description,
                s.created_at,
                COUNT(si.user_code) as applicant_count
            FROM sessions s
            LEFT JOIN applicant_info si ON s.id = si.session_id
            GROUP BY s.id, s.program_code, s.program, s.session_abbrev, s.year, s.name, s.description, s.created_at
            ORDER BY s.year DESC, s.program
        """
        )
        sessions = cursor.fetchall()
        cursor.close()
        conn.close()

        return sessions, None

    except Exception as e:
        return None, f"Database error: {str(e)}"


def get_applicant_info_by_code(user_code):
    """Get detailed applicant information by user code"""
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT 
                interest_code, interest, title, family_name, given_name, 
                middle_name, preferred_name, former_family_name, gender_code, 
                gender, country_birth_code, country_birth, date_birth, age,
                country_citizenship_code, country_citizenship, dual_citizenship_code, 
                dual_citizenship, primary_spoken_lang_code, primary_spoken_lang, 
                other_spoken_lang_code, other_spoken_lang, visa_type_code, 
                visa_type, country_code, country, address_line1, address_line2, 
                city, province_state_region, postal_code, primary_telephone, 
                secondary_telephone, email, aboriginal, first_nation, inuit, 
                metis, aboriginal_not_specified, aboriginal_info, 
                academic_history_code, academic_history, ubc_academic_history
            FROM applicant_info 
            WHERE user_code = %s
        """,
            (user_code,),
        )

        applicant_info = cursor.fetchone()
        cursor.close()
        conn.close()

        return applicant_info, None

    except Exception as e:
        if conn:
            conn.close()
        return None, f"Database error: {str(e)}"


def get_applicant_test_scores_by_code(user_code):
    """Get all test scores for a applicant by user code"""
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        test_scores = {}

        # TOEFL scores (multiple entries)
        cursor.execute(
            """
            SELECT * FROM toefl WHERE user_code = %s ORDER BY toefl_number
        """,
            (user_code,),
        )
        test_scores["toefl"] = cursor.fetchall()

        # IELTS scores (multiple entries)
        cursor.execute(
            """
            SELECT * FROM ielts WHERE user_code = %s ORDER BY ielts_number
        """,
            (user_code,),
        )
        test_scores["ielts"] = cursor.fetchall()

        # Other test scores (single entries)
        cursor.execute(
            """
            SELECT * FROM melab WHERE user_code = %s
        """,
            (user_code,),
        )
        test_scores["melab"] = cursor.fetchone()

        cursor.execute(
            """
            SELECT * FROM pte WHERE user_code = %s
        """,
            (user_code,),
        )
        test_scores["pte"] = cursor.fetchone()

        cursor.execute(
            """
            SELECT * FROM cael WHERE user_code = %s
        """,
            (user_code,),
        )
        test_scores["cael"] = cursor.fetchone()

        cursor.execute(
            """
            SELECT * FROM celpip WHERE user_code = %s
        """,
            (user_code,),
        )
        test_scores["celpip"] = cursor.fetchone()

        cursor.execute(
            """
            SELECT * FROM duolingo WHERE user_code = %s
        """,
            (user_code,),
        )
        test_scores["duolingo"] = cursor.fetchone()

        cursor.execute(
            """
            SELECT * FROM alt_elpp WHERE user_code = %s
        """,
            (user_code,),
        )
        test_scores["alt_elpp"] = cursor.fetchone()

        cursor.execute(
            """
            SELECT * FROM gre WHERE user_code = %s
        """,
            (user_code,),
        )
        test_scores["gre"] = cursor.fetchone()

        cursor.execute(
            """
            SELECT * FROM gmat WHERE user_code = %s
        """,
            (user_code,),
        )
        test_scores["gmat"] = cursor.fetchone()

        cursor.close()
        conn.close()

        return test_scores, None

    except Exception as e:
        if conn:
            conn.close()
        return None, f"Database error: {str(e)}"


def get_applicant_institutions_by_code(user_code):
    """Get all institution information for a applicant by user code"""
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT 
                institution_number, institution_code, full_name, country,
                start_date, end_date, program_study, degree_confer_code,
                degree_confer, date_confer, credential_receive_code,
                credential_receive, expected_confer_date, expected_credential_code,
                expected_credential, honours, fail_withdraw, reason, gpa
            FROM institution_info 
            WHERE user_code = %s
            ORDER BY institution_number
        """,
            (user_code,),
        )

        institutions = cursor.fetchall()
        cursor.close()
        conn.close()

        return institutions, None

    except Exception as e:
        if conn:
            conn.close()
        return None, f"Database error: {str(e)}"


def calculate_application_info_fields(user_code, cursor):
    """Calculate highest_degree, degree_area, and gpa based on institution data"""
    try:
        # Define degree hierarchy (higher number = higher degree)
        degree_hierarchy = {
            "phd": 4,
            "doctorate": 4,
            "doctoral": 4,
            "ph.d": 4,
            "ph.d.": 4,
            "master": 3,
            "master's": 3,
            "masters": 3,
            "msc": 3,
            "ma": 3,
            "mba": 3,
            "med": 3,
            "bachelor": 2,
            "bachelor's": 2,
            "bachelors": 2,
            "bsc": 2,
            "ba": 2,
            "beng": 2,
            "associate": 1,
            "diploma": 1,
            "certificate": 1,
        }

        # Get all institutions with degree information for this user
        cursor.execute(
            """
            SELECT institution_number, credential_receive, date_confer, program_study, gpa
            FROM institution_info 
            WHERE user_code = %s 
            AND credential_receive IS NOT NULL 
            AND credential_receive != ''
            ORDER BY institution_number
        """,
            (user_code,),
        )

        institutions = cursor.fetchall()

        if not institutions:
            return None, None, None

        # Find the highest degree with latest date
        highest_degree_level = 0
        selected_institution = None

        for institution in institutions:
            # Handle both tuple and dict results - access by index for tuples
            if isinstance(institution, tuple):
                institution_number = institution[0]
                credential_receive = institution[1]
                date_confer = institution[2]
                program_study = institution[3]
                gpa = institution[4]
            else:
                # Dictionary access (for RealDictCursor)
                institution_number = institution["institution_number"]
                credential_receive = institution["credential_receive"]
                date_confer = institution["date_confer"]
                program_study = institution["program_study"]
                gpa = institution["gpa"]

            if not credential_receive:
                continue

            credential = str(credential_receive).lower().strip()

            # Find matching degree level
            current_degree_level = 0
            for degree_key, level in degree_hierarchy.items():
                if degree_key in credential:
                    current_degree_level = max(current_degree_level, level)

            # If this is a higher degree, or same degree with later date
            if current_degree_level > highest_degree_level:
                highest_degree_level = current_degree_level
                selected_institution = {
                    "credential_receive": credential_receive,
                    "date_confer": date_confer,
                    "program_study": program_study,
                    "gpa": gpa,
                }
            elif current_degree_level == highest_degree_level and selected_institution:
                # Same degree level - choose the one with latest date_confer
                current_date = date_confer
                selected_date = selected_institution["date_confer"]

                if current_date and selected_date:
                    if current_date > selected_date:
                        selected_institution = {
                            "credential_receive": credential_receive,
                            "date_confer": date_confer,
                            "program_study": program_study,
                            "gpa": gpa,
                        }
                elif current_date and not selected_date:
                    selected_institution = {
                        "credential_receive": credential_receive,
                        "date_confer": date_confer,
                        "program_study": program_study,
                        "gpa": gpa,
                    }

        if selected_institution:
            highest_degree = selected_institution["credential_receive"]
            degree_area = selected_institution["program_study"]
            gpa = selected_institution["gpa"]
            return highest_degree, degree_area, gpa

        return None, None, None

    except Exception as e:
        print(
            f"Error calculating application_info fields for user {user_code}: {str(e)}"
        )
        return None, None, None


def process_application_info(user_code, row, cursor, current_time):
    """Process and insert application_info data"""
    try:
        # Determine if applicant is Canadian
        country_citizenship = str(row.get("Country of Current Citizenship", "")).strip()
        dual_citizenship = str(row.get("Dual Citizenship", "")).strip()

        is_canadian = (
            country_citizenship.lower() == "canada"
            or dual_citizenship.lower() == "canada"
        )

        # Create full name
        given_name = str(row.get("Given Name", "")).strip()
        family_name = str(row.get("Family Name", "")).strip()
        full_name = f"{given_name} {family_name}".strip()

        # Calculate highest_degree and degree_area only (no longer using gpa)
        highest_degree, degree_area, _ = calculate_application_info_fields(
            user_code, cursor
        )

        # Insert into application_info table WITHOUT gpa
        application_info_query = """
        INSERT INTO application_info (
            user_code, full_name, canadian, sent, highest_degree, degree_area
        ) VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_code) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            canadian = EXCLUDED.canadian,
            highest_degree = EXCLUDED.highest_degree,
            degree_area = EXCLUDED.degree_area
        """

        cursor.execute(
            application_info_query,
            (
                user_code,
                full_name,
                is_canadian,
                "Not Reviewed",
                highest_degree,
                degree_area,
            ),
        )

    except Exception as e:
        # Log error but don't fail the entire process
        print(f"Error processing application_info for user {user_code}: {str(e)}")


# Replace your existing get_applicant_application_info_by_code function in models/applicants.py:


def get_applicant_application_info_by_code(user_code):
    """Get application_info data for a applicant by user code"""
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT 
                user_code, sent, full_name, canadian, english,
                cs, stat, math, gpa, highest_degree, degree_area,
                mds_v, mds_cl, scholarship,
                english_status, english_description, english_comment
            FROM application_info 
            WHERE user_code = %s
        """,
            (user_code,),
        )

        application_info = cursor.fetchone()
        cursor.close()
        conn.close()

        return application_info, None

    except Exception as e:
        if conn:
            conn.close()
        return None, f"Database error: {str(e)}"


def update_applicant_application_status(user_code, status):
    """Update applicant status in application_info table"""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE application_info 
            SET sent = %s
            WHERE user_code = %s
        """,
            (status, user_code),
        )

        if cursor.rowcount == 0:
            # If no rows updated, create new record
            cursor.execute(
                """
                INSERT INTO application_info (user_code, sent) 
                VALUES (%s, %s)
            """,
                (user_code, status),
            )

        conn.commit()
        cursor.close()
        conn.close()

        return True, "Status updated successfully"

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return False, f"Database error: {str(e)}"


def update_applicant_prerequisites(user_code, cs, stat, math, gpa=None):
    """Update applicant prerequisites (courses and GPA) in application_info table"""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        cursor = conn.cursor()

        # Validate user_code exists in applicant_info first
        cursor.execute(
            "SELECT user_code FROM applicant_info WHERE user_code = %s", (user_code,)
        )
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return False, "Applicant not found"

        cursor.execute(
            """
            UPDATE application_info 
            SET cs = %s, stat = %s, math = %s, gpa = %s
            WHERE user_code = %s
        """,
            (cs, stat, math, gpa, user_code),
        )

        if cursor.rowcount == 0:
            # If no rows updated, create new record
            cursor.execute(
                """
                INSERT INTO application_info (user_code, cs, stat, math, gpa) 
                VALUES (%s, %s, %s, %s, %s)
            """,
                (user_code, cs, stat, math, gpa),
            )

        conn.commit()
        cursor.close()
        conn.close()

        return True, "Prerequisites updated successfully"

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return False, f"Database error: {str(e)}"


# Add these functions at the end of your models/applicants.py file


def update_english_comment(user_code, english_comment):
    """Update English comment for applicant in application_info table"""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        cursor = conn.cursor()

        # Validate user_code exists in applicant_info first
        cursor.execute(
            "SELECT user_code FROM applicant_info WHERE user_code = %s", (user_code,)
        )
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return False, "Applicant not found"

        cursor.execute(
            """
            UPDATE application_info 
            SET english_comment = %s
            WHERE user_code = %s
        """,
            (english_comment, user_code),
        )

        if cursor.rowcount == 0:
            # If no rows updated, create new record
            cursor.execute(
                """
                INSERT INTO application_info (user_code, english_comment) 
                VALUES (%s, %s)
            """,
                (user_code, english_comment),
            )

        conn.commit()
        cursor.close()
        conn.close()

        return True, "English comment updated successfully"

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return False, f"Database error: {str(e)}"


def update_english_status(user_code, english_status):
    """Update English status for applicant in application_info table"""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        cursor = conn.cursor()

        # Validate user_code exists in applicant_info first
        cursor.execute(
            "SELECT user_code FROM applicant_info WHERE user_code = %s", (user_code,)
        )
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return False, "Applicant not found"

        # Update the english_status and set english boolean based on status
        english_boolean = english_status in ["Passed", "Not Required"]

        cursor.execute(
            """
            UPDATE application_info 
            SET english_status = %s, english = %s
            WHERE user_code = %s
        """,
            (english_status, english_boolean, user_code),
        )

        if cursor.rowcount == 0:
            # If no rows updated, create new record
            cursor.execute(
                """
                INSERT INTO application_info (user_code, english_status, english) 
                VALUES (%s, %s, %s)
            """,
                (user_code, english_status, english_boolean),
            )

        conn.commit()
        cursor.close()
        conn.close()

        return True, "English status updated successfully"

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return False, f"Database error: {str(e)}"
