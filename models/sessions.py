"""
Sessions Model

Handles CRUD operations for academic sessions including campus-based filtering,
session archival, and applicant count aggregation. Supports multi-campus deployment
(UBC Vancouver and UBC Okanagan) with proper session isolation.
"""

from utils.db_helpers import db_connection, db_transaction


def get_session_name():
    """
    Get the session name from the single session record.

    @return: Tuple of (session_name, error_message)
    @return_type: tuple[str, None] or tuple[None, str]

    @db_tables: sessions
    @limit: Uses LIMIT 1 to get single session record
    """
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("SELECT name FROM sessions LIMIT 1")
            result = cursor.fetchone()
        if result:
            return result["name"], None
        return None, "No session found"
    except Exception as e:
        return None, f"Database error: {str(e)}"


def get_all_sessions(include_archived=False):
    """
    Get all sessions with applicant counts, optionally including archived sessions.

    @param include_archived: Whether to include archived (soft-deleted) sessions
    @param_type include_archived: bool

    @return: Tuple of (sessions_by_campus dict, error_message)
    @return_type: tuple[dict, None] or tuple[None, str]

    @db_tables: sessions, applicant_info
    @joins: LEFT JOIN to count applicants per session
    @order: campus ASC, year DESC
    """
    try:
        with db_connection() as (conn, cursor):
            query = """
            SELECT
                s.id,
                s.program_code,
                s.program,
                s.session_abbrev,
                s.year,
                s.name,
                s.description,
                s.campus,
                s.is_archived,
                s.created_at,
                s.updated_at,
                COUNT(a.user_code) as applicant_count
            FROM sessions s
            LEFT JOIN applicant_info a ON s.id = a.session_id
            WHERE 1=1
            """
            if not include_archived:
                query += " AND s.is_archived = FALSE"
            query += """
                GROUP BY s.id, s.program_code, s.program, s.session_abbrev,
                        s.year, s.name, s.description, s.campus, s.is_archived,
                        s.created_at, s.updated_at
                ORDER BY s.campus ASC, s.year DESC, s.session_abbrev DESC
            """
            cursor.execute(query)
            result = cursor.fetchall()

        sessions_by_campus = {}
        for session in result:
            session_dict = dict(session)
            campus = session_dict.get("campus", "")
            if campus not in sessions_by_campus:
                sessions_by_campus[campus] = []
            sessions_by_campus[campus].append(session_dict)

        return sessions_by_campus, None
    except Exception as e:
        return None, f"Database error: {str(e)}"


def get_session_by_id(session_id):
    """
    Get a specific session by its ID.

    @param session_id: Unique identifier for the session
    @param_type session_id: int

    @return: Tuple of (session_dict, error_message)
    @return_type: tuple[dict, None] or tuple[None, str]

    @db_tables: sessions, applicant_info
    @joins: LEFT JOIN to count applicants
    """
    try:
        with db_connection() as (conn, cursor):
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
                    s.campus,
                    s.is_archived,
                    s.created_at,
                    s.updated_at,
                    COUNT(a.user_code) as applicant_count
                FROM sessions s
                LEFT JOIN applicant_info a ON s.id = a.session_id
                WHERE s.id = %s
                GROUP BY s.id, s.program_code, s.program, s.session_abbrev,
                         s.year, s.name, s.description, s.campus, s.is_archived,
                         s.created_at, s.updated_at
                """,
                (session_id,),
            )
            result = cursor.fetchone()
        if result:
            return dict(result), None
        return None, "Session not found"
    except Exception as e:
        return None, f"Database error: {str(e)}"


def create_session(program_code, program, session_abbrev, year, campus, name=None, description=None):
    """
    Create a new academic session.

    @param program_code: Short program code (e.g., 'MDS')
    @param program: Full program name (e.g., 'Master of Data Science')
    @param session_abbrev: Session abbreviation (e.g., '2027W')
    @param year: Academic year (e.g., 2027)
    @param campus: Campus code (free-text, e.g. 'UBC-V', 'UBC-O', 'SFU')
    @param name: Optional display name (auto-generated if not provided)
    @param description: Optional description

    @return: Tuple of (session_id, error_message)
    @return_type: tuple[int, None] or tuple[None, str]

    @db_tables: sessions
    """
    if not name:
        name = f"{program_code}-{campus} {session_abbrev}"

    try:
        with db_transaction() as (conn, cursor):
            cursor.execute(
                """
                INSERT INTO sessions (program_code, program, session_abbrev, year, campus, name, description, is_archived)
                VALUES (%s, %s, %s, %s, %s, %s, %s, FALSE)
                RETURNING id
                """,
                (program_code, program, session_abbrev, year, campus, name, description),
            )
            return cursor.fetchone()["id"], None
    except Exception as e:
        if "unique constraint" in str(e).lower():
            return None, "Session already exists for this campus, program, and year"
        return None, f"Database error: {str(e)}"


def update_session(session_id, **kwargs):
    """
    Update an existing session's fields.

    @param session_id: ID of the session to update
    @param kwargs: Fields to update (program_code, program, session_abbrev,
                   year, campus, name, description)

    @return: Tuple of (success, error_message)
    @return_type: tuple[bool, str]

    @db_tables: sessions
    """
    if not kwargs:
        return False, "No fields provided to update"

    allowed_fields = ["program_code", "program", "session_abbrev", "year", "campus", "name", "description"]
    updates = []
    values = []

    for key, value in kwargs.items():
        if key in allowed_fields:
            updates.append(f"{key} = %s")
            values.append(value)

    if not updates:
        return False, "No valid fields to update"

    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(session_id)

    try:
        with db_transaction() as (conn, cursor):
            query = f"UPDATE sessions SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(query, tuple(values))
            if cursor.rowcount == 0:
                return False, "Session not found"
        return True, "Session updated successfully"
    except Exception as e:
        return False, f"Database error: {str(e)}"


def archive_session(session_id):
    """
    Archive (soft-delete) a session.

    @param session_id: ID of the session to archive
    @return: Tuple of (success, message)
    @db_tables: sessions
    @updates: Sets is_archived = TRUE
    """
    try:
        with db_transaction() as (conn, cursor):
            cursor.execute("SELECT is_archived FROM sessions WHERE id = %s", (session_id,))
            result = cursor.fetchone()

            if not result:
                return False, "Session not found"
            if result["is_archived"]:
                return False, "Session is already archived"

            cursor.execute(
                "UPDATE sessions SET is_archived = TRUE, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (session_id,),
            )
        return True, "Session archived successfully"
    except Exception as e:
        return False, f"Database error: {str(e)}"


def restore_session(session_id):
    """
    Restore an archived session.

    @param session_id: ID of the session to restore
    @return: Tuple of (success, message)
    @db_tables: sessions
    @updates: Sets is_archived = FALSE
    """
    try:
        with db_transaction() as (conn, cursor):
            cursor.execute("SELECT is_archived FROM sessions WHERE id = %s", (session_id,))
            result = cursor.fetchone()

            if not result:
                return False, "Session not found"
            if not result["is_archived"]:
                return False, "Session is not archived"

            cursor.execute(
                "UPDATE sessions SET is_archived = FALSE, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (session_id,),
            )
        return True, "Session restored successfully"
    except Exception as e:
        return False, f"Database error: {str(e)}"


def get_sessions_by_campus(campus, include_archived=False):
    """
    Get all sessions for a specific campus.

    @param campus: Campus code (free-text)
    @param include_archived: Whether to include archived sessions

    @return: Tuple of (sessions_list, error_message)
    @return_type: tuple[list[dict], None] or tuple[None, str]

    @db_tables: sessions, applicant_info
    """
    try:
        with db_connection() as (conn, cursor):
            query = """
                SELECT
                    s.id,
                    s.program_code,
                    s.program,
                    s.session_abbrev,
                    s.year,
                    s.name,
                    s.description,
                    s.campus,
                    s.is_archived,
                    s.created_at,
                    s.updated_at,
                    COUNT(a.user_code) as applicant_count
                FROM sessions s
                LEFT JOIN applicant_info a ON s.id = a.session_id
                WHERE s.campus = %s
            """
            params = [campus]
            if not include_archived:
                query += " AND s.is_archived = FALSE"
            query += """
                GROUP BY s.id, s.program_code, s.program, s.session_abbrev,
                         s.year, s.name, s.description, s.campus, s.is_archived,
                         s.created_at, s.updated_at
                ORDER BY s.year DESC, s.session_abbrev DESC
            """
            cursor.execute(query, tuple(params))
            return [dict(s) for s in cursor.fetchall()], None
    except Exception as e:
        return None, f"Database error: {str(e)}"


def get_most_recent_session(campus=None):
    """
    Get the most recent (by year) non-archived session.

    @param campus: Optional campus filter (free-text)
    @return: Tuple of (session_dict, error_message)

    @db_tables: sessions
    @order: year DESC, created_at DESC
    @limit: 1
    """
    try:
        with db_connection() as (conn, cursor):
            query = """
                SELECT
                    s.id,
                    s.program_code,
                    s.program,
                    s.session_abbrev,
                    s.year,
                    s.name,
                    s.description,
                    s.campus,
                    s.is_archived,
                    s.created_at,
                    s.updated_at,
                    COUNT(a.user_code) as applicant_count
                FROM sessions s
                LEFT JOIN applicant_info a ON s.id = a.session_id
                WHERE s.is_archived = FALSE
            """
            params = []
            if campus:
                query += " AND s.campus = %s"
                params.append(campus)
            query += """
                GROUP BY s.id, s.program_code, s.program, s.session_abbrev,
                         s.year, s.name, s.description, s.campus, s.is_archived,
                         s.created_at, s.updated_at
                ORDER BY s.year DESC, s.created_at DESC
                LIMIT 1
            """
            cursor.execute(query, tuple(params))
            result = cursor.fetchone()
        if result:
            return dict(result), None
        return None, "No sessions found"
    except Exception as e:
        return None, f"Database error: {str(e)}"


def get_session_applicant_count(session_id):
    """
    Get the count of applicants in a specific session.

    @param session_id: ID of the session
    @return: Tuple of (count, error_message)

    @db_tables: applicant_info
    """
    try:
        with db_connection() as (conn, cursor):
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM applicant_info WHERE session_id = %s",
                (session_id,),
            )
            return cursor.fetchone()["cnt"], None
    except Exception as e:
        return None, f"Database error: {str(e)}"
