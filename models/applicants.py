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
    """
    Calculate age from birth date.

    Calculates a person's current age based on their birth date, accounting
    for whether their birthday has occurred this year.

    @param birth_date: The person's birth date
    @param_type birth_date: datetime.date or None

    @return: Current age in years, or None if birth_date is None
    @return_type: int or None

    @example:
        birth_date = date(1995, 5, 15)
        age = calculate_age(birth_date)  # Returns current age
    """

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
    """
    Create or retrieve session information based on CSV data.

    Creates a new academic session record or retrieves an existing one
    based on program code, program name, and session abbreviation.
    Extracts year information from session abbreviation.

    @param cursor: Database cursor for executing queries
    @param_type cursor: psycopg2.cursor
    @param program_code: Program code identifier (max 10 chars)
    @param_type program_code: str
    @param program: Program name (max 20 chars)
    @param_type program: str
    @param session_abbrev: Session abbreviation with year prefix (max 6 chars)
    @param_type session_abbrev: str

    @return: Tuple of (session_id, message)
    @return_type: tuple[int, str] or tuple[None, str]

    @validation:
        - Session abbreviation must be at least 4 characters
        - First 4 characters must be numeric (year)
        - Input strings truncated to database column limits

    @db_tables: sessions

    @example:
        session_id, message = create_or_get_sessions(cursor, "MDS", "Master of Data Science", "2025W")
        # Returns (1, "Session created successfully") or existing session ID
    """

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
    """
    Process uploaded CSV data and insert into database tables.

    Main function for processing applicant CSV files. Handles session creation,
    applicant information processing, test scores, institution data, and
    application metadata. Tracks all processed user codes for updates.

    @param df: Pandas DataFrame containing CSV data
    @param_type df: pandas.DataFrame

    @return: Tuple of (success, message, records_processed)
    @return_type: tuple[bool, str, int]

    @validation:
        - Validates required columns exist
        - Checks for valid program and session data
        - Processes each row with error handling

    @db_tables: sessions, applicant_info, applicant_status, application_info,
               toefl, ielts, gre, gmat, institution_info, and other test tables
    @transaction: Uses database transaction with rollback on error

    @example:
        success, message, count = process_csv_data(df)
        if success:
            print(f"Processed {count} records successfully")
    """

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
            
            # Handle racialized field - convert NaN to None, keep Y/N values
            racialized_value = row.get("Racialized")
            
            if pd.isna(racialized_value):
                racialized_value = None
            else:
                racialized_value = str(racialized_value).strip()

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
                aboriginal_info, racialized, academic_history_code, academic_history, ubc_academic_history, interest_code, interest,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s)
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
                racialized = EXCLUDED.racialized,
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
                      OR applicant_info.racialized IS DISTINCT FROM EXCLUDED.racialized
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
                    row.get("Aboriginal Type Not Specified"),  # aboriginal_not_specified
                    row.get("Aboriginal Info"),
                    racialized_value,
                    row.get("Academic History Source CODE"),
                    row.get("IAcademic History Source Value"),
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
            toefl_changed = process_toefl_scores(user_code, row, cursor, current_time)
            ielts_changed = process_ielts_scores(user_code, row, cursor, current_time)
            other_tests_changed = process_other_test_scores(user_code, row, cursor, current_time)

            touched_user_codes.add(user_code)

            # Process institution information first
            institution_changed = process_institution_info(user_code, row, cursor, current_time)

            # Process application_info after institutions to calculate fields from institution data
            process_application_info(user_code, row, cursor, current_time)

            # If any data changed in any table, force update the applicant_status.updated_at
            if (data_changed or institution_changed or toefl_changed or ielts_changed or other_tests_changed):
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
    """
    Get all applicants with their status and basic information.

    Retrieves a comprehensive list of all applicants including their current
    status, contact information, submission dates, and overall ratings.
    Used for the main applicants dashboard display.

    @return: Tuple of (applicants_list, error_message)
    @return_type: tuple[list, None] or tuple[None, str]

    @db_tables: applicant_status, applicant_info, ratings
    @joins: LEFT JOIN to include applicants without ratings
    @aggregation: Calculates average rating across all reviewers

    @example:
        applicants, error = get_all_applicant_status()
        if not error:
            for applicant in applicants:
                print(f"{applicant['given_name']} {applicant['family_name']}: {applicant['status']}")
    """

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
    """
    Get all academic sessions with applicant counts.

    Retrieves all session records from the database along with the count
    of applicants associated with each session for administrative overview.

    @return: Tuple of (sessions_list, error_message)
    @return_type: tuple[list, None] or tuple[None, str]

    @db_tables: sessions, applicant_info
    @joins: LEFT JOIN to count applicants per session
    @ordering: Ordered by year (descending) and program name

    @example:
        sessions, error = get_all_sessions()
        if not error:
            for session in sessions:
                print(f"{session['name']}: {session['applicant_count']} applicants")
    """

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
    """
    Get detailed applicant information by user code.

    Retrieves comprehensive personal and demographic information for a
    specific applicant, including contact details, citizenship, and
    session information.

    @param user_code: Unique identifier for the applicant
    @param_type user_code: str

    @return: Tuple of (applicant_info_dict, error_message)
    @return_type: tuple[dict, None] or tuple[None, str]

    @db_tables: applicant_info, sessions
    @joins: JOIN with sessions for session name

    @example:
        info, error = get_applicant_info_by_code("12345")
        if not error:
            print(f"Name: {info['given_name']} {info['family_name']}")
            print(f"Email: {info['email']}")
    """

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
                metis, aboriginal_not_specified, aboriginal_info, racialized,
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
    """
    Get all standardized test scores for an applicant.

    Retrieves all test scores from multiple test types including TOEFL,
    IELTS, GRE, GMAT, Duolingo, and other English proficiency tests.

    @param user_code: Unique identifier for the applicant
    @param_type user_code: str

    @return: Tuple of (test_scores_dict, error_message)
    @return_type: tuple[dict, None] or tuple[None, str]

    @db_tables: toefl, ielts, melab, pte, cael, celpip, duolingo, alt_elpp, gre, gmat
    @structure: Returns dictionary with test type as keys, score records as values

    @example:
        scores, error = get_applicant_test_scores_by_code("12345")
        if not error:
            if scores['toefl']:
                print(f"TOEFL Total: {scores['toefl']['total']}")
            if scores['gre']:
                print(f"GRE Verbal: {scores['gre']['verbal']}")
    """

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
    """
    Get all institutional/academic history for an applicant.

    Retrieves educational background information including all institutions
    attended, degrees earned, GPAs, and academic credentials.

    @param user_code: Unique identifier for the applicant
    @param_type user_code: str

    @return: Tuple of (institutions_list, error_message)
    @return_type: tuple[list, None] or tuple[None, str]

    @db_tables: institution_info
    @ordering: Ordered by institution_number for consistent display

    @example:
        institutions, error = get_applicant_institutions_by_code("12345")
        if not error:
            for inst in institutions:
                print(f"{inst['full_name']} - {inst['degree_confer']} in {inst['program_study']}")
    """

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


def get_applicant_application_info_by_code(user_code):
    """
    Get application-specific information and metadata.

    Retrieves application status, English proficiency information,
    prerequisite course data, GPA, and other application-specific metadata.

    @param user_code: Unique identifier for the applicant
    @param_type user_code: str

    @return: Tuple of (application_info_dict, error_message)
    @return_type: tuple[dict, None] or tuple[None, str]

    @db_tables: application_info

    @example:
        app_info, error = get_applicant_application_info_by_code("12345")
        if not error:
            print(f"Status: {app_info['sent']}")
            print(f"English Status: {app_info['english_status']}")
            print(f"GPA: {app_info['gpa']}")
    """

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
    """
    Update the application status for an applicant.

    Changes the application review status in the application_info table.
    Creates a new record if none exists for the applicant.

    @param user_code: Unique identifier for the applicant
    @param_type user_code: str
    @param status: New application status
    @param_type status: str

    @return: Tuple of (success, message)
    @return_type: tuple[bool, str]

    @valid_statuses: ["Not Reviewed", "Reviewed", "Waitlist", "Declined", "Offer", "CoGS", "Offer Sent"]
    @db_tables: application_info
    @upsert: Updates existing record or creates new one

    @example:
        success, message = update_applicant_application_status("12345", "Reviewed")
        if success:
            print("Status updated successfully")
    """

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
    """
    Update prerequisite course and GPA information for an applicant.

    Updates computer science, statistics, and mathematics prerequisite
    course information along with GPA data in the application_info table.

    @param user_code: Unique identifier for the applicant
    @param_type user_code: str
    @param cs: Computer Science courses completed
    @param_type cs: str
    @param stat: Statistics courses completed
    @param_type stat: str
    @param math: Mathematics courses completed
    @param_type math: str
    @param gpa: Overall GPA (optional)
    @param_type gpa: str or None

    @return: Tuple of (success, message)
    @return_type: tuple[bool, str]

    @validation: Validates that user_code exists in applicant_info
    @db_tables: application_info, applicant_info
    @upsert: Updates existing record or creates new one

    @example:
        success, msg = update_applicant_prerequisites(
            "12345",
            "CPSC 110, CPSC 210",
            "STAT 251",
            "MATH 100, MATH 101",
            "3.85"
        )
    """

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


def update_english_comment(user_code, english_comment):
    """
    Update English proficiency comments for an applicant.

    Updates the English language assessment comments in the application_info
    table. Used by Admin users for documenting English proficiency evaluations.

    @param user_code: Unique identifier for the applicant
    @param_type user_code: str
    @param english_comment: English proficiency assessment comment
    @param_type english_comment: str

    @return: Tuple of (success, message)
    @return_type: tuple[bool, str]

    @validation: Validates that user_code exists in applicant_info
    @db_tables: application_info, applicant_info
    @upsert: Updates existing record or creates new one

    @example:
        success, msg = update_english_comment("12345", "Strong English proficiency demonstrated")
    """

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
    """
    Update English proficiency status for an applicant.

    Updates the English language requirement status in the application_info
    table. Used to track whether English requirements are met.

    @param user_code: Unique identifier for the applicant
    @param_type user_code: str
    @param english_status: English proficiency status
    @param_type english_status: str

    @return: Tuple of (success, message)
    @return_type: tuple[bool, str]

    @valid_statuses: ["Not Met", "Not Required", "Passed"]
    @validation: Validates that user_code exists in applicant_info
    @db_tables: application_info, applicant_info
    @upsert: Updates existing record or creates new one

    @example:
        success, msg = update_english_status("12345", "Passed")
    """

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
    
    ###CHANGED
def get_single_applicant_for_export(user_code, include_sections=None):
    """
    Fetch comprehensive data for a single applicant, structured by section.
    Retrieves all application-related data for a specific applicant. The data
    is compiled from multiple tables and returned as a dictionary nested by
    section. Optionally, the 'include_sections' parameter can be used to
    limit the returned data to specific sections (e.g., 'personal', 'ratings').

    @param user_code: Unique identifier for the applicant
    @param_type user_code: str
    @param include_sections: An iterable (e.g., list or set) of section names
                             to include. If None, all sections are included.
    @param_type include_sections: iterable[str] or None
    @return: A tuple containing the applicant's data dictionary and an error
             message. On success, (result_dict, None). On failure,
             (None, error_message).
    @return_type: tuple[dict | None, str | None]
    @validation: Validates that user_code exists in applicant_info.
    @db_tables: applicant_info, applicant_status, application_info,
                test_scores, institutions, ratings, "user"
    @example:
        # Fetch all data for one applicant
        data, error = get_single_applicant_for_export("12345")
        if not error:
            print(data['basic']['given_name'])

        # Fetch only basic info and ratings
        data, error = get_single_applicant_for_export(
            "67890",
            include_sections=['basic', 'ratings']
        )
    """
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"

    try:
        result = {}
        
        # basic applicant info
        applicant_info, error = get_applicant_info_by_code(user_code)
        if error or not applicant_info:
            return None, error or "Applicant not found"
        
        result['basic'] = {
            'user_code': user_code,
            'given_name': applicant_info.get('given_name'),
            'family_name': applicant_info.get('family_name'),
            'email': applicant_info.get('email')
        }
        
        # Personal Information
        if not include_sections or 'personal' in include_sections:
            # Get status info separately
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT student_number, app_start, submit_date, status, detail_status
                FROM applicant_status
                WHERE user_code = %s
            """, (user_code,))
            status_info = cursor.fetchone()
            cursor.close()
            
            # Combine applicant_info with status_info
            result['personal'] = {**applicant_info, **(status_info or {})}
        
        # Application Information - use existing getter
        if not include_sections or 'application' in include_sections:
            app_info, _ = get_applicant_application_info_by_code(user_code)
            result['application'] = app_info
        
        # Prerequisites - already part of application_info
        if not include_sections or 'prerequisites' in include_sections:
            if 'application' not in result:
                app_info, _ = get_applicant_application_info_by_code(user_code)
            else:
                app_info = result['application']
            
            result['prerequisites'] = {
                'cs': app_info.get('cs') if app_info else None,
                'stat': app_info.get('stat') if app_info else None,
                'math': app_info.get('math') if app_info else None,
                'gpa': app_info.get('gpa') if app_info else None
            }
        
        # Test Scores - use existing getter
        if not include_sections or 'test_scores' in include_sections:
            test_scores, _ = get_applicant_test_scores_by_code(user_code)
            result['test_scores'] = test_scores or {}
        
        # Institutions - use existing getter
        if not include_sections or 'institutions' in include_sections:
            institutions, _ = get_applicant_institutions_by_code(user_code)
            result['institutions'] = institutions or []
        
        # Ratings and Comments - only unique query needed
        if not include_sections or 'ratings' in include_sections:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    r.rating, r.user_comment, r.created_at, r.updated_at,
                    u.first_name, u.last_name, u.email as reviewer_email
                FROM ratings r
                JOIN "user" u ON r.user_id = u.id
                WHERE r.user_code = %s
                ORDER BY r.created_at DESC
            """, (user_code,))
            result['ratings'] = cursor.fetchall()
            cursor.close()
        
        conn.close()
        return result, None

    except Exception as e:
        if conn:
            conn.close()
        print(f"Error in get_single_applicant_for_export: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, f"Database error: {str(e)}"


def get_selected_applicants_for_export(user_codes, sections=None):
    """
    Fetch aggregated data for a selected list of applicants.
    Please note, this structure for the code is formatted as to keep performance.
    If I were to reuse the get_single_applicant for export, and loop over that to
    grab each selected applicants data, this would cause huge performance issues, the current
    structure only executes 1 query in order to keep this to a minimum.

    @param_type user_codes: list[str] or tuple[str]
    @param sections: An iterable (e.g., list or set) of section names to
                     include (e.g., 'personal', 'application', 'ratings').
                     If None, all sections are included.
    @param_type sections: iterable[str] or None
    @return: A tuple containing a list of applicant data dictionaries and
             an error message. On success, (list_of_dicts, None).
             On failure, (None, error_message).
    @return_type: tuple[list[dict] | None, str | None]
    @validation: The user_codes parameter must be a non-empty list or tuple.
    @db_tables: applicant_info, applicant_status, application_info,
                sessions, ratings, "user"
    @example:
        user_list = ["12345", "67890"]
        section_list = ['personal', 'ratings']
        
        data, error = get_selected_applicants_for_export(user_list, section_list)
        
        if not error:
            for applicant in data:
                print(applicant['family_name'], applicant['avg_rating'])
    """
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Determine which fields to include based on sections
        all_sections = sections is None
        include_personal = all_sections or 'personal' in sections
        include_application = all_sections or 'application' in sections
        include_prerequisites = all_sections or 'prerequisites' in sections
        include_ratings = all_sections or 'ratings' in sections
        
        # Build dynamic SELECT based on sections
        select_fields = ["ai.user_code", "ai.given_name", "ai.family_name"]
        
        if include_personal:
            select_fields.extend([
                "ai.email", "ast.student_number", "ai.date_birth", "ai.gender",
                "ai.country", "ai.country_citizenship", "ai.primary_spoken_lang"
            ])
        
        if include_application:
            select_fields.extend([
                "COALESCE(app.sent, 'Not Reviewed') as current_status",
                "ast.submit_date", "ast.updated_at as uploaded_at",
                "app.english_status as english_proficiency_status",
                "app.english_comment"
            ])
        
        if include_prerequisites:
            select_fields.extend(["app.cs", "app.stat", "app.math", "app.gpa"])
        
        if include_ratings:
            select_fields.extend([
                "COALESCE(AVG(r.rating), 0) as avg_rating",
                "COUNT(r.user_id) as rating_count",
                "STRING_AGG(CASE WHEN r.user_comment IS NOT NULL AND r.user_comment != '' " +
                "THEN u.first_name || ' ' || u.last_name || ': ' || r.user_comment END, ' | ') as all_comments"
            ])
        
        # Add session info
        select_fields.extend(["s.program_code", "s.year as program_year", "app.canadian"])
        
        placeholders = ','.join(['%s'] * len(user_codes))
        query = f"""
            SELECT {', '.join(select_fields)}
            FROM applicant_info ai
            LEFT JOIN applicant_status ast ON ai.user_code = ast.user_code
            LEFT JOIN application_info app ON ai.user_code = app.user_code
            LEFT JOIN sessions s ON ai.session_id = s.id
        """
        
        if include_ratings:
            query += """
            LEFT JOIN ratings r ON ai.user_code = r.user_code
            LEFT JOIN "user" u ON r.user_id = u.id
            """
        
        query += f"""
            WHERE ai.user_code IN ({placeholders})
            GROUP BY 
                ai.user_code, ai.given_name, ai.family_name
        """
        
        # Add GROUP BY fields based on what's selected
        if include_personal:
            query += ", ai.email, ast.student_number, ai.date_birth, ai.gender, ai.country, ai.country_citizenship, ai.primary_spoken_lang"
        if include_application:
            query += ", app.sent, ast.submit_date, ast.updated_at, app.english_status, app.english_comment"
        if include_prerequisites:
            query += ", app.cs, app.stat, app.math, app.gpa"
        
        query += ", s.program_code, s.year, app.canadian ORDER BY ai.family_name, ai.given_name"
        
        cursor.execute(query, user_codes)
        applicants = cursor.fetchall()
        cursor.close()
        conn.close()

        return applicants, None

    except Exception as e:
        if conn:
            conn.close()
        print(f"Error in get_selected_applicants_for_export: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, f"Database error: {str(e)}"


def get_all_applicants_for_export(status_filter=None):
    """
    Fetch comprehensive, aggregated data for all applicants.


    @param status_filter: Optional status string to filter applicants
                          (e.g., 'Passed', 'Failed', 'Not Reviewed').
                          If None, all applicants are returned.
    @param_type status_filter: str or None
    @return: A tuple containing a list of all applicant data dictionaries
             and an error message. On success, (list_of_dicts, None).
             On failure, (None, error_message).
    @return_type: tuple[list[dict] | None, str | None]
    @db_tables: applicant_info, applicant_status, application_info,
                ratings, "user", sessions
    @example:
        # Get all applicants
        all_data, error = get_all_applicants_for_export()

        # Get only applicants with 'Passed' status
        passed_data, error = get_all_applicants_for_export(
            status_filter="Passed"
        )
        
        if not error:
            print(f"Total applicants found: {len(all_data)}")
    """
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                ai.user_code,
                ai.given_name,
                ai.family_name,
                ai.email,
                ast.student_number,
                ai.date_birth,
                ai.gender,
                ai.country,
                ai.country_citizenship,
                ai.primary_spoken_lang,
                COALESCE(app.sent, 'Not Reviewed') as current_status,
                ast.submit_date,
                ast.updated_at as uploaded_at,
                app.english_status as english_proficiency_status,
                app.english_comment,
                app.cs,
                app.stat,
                app.math,
                app.gpa,
                app.canadian,
                COALESCE(AVG(r.rating), 0) as avg_rating,
                COUNT(r.user_id) as rating_count,
                STRING_AGG(
                    CASE 
                        WHEN r.user_comment IS NOT NULL AND r.user_comment != '' 
                        THEN u.first_name || ' ' || u.last_name || ': ' || r.user_comment 
                    END, 
                    ' | '
                ) as all_comments,
                s.program_code,
                s.year as program_year
            FROM applicant_info ai
            LEFT JOIN applicant_status ast ON ai.user_code = ast.user_code
            LEFT JOIN application_info app ON ai.user_code = app.user_code
            LEFT JOIN ratings r ON ai.user_code = r.user_code
            LEFT JOIN "user" u ON r.user_id = u.id
            LEFT JOIN sessions s ON ai.session_id = s.id
        """
        
        params = []
        if status_filter:
            query += " WHERE app.sent = %s"
            params.append(status_filter)
        
        query += """
            GROUP BY 
                ai.user_code, ai.given_name, ai.family_name, ai.email,
                ast.student_number, ai.date_birth, ai.gender, ai.country,
                ai.country_citizenship, ai.primary_spoken_lang,
                app.sent, ast.submit_date, ast.updated_at,
                app.english_status, app.english_comment,
                app.cs, app.stat, app.math, app.gpa, app.canadian,
                s.program_code, s.year
            ORDER BY ai.family_name, ai.given_name
        """
        
        cursor.execute(query, params) if params else cursor.execute(query)
        
        applicants = cursor.fetchall()
        cursor.close()
        conn.close()

        return applicants, None

    except Exception as e:
        if conn:
            conn.close()
        print(f"Error in get_all_applicants_for_export: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, f"Database error: {str(e)}"