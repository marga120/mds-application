"""
CSV Processing Module

This module handles processing of uploaded CSV data and inserting
applicant records into the database.
"""

import pandas as pd
from datetime import datetime, date
from utils.database import get_db_connection
from models.test_scores import (
    process_toefl_scores,
    process_ielts_scores,
    process_other_test_scores,
)
from utils.db_helpers import db_connection
from models.institutions import process_institution_info
from .english_status import compute_english_status


def convert_id_to_string(value):
    """Convert ID numbers to clean strings, removing .0 from floats."""
    if pd.isna(value):
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def calculate_age(birth_date):
    """Calculate age from birth date."""
    if not birth_date:
        return None

    today = date.today()
    age = today.year - birth_date.year

    if today.month < birth_date.month or (
        today.month == birth_date.month and today.day < birth_date.day
    ):
        age -= 1

    return age


def create_or_get_sessions(cursor, program_code, program, session_abbrev, campus='UBC-V'):
    """Create or retrieve session information based on CSV data."""
    try:
        program_code = program_code[:10]
        program = program[:50]
        session_abbrev = session_abbrev[:10]

        if campus not in ['UBC-V', 'UBC-O']:
            campus = 'UBC-V'

        if len(session_abbrev) < 4:
            return None, f"Session abbreviation '{session_abbrev}' is too short"

        year_str = session_abbrev[:4]
        if not year_str.isdigit():
            return None, f"First 4 characters of session '{session_abbrev}' are not numeric"

        year = int(year_str)

        campus_short = campus.split('-')[1] if '-' in campus else 'V'
        name = f"{program_code}-{campus_short} {session_abbrev}"[:30]

        cursor.execute(
            """
            SELECT id FROM sessions
            WHERE program_code = %s AND year = %s AND session_abbrev = %s AND campus = %s
            """,
            (program_code, year, session_abbrev, campus),
        )

        existing_session = cursor.fetchone()
        if existing_session:
            return existing_session[0], f"Found existing session: {name}"

        cursor.execute(
            """
            INSERT INTO sessions (program_code, program, session_abbrev, year, name, description, campus, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (program_code, program, session_abbrev, year, name, "", campus, datetime.now(), datetime.now()),
        )

        session_id = cursor.fetchone()[0]
        return session_id, f"Created new session: {name} (ID: {session_id})"

    except ValueError as e:
        return None, f"Error parsing year from session_abbrev '{session_abbrev}': {e}"
    except Exception as e:
        return None, f"Database error creating session: {e}"


def calculate_application_info_fields(user_code, cursor):
    """Calculate highest_degree, degree_area, and gpa based on institution data."""
    try:
        degree_hierarchy = {
            "phd": 4, "doctorate": 4, "doctoral": 4, "ph.d": 4, "ph.d.": 4,
            "master": 3, "master's": 3, "masters": 3, "msc": 3, "ma": 3, "mba": 3, "med": 3,
            "bachelor": 2, "bachelor's": 2, "bachelors": 2, "bsc": 2, "ba": 2, "beng": 2,
            "associate": 1, "diploma": 1, "certificate": 1,
        }

        cursor.execute(
            """
            SELECT institution_number, credential_receive, date_confer, program_study, gpa
            FROM institution_info
            WHERE user_code = %s AND credential_receive IS NOT NULL AND credential_receive != ''
            ORDER BY institution_number
            """,
            (user_code,),
        )

        institutions = cursor.fetchall()
        if not institutions:
            return None, None, None

        highest_degree_level = 0
        selected_institution = None

        for institution in institutions:
            if isinstance(institution, tuple):
                credential_receive = institution[1]
                date_confer = institution[2]
                program_study = institution[3]
                gpa = institution[4]
            else:
                credential_receive = institution["credential_receive"]
                date_confer = institution["date_confer"]
                program_study = institution["program_study"]
                gpa = institution["gpa"]

            if not credential_receive:
                continue

            credential = str(credential_receive).lower().strip()
            current_degree_level = 0
            for degree_key, level in degree_hierarchy.items():
                if degree_key in credential:
                    current_degree_level = max(current_degree_level, level)

            if current_degree_level > highest_degree_level:
                highest_degree_level = current_degree_level
                selected_institution = {
                    "credential_receive": credential_receive,
                    "date_confer": date_confer,
                    "program_study": program_study,
                    "gpa": gpa,
                }
            elif current_degree_level == highest_degree_level and selected_institution:
                current_date = date_confer
                selected_date = selected_institution["date_confer"]
                if current_date and selected_date and current_date > selected_date:
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
            return (selected_institution["credential_receive"],
                    selected_institution["program_study"],
                    selected_institution["gpa"])

        return None, None, None

    except Exception as e:
        print(f"Error calculating application_info fields for user {user_code}: {str(e)}")
        return None, None, None


def process_application_info(user_code, row, cursor, current_time):
    """Process and insert application_info data."""
    try:
        country_citizenship = str(row.get("Country of Current Citizenship", "")).strip()
        dual_citizenship = str(row.get("Dual Citizenship", "")).strip()

        is_canadian = (
            country_citizenship.lower() == "canada"
            or dual_citizenship.lower() == "canada"
        )

        given_name = str(row.get("Given Name", "")).strip()
        family_name = str(row.get("Family Name", "")).strip()
        full_name = f"{given_name} {family_name}".strip()

        highest_degree, degree_area, _ = calculate_application_info_fields(user_code, cursor)

        application_info_query = """
        INSERT INTO application_info (
            user_code, full_name, canadian, sent, highest_degree, degree_area,
            mds_v, mds_cl, mds_o
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_code) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            canadian = EXCLUDED.canadian,
            highest_degree = EXCLUDED.highest_degree,
            degree_area = EXCLUDED.degree_area,
            mds_v = EXCLUDED.mds_v,
            mds_cl = EXCLUDED.mds_cl,
            mds_o = EXCLUDED.mds_o
        """

        cursor.execute(
            application_info_query,
            (user_code, full_name, is_canadian, "Not Reviewed", highest_degree, degree_area,
             "No", "No", "Yes"),
        )

    except Exception as e:
        print(f"Error processing application_info for user {user_code}: {str(e)}")


def process_csv_data(df):
    """
    Process uploaded CSV data and insert into database tables.

    @param df: Pandas DataFrame containing CSV data
    @return: Tuple of (success, message, records_processed)
    """
    conn = get_db_connection()
    touched_user_codes = set()

    if not conn:
        return False, "Database connection failed", 0

    try:
        cursor = conn.cursor()
        records_processed = 0
        session_id = None

        if not df.empty:
            first_row = df.iloc[0]
            program_code = str(first_row.get("Program CODE", "")).strip()
            program = str(first_row.get("Program", "")).strip()
            session_abbrev = str(first_row.get("Session", "")).strip()

            campus = str(first_row.get("Campus", first_row.get("campus", ""))).strip()

            if campus and campus.upper() in ['UBC-O', 'UBCO', 'O', 'OKANAGAN']:
                campus = 'UBC-O'
            elif campus and campus.upper() in ['UBC-V', 'UBCV', 'V', 'VANCOUVER']:
                campus = 'UBC-V'
            else:
                if program_code.upper().startswith('OG'):
                    campus = 'UBC-O'
                elif program_code.upper().startswith('VG'):
                    campus = 'UBC-V'
                else:
                    campus = 'UBC-V'

            if not program_code or program_code == "nan":
                return False, f"Invalid Program CODE", 0
            if not program or program == "nan":
                return False, f"Invalid Program", 0
            if not session_abbrev or session_abbrev == "nan":
                return False, f"Invalid Session", 0

            sessions_result, message = create_or_get_sessions(cursor, program_code, program, session_abbrev, campus)
            if sessions_result is None:
                return False, f"Session creation failed: {message}", 0

            session_id = sessions_result
        else:
            return False, "CSV file is empty", 0

        for _, row in df.iterrows():
            user_code = str(row.get("User Code", "")).strip()
            if not user_code or user_code == "nan":
                continue

            data_changed = False

            date_birth = None
            if pd.notna(row.get("Date of Birth")):
                try:
                    date_birth = pd.to_datetime(row.get("Date of Birth")).date()
                except:
                    pass

            age = calculate_age(date_birth)
            current_time = datetime.now()

            ubc_academic_history = row.get(
                "{ UBC Academic History List - eVision Record #; Start Date; End Date; Category; Program of Study; Degree Conferred?; Date Conferred; Credential Received; Withdrawal Reasons; Honours }",
                "",
            )

            if pd.isna(ubc_academic_history) or str(ubc_academic_history).strip() == "nan":
                ubc_academic_history = ""
            else:
                ubc_academic_history = str(ubc_academic_history).strip()

            racialized_value = row.get("Racialized")
            if pd.isna(racialized_value):
                racialized_value = None
            else:
                racialized_value = str(racialized_value).strip()

            cursor.execute("SELECT updated_at FROM applicant_info WHERE user_code = %s", (user_code,))
            old_info_updated = cursor.fetchone()

            # Insert applicant_info
            _insert_applicant_info(cursor, user_code, session_id, row, date_birth, age,
                                   ubc_academic_history, racialized_value, current_time)

            cursor.execute("SELECT updated_at FROM applicant_info WHERE user_code = %s", (user_code,))
            new_info_updated = cursor.fetchone()

            if old_info_updated is None or (old_info_updated and new_info_updated and old_info_updated[0] != new_info_updated[0]):
                data_changed = True

            # Parse dates for applicant_status
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

            cursor.execute("SELECT updated_at FROM applicant_status WHERE user_code = %s", (user_code,))
            old_status_updated = cursor.fetchone()

            _insert_applicant_status(cursor, user_code, row, app_start, submit_date, current_time)

            cursor.execute("SELECT updated_at FROM applicant_status WHERE user_code = %s", (user_code,))
            new_status_updated = cursor.fetchone()

            if old_status_updated is None or (old_status_updated and new_status_updated and old_status_updated[0] != new_status_updated[0]):
                data_changed = True

            # Process test scores
            toefl_changed = process_toefl_scores(user_code, row, cursor, current_time)
            ielts_changed = process_ielts_scores(user_code, row, cursor, current_time)
            other_tests_changed = process_other_test_scores(user_code, row, cursor, current_time)

            touched_user_codes.add(user_code)

            # Process institution information
            institution_changed = process_institution_info(user_code, row, cursor, current_time)

            # Process application_info
            process_application_info(user_code, row, cursor, current_time)

            if data_changed or institution_changed or toefl_changed or ielts_changed or other_tests_changed:
                cursor.execute(
                    "UPDATE applicant_status SET updated_at = %s WHERE user_code = %s",
                    (current_time, user_code)
                )

            records_processed += 1

        conn.commit()

        # Recompute English status for all updated applicants
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


def _insert_applicant_info(cursor, user_code, session_id, row, date_birth, age,
                           ubc_academic_history, racialized_value, current_time):
    """Insert or update applicant_info record."""
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
              OR applicant_info.family_name IS DISTINCT FROM EXCLUDED.family_name
              OR applicant_info.given_name IS DISTINCT FROM EXCLUDED.given_name
              OR applicant_info.email IS DISTINCT FROM EXCLUDED.email
            THEN EXCLUDED.updated_at
            ELSE applicant_info.updated_at
        END
    """

    cursor.execute(
        applicant_info_query,
        (
            user_code,
            session_id,
            row.get("Title"),
            row.get("Family Name"),
            row.get("Given Name"),
            row.get("Middle Name"),
            row.get("Preferred Name"),
            row.get("Former Family Name"),
            row.get("Gender CODE"),
            row.get("Gender"),
            date_birth,
            age,
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
            convert_id_to_string(row.get("Primary Telephone")),
            convert_id_to_string(row.get("Secondary Telephone")),
            row.get("Email"),
            row.get("Aboriginal"),
            row.get("Aboriginal Type First Nations"),
            row.get("Aboriginal Type Inuit"),
            row.get("Aboriginal Type Metis"),
            row.get("Aboriginal Type Not Specified"),
            row.get("Aboriginal Info"),
            racialized_value,
            row.get("Academic History Source CODE"),
            row.get("IAcademic History Source Value"),
            ubc_academic_history,
            row.get("Source of Interest in UBC CODE"),
            row.get("Source of Interest in UBC"),
            current_time,
            current_time,
        ),
    )


def _insert_applicant_status(cursor, user_code, row, app_start, submit_date, current_time):
    """Insert or update applicant_status record."""
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
              OR applicant_status.status IS DISTINCT FROM EXCLUDED.status
            THEN EXCLUDED.updated_at
            ELSE applicant_status.updated_at
        END
    """

    cursor.execute(
        status_query,
        (
            user_code,
            convert_id_to_string(row.get("Student Number")),
            app_start,
            submit_date,
            row.get("Status CODE"),
            row.get("Status"),
            row.get("Detailed Status"),
            current_time,
            current_time,
        ),
    )
