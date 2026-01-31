"""
Core Applicant Model Functions

This module contains the basic CRUD operations for applicants including
retrieval of applicant data, status, test scores, and institutions.
"""

from psycopg2.extras import RealDictCursor
from utils.db_helpers import db_connection, db_transaction


def convert_id_to_string(value):
    """Convert ID numbers to clean strings, removing .0 from floats."""
    import pandas as pd
    if pd.isna(value):
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def get_all_applicant_status(session_id=None):
    """
    Get all applicants with their status and basic information.

    @param session_id: Optional session ID to filter applicants by session
    @return: Tuple of (applicants_list, error_message)
    """
    try:
        with db_connection() as (conn, cursor):
            query = """
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
                    ROUND(AVG(r.rating), 1) as overall_rating,
                    ai.sent as review_status,
                    latest_log.created_at as review_status_updated_at,
                    CASE WHEN ai.canadian = true THEN 'Yes' ELSE 'No' END as canadian,
                    si.gender,
                    si.country_citizenship as citizenship_country,
                    si.visa_type_code as visa,
                    si.session_id
                FROM applicant_status ss
                LEFT JOIN applicant_info si ON ss.user_code = si.user_code
                LEFT JOIN ratings r ON ss.user_code = r.user_code
                LEFT JOIN application_info ai ON ss.user_code = ai.user_code
                LEFT JOIN LATERAL(
                    SELECT created_at
                    FROM activity_log
                    WHERE action_type = 'status_change'
                    AND target_id = ss.user_code
                    ORDER BY created_at DESC
                    LIMIT 1
                ) latest_log ON true
            """

            params = []
            if session_id is not None:
                query += " WHERE si.session_id = %s"
                params.append(session_id)

            query += """
                GROUP BY ss.user_code, si.family_name, si.given_name, si.email,
                         ss.student_number, ss.app_start, ss.submit_date,
                         ss.status_code, ss.status, ss.detail_status, ss.updated_at,
                         ai.sent, ai.canadian, si.gender, si.country_citizenship, si.visa_type_code,
                         latest_log.created_at, si.session_id
                ORDER BY ss.submit_date DESC, si.family_name
            """

            if params:
                cursor.execute(query, tuple(params))
            else:
                cursor.execute(query)

            return cursor.fetchall(), None

    except Exception as e:
        return None, f"Database error: {str(e)}"


def get_all_sessions():
    """Get all academic sessions with applicant counts."""
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
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
            """)
            return cursor.fetchall(), None

    except Exception as e:
        return None, f"Database error: {str(e)}"


def get_applicant_info_by_code(user_code):
    """Get detailed applicant information by user code."""
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
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
            """, (user_code,))
            return cursor.fetchone(), None

    except Exception as e:
        return None, f"Database error: {str(e)}"


def get_applicant_test_scores_by_code(user_code):
    """Get all test scores for an applicant by user code."""
    try:
        with db_connection() as (conn, cursor):
            test_scores = {}

            cursor.execute("SELECT * FROM toefl WHERE user_code = %s ORDER BY toefl_number", (user_code,))
            test_scores["toefl"] = cursor.fetchall()

            cursor.execute("SELECT * FROM ielts WHERE user_code = %s ORDER BY ielts_number", (user_code,))
            test_scores["ielts"] = cursor.fetchall()

            cursor.execute("SELECT * FROM melab WHERE user_code = %s", (user_code,))
            test_scores["melab"] = cursor.fetchone()

            cursor.execute("SELECT * FROM pte WHERE user_code = %s", (user_code,))
            test_scores["pte"] = cursor.fetchone()

            cursor.execute("SELECT * FROM cael WHERE user_code = %s", (user_code,))
            test_scores["cael"] = cursor.fetchone()

            cursor.execute("SELECT * FROM celpip WHERE user_code = %s", (user_code,))
            test_scores["celpip"] = cursor.fetchone()

            cursor.execute("SELECT * FROM duolingo WHERE user_code = %s", (user_code,))
            test_scores["duolingo"] = cursor.fetchone()

            cursor.execute("SELECT * FROM alt_elpp WHERE user_code = %s", (user_code,))
            test_scores["alt_elpp"] = cursor.fetchone()

            cursor.execute("SELECT * FROM gre WHERE user_code = %s", (user_code,))
            test_scores["gre"] = cursor.fetchone()

            cursor.execute("SELECT * FROM gmat WHERE user_code = %s", (user_code,))
            test_scores["gmat"] = cursor.fetchone()

            return test_scores, None

    except Exception as e:
        return None, f"Database error: {str(e)}"


def get_applicant_institutions_by_code(user_code):
    """Get all institution information for an applicant by user code."""
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT
                    institution_number, institution_code, full_name, country,
                    start_date, end_date, program_study, degree_confer_code,
                    degree_confer, date_confer, credential_receive_code,
                    credential_receive, expected_confer_date, expected_credential_code,
                    expected_credential, honours, fail_withdraw, reason, gpa
                FROM institution_info
                WHERE user_code = %s
                ORDER BY institution_number
            """, (user_code,))
            return cursor.fetchall(), None

    except Exception as e:
        return None, f"Database error: {str(e)}"


def get_applicant_application_info_by_code(user_code):
    """Get application_info data for an applicant by user code."""
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT
                    user_code, sent, full_name, canadian, english,
                    cs, stat, math, additional_comments, gpa, highest_degree, degree_area,
                    mds_v, mds_cl, mds_o, scholarship,
                    english_status, english_description, english_comment
                FROM application_info
                WHERE user_code = %s
            """, (user_code,))
            return cursor.fetchone(), None

    except Exception as e:
        return None, f"Database error: {str(e)}"


def update_applicant_application_status(user_code, status):
    """Update applicant status in application_info table."""
    try:
        with db_transaction() as (conn, cursor):
            cursor.execute(
                "UPDATE application_info SET sent = %s WHERE user_code = %s",
                (status, user_code),
            )

            if cursor.rowcount == 0:
                cursor.execute(
                    "INSERT INTO application_info (user_code, sent) VALUES (%s, %s)",
                    (user_code, status),
                )

        return True, "Status updated successfully"

    except Exception as e:
        return False, f"Database error: {str(e)}"


def update_applicant_prerequisites(user_code, cs, stat, math, gpa=None, additional_comments=None, mds_v=None, mds_cl=None, mds_o=None):
    """Update applicant prerequisites in application_info table."""
    try:
        with db_transaction() as (conn, cursor):
            # Validate user_code exists
            cursor.execute("SELECT user_code FROM applicant_info WHERE user_code = %s", (user_code,))
            if not cursor.fetchone():
                return False, "Applicant not found"

            cursor.execute("""
                UPDATE application_info
                SET cs = %s, stat = %s, math = %s, gpa = %s, additional_comments = %s,
                    mds_v = %s, mds_cl = %s, mds_o = %s
                WHERE user_code = %s
            """, (cs, stat, math, gpa, additional_comments, mds_v, mds_cl, mds_o, user_code))

            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO application_info (user_code, cs, stat, math, gpa, additional_comments, mds_v, mds_cl, mds_o)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (user_code, cs, stat, math, gpa, additional_comments,
                      mds_v or 'No', mds_cl or 'No', mds_o or 'Yes'))

        return True, "Prerequisites updated successfully"

    except Exception as e:
        return False, f"Database error: {str(e)}"


def update_applicant_scholarship(user_code, scholarship):
    """Update scholarship decision for an applicant."""
    try:
        with db_transaction() as (conn, cursor):
            cursor.execute("SELECT user_code FROM applicant_info WHERE user_code = %s", (user_code,))
            if not cursor.fetchone():
                return False, "Applicant not found"

            cursor.execute(
                "UPDATE application_info SET scholarship = %s WHERE user_code = %s",
                (scholarship, user_code),
            )

            if cursor.rowcount == 0:
                cursor.execute(
                    "INSERT INTO application_info (user_code, scholarship) VALUES (%s, %s)",
                    (user_code, scholarship),
                )

        return True, "Scholarship decision updated successfully"

    except Exception as e:
        return False, f"Database error: {str(e)}"


def update_english_comment(user_code, english_comment):
    """Update English comment for applicant in application_info table."""
    try:
        with db_transaction() as (conn, cursor):
            cursor.execute("SELECT user_code FROM applicant_info WHERE user_code = %s", (user_code,))
            if not cursor.fetchone():
                return False, "Applicant not found"

            cursor.execute(
                "UPDATE application_info SET english_comment = %s WHERE user_code = %s",
                (english_comment, user_code),
            )

            if cursor.rowcount == 0:
                cursor.execute(
                    "INSERT INTO application_info (user_code, english_comment) VALUES (%s, %s)",
                    (user_code, english_comment),
                )

        return True, "English comment updated successfully"

    except Exception as e:
        return False, f"Database error: {str(e)}"


def update_english_status(user_code, english_status):
    """Update English status for applicant in application_info table."""
    try:
        with db_transaction() as (conn, cursor):
            cursor.execute("SELECT user_code FROM applicant_info WHERE user_code = %s", (user_code,))
            if not cursor.fetchone():
                return False, "Applicant not found"

            english_boolean = english_status in ["Passed", "Not Required"]

            cursor.execute(
                "UPDATE application_info SET english_status = %s, english = %s WHERE user_code = %s",
                (english_status, english_boolean, user_code),
            )

            if cursor.rowcount == 0:
                cursor.execute(
                    "INSERT INTO application_info (user_code, english_status, english) VALUES (%s, %s, %s)",
                    (user_code, english_status, english_boolean),
                )

        return True, "English status updated successfully"

    except Exception as e:
        return False, f"Database error: {str(e)}"


def clear_all_applicant_data():
    """Clear all applicant data from the database."""
    try:
        with db_transaction() as (conn, cursor):
            tables_to_clear = [
                'ratings', 'applicant_documents', 'toefl', 'ielts', 'melab', 'pte', 'cael', 'celpip',
                'duolingo', 'alt_elpp', 'gre', 'gmat', 'institution_info',
                'application_info', 'applicant_status', 'program_info', 'applicant_info',
            ]

            cursor.execute("SELECT COUNT(*) as count FROM applicant_info")
            records_cleared = cursor.fetchone()['count']

            tables_cleared = 0
            for table in tables_to_clear:
                cursor.execute(f"DELETE FROM {table}")
                tables_cleared += 1

        return True, "All applicant data has been cleared successfully", tables_cleared, records_cleared

    except Exception as e:
        return False, f"Error clearing data: {str(e)}", 0, 0
