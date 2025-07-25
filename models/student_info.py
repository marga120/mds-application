from utils.database import get_db_connection
from psycopg2.extras import RealDictCursor
import pandas as pd
from datetime import datetime


def create_or_get_session(cursor, program_code, program, session_abbrev):
    """Create or get session based on CSV data"""
    try:
        # Truncate values to fit database column limits
        program_code = program_code[:10]  # program_code VARCHAR(10)
        program = program[:20]            # program VARCHAR(20)
        session_abbrev = session_abbrev[:6]  # session_abbrev VARCHAR(6)
        
        # Extract year from session_abbrev (first 4 characters)
        if len(session_abbrev) < 4:
            return None, f"Session abbreviation '{session_abbrev}' is too short (need at least 4 characters)"
            
        year_str = session_abbrev[:4]
        
        if not year_str.isdigit():
            return None, f"First 4 characters of session '{session_abbrev}' are not numeric: '{year_str}'"
        
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
            (program_code, year, session_abbrev)
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
                datetime.now()
            )
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
                return False, f"Invalid Program CODE: '{first_row.get('Program CODE', 'NOT_FOUND')}'", 0
            if not program or program == "nan" or program == "":
                return False, f"Invalid Program: '{first_row.get('Program', 'NOT_FOUND')}'", 0
            if not session_abbrev or session_abbrev == "nan" or session_abbrev == "":
                return False, f"Invalid Session: '{first_row.get('Session', 'NOT_FOUND')}'", 0
            
            session_result, message = create_or_get_session(cursor, program_code, program, session_abbrev)
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

            # Get current timestamp
            current_time = datetime.now()

            # Insert into student_info table (now with session_id)
            student_info_query = """
            INSERT INTO student_info (
                user_code, session_id, title, family_name, given_name, middle_name, preferred_name,
                former_family_name, gender_code, gender, date_birth, country_birth_code,
                country_citizenship_code, country_citizenship, dual_citizenship_code,
                dual_citizenship, primary_spoken_lang_code, primary_spoken_lang,
                other_spoken_lang_code, other_spoken_lang, visa_type_code, visa_type,
                country_code, country, address_line1, address_line2, city,
                province_state_region, postal_code, primary_telephone, secondary_telephone,
                email, aboriginal, first_nation, inuit, metis, aboriginal_not_specified,
                aboriginal_info, academic_history_code, academic_history, interest_code, interest,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
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
                s.name as session_name,
                s.year as session_year,
                s.program as session_program,
                EXTRACT(EPOCH FROM (NOW() - ss.updated_at)) as seconds_since_update
            FROM student_status ss
            LEFT JOIN student_info si ON ss.user_code = si.user_code
            LEFT JOIN session s ON si.session_id = s.id
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