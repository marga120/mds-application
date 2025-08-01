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


def create_or_get_session(cursor, program_code, program, session_abbrev):
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
            SELECT id FROM session 
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
            INSERT INTO session (program_code, program, session_abbrev, year, name, description, created_at, updated_at)
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


def process_csv_data(df):
    """Process CSV data and insert into session, student_info and student_status tables"""
    conn = get_db_connection()
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

            session_result, message = create_or_get_session(
                cursor, program_code, program, session_abbrev
            )
            if session_result is None:
                return False, f"Session creation failed: {message}", 0

            session_id = session_result
        else:
            return False, "CSV file is empty", 0

        for _, row in df.iterrows():
            user_code = str(row.get("User Code", "")).strip()
            if not user_code or user_code == "nan":
                continue

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

            # Insert into student_info table (now with session_id)
            student_info_query = """
            INSERT INTO student_info (
                user_code, session_id, title, family_name, given_name, middle_name, preferred_name,
                former_family_name, gender_code, gender, date_birth, age, country_birth_code,
                country_citizenship_code, country_citizenship, dual_citizenship_code,
                dual_citizenship, primary_spoken_lang_code, primary_spoken_lang,
                other_spoken_lang_code, other_spoken_lang, visa_type_code, visa_type,
                country_code, country, address_line1, address_line2, city,
                province_state_region, postal_code, primary_telephone, secondary_telephone,
                email, aboriginal, first_nation, inuit, metis, aboriginal_not_specified,
                aboriginal_info, academic_history_code, academic_history, interest_code, interest,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s)
            ON CONFLICT (user_code) DO UPDATE SET
                session_id = EXCLUDED.session_id,
                family_name = EXCLUDED.family_name,
                given_name = EXCLUDED.given_name,
                email = EXCLUDED.email,
                updated_at = CASE 
                    WHEN student_info.session_id IS DISTINCT FROM EXCLUDED.session_id
                      OR student_info.family_name IS DISTINCT FROM EXCLUDED.family_name 
                      OR student_info.given_name IS DISTINCT FROM EXCLUDED.given_name 
                      OR student_info.email IS DISTINCT FROM EXCLUDED.email 
                    THEN EXCLUDED.updated_at 
                    ELSE student_info.updated_at 
                END
            """

            cursor.execute(
                student_info_query,
                (
                    user_code,
                    session_id,  # Add session_id here
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
                    row.get("IAcademic History Source Value"),
                    row.get("Source of Interest in UBC CODE"),
                    row.get("Source of Interest in UBC"),
                    current_time,  # created_at
                    current_time,  # updated_at
                ),
            )

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

            # Insert into student_status table
            status_query = """
            INSERT INTO student_status (
                user_code, student_number, app_start, submit_date, 
                status_code, status, detail_status, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
             ON CONFLICT (user_code) DO UPDATE SET
                student_number = EXCLUDED.student_number,
                status = EXCLUDED.status,
                detail_status = EXCLUDED.detail_status,
                updated_at = CASE 
                    WHEN student_status.student_number IS DISTINCT FROM EXCLUDED.student_number 
                      OR student_status.status IS DISTINCT FROM EXCLUDED.status 
                      OR student_status.detail_status IS DISTINCT FROM EXCLUDED.detail_status 
                    THEN EXCLUDED.updated_at 
                    ELSE student_status.updated_at 
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

            # Process test scores
            process_toefl_scores(user_code, row, cursor, current_time)
            process_ielts_scores(user_code, row, cursor, current_time)
            process_other_test_scores(user_code, row, cursor, current_time)

            # Process institution information
            process_institution_info(user_code, row, cursor, current_time)

            # Process app_info processing
            process_app_info(user_code, row, cursor, current_time)

            records_processed += 1

        conn.commit()
        cursor.close()
        conn.close()
        return True, "Data processed successfully", records_processed

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return False, f"Database error: {str(e)}", 0


def get_all_student_status():
    """Get all students from student_status joined with student_info and session"""
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
            FROM student_status ss
            LEFT JOIN student_info si ON ss.user_code = si.user_code
            LEFT JOIN rating r ON ss.user_code = r.user_code
            GROUP BY ss.user_code, si.family_name, si.given_name, si.email, 
                     ss.student_number, ss.app_start, ss.submit_date, 
                     ss.status_code, ss.status, ss.detail_status, ss.updated_at
            ORDER BY ss.submit_date DESC, si.family_name
        """
        )
        students = cursor.fetchall()
        cursor.close()
        conn.close()

        return students, None

    except Exception as e:
        return None, f"Database error: {str(e)}"


def get_all_sessions():
    """Get all sessions from the session table"""
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
                COUNT(si.user_code) as student_count
            FROM session s
            LEFT JOIN student_info si ON s.id = si.session_id
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


def get_student_info_by_code(user_code):
    """Get detailed student information by user code"""
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
            FROM student_info 
            WHERE user_code = %s
        """,
            (user_code,),
        )

        student_info = cursor.fetchone()
        cursor.close()
        conn.close()

        return student_info, None

    except Exception as e:
        if conn:
            conn.close()
        return None, f"Database error: {str(e)}"


def get_student_test_scores_by_code(user_code):
    """Get all test scores for a student by user code"""
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


def get_student_institutions_by_code(user_code):
    """Get all institution information for a student by user code"""
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


def process_app_info(user_code, row, cursor, current_time):
    """Process and insert app_info data"""
    try:
        # Determine if student is Canadian
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

        # Insert into app_info table
        app_info_query = """
        INSERT INTO app_info (
            user_code, full_name, canadian, sent
        ) VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_code) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            canadian = EXCLUDED.canadian
        """

        cursor.execute(
            app_info_query, (user_code, full_name, is_canadian, "Not Reviewed")
        )

    except Exception as e:
        # Log error but don't fail the entire process
        print(f"Error processing app_info for user {user_code}: {str(e)}")


def get_student_app_info_by_code(user_code):
    """Get app_info data for a student by user code"""
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT 
                user_code, status, sent, full_name, canadian, english,
                cs, stat, math, gpa, highest_degree, degree_area,
                mds_v, mds_cl, scholarship
            FROM app_info 
            WHERE user_code = %s
        """,
            (user_code,),
        )

        app_info = cursor.fetchone()
        cursor.close()
        conn.close()

        return app_info, None

    except Exception as e:
        if conn:
            conn.close()
        return None, f"Database error: {str(e)}"


def update_student_app_status(user_code, status):
    """Update student status in app_info table"""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE app_info 
            SET sent = %s
            WHERE user_code = %s
        """,
            (status, user_code),
        )

        if cursor.rowcount == 0:
            # If no rows updated, create new record
            cursor.execute(
                """
                INSERT INTO app_info (user_code, sent) 
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
