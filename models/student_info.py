from utils.database import get_db_connection
from psycopg2.extras import RealDictCursor
import pandas as pd
from datetime import datetime
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


def process_csv_data(df):
    """Process CSV data and insert into student_info and student_status tables"""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed", 0

    try:
        cursor = conn.cursor()
        records_processed = 0

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

            # Insert into student_info table
            student_info_query = """
            INSERT INTO student_info (
                user_code, title, family_name, given_name, middle_name, preferred_name,
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
                %s, %s)
            ON CONFLICT (user_code) DO UPDATE SET
                family_name = EXCLUDED.family_name,
                given_name = EXCLUDED.given_name,
                email = EXCLUDED.email,
                updated_at = CASE 
                    WHEN student_info.family_name IS DISTINCT FROM EXCLUDED.family_name 
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
                    # None,  # aboriginal
                    # None,  # first_nation
                    # None,  # inuit
                    # None,  # metis
                    # None,  # aboriginal_not_specified
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
    """Get all students from student_status joined with student_info"""
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
                gender, country_birth_code, country_birth, date_birth, 
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
