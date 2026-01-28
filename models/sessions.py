"""
Sessions Model

Handles CRUD operations for academic sessions including campus-based filtering,
session archival, and applicant count aggregation. Supports multi-campus deployment
(UBC Vancouver and UBC Okanagan) with proper session isolation.
"""

from utils.database import get_db_connection
from psycopg2.extras import RealDictCursor


def get_session_name():
    """
    Get the session name from the single session record.
    
    Retrieves the name of the current academic session from the sessions table.
    Assumes a single active session model for the application.
    
    @return: Tuple of (session_name, error_message)
    @return_type: tuple[str, None] or tuple[None, str]
    
    @db_tables: sessions
    @limit: Uses LIMIT 1 to get single session record
    
    @example:
        session_name, error = get_session_name()
        if not error:
            print(f"Current session: {session_name}")
        else:
            print("No session found, using default")
    """

    """Get the session name from the single session record"""
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT name FROM sessions LIMIT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return result['name'], None
        else:
            return None, "No session found"
            
    except Exception as e:
        if conn:
            conn.close()
        return None, f"Database error: {str(e)}"


def get_all_sessions(include_archived=False):
    """
    Get all sessions with applicant counts, optionally including archived sessions.

    Retrieves all academic sessions from the database with aggregated applicant
    counts per session. Results are grouped by campus and sorted by year descending.

    @param include_archived: Whether to include archived (soft-deleted) sessions
    @param_type include_archived: bool

    @return: Tuple of (sessions_list, error_message)
    @return_type: tuple[list[dict], None] or tuple[None, str]

    @return_structure:
        Each session dict contains:
        - id: Session ID
        - program_code: Program code (e.g., 'MDS')
        - program: Full program name
        - session_abbrev: Session abbreviation (e.g., '2027W')
        - year: Academic year
        - name: Display name (e.g., 'MDS-V 2027W')
        - campus: Campus code ('UBC-V' or 'UBC-O')
        - is_archived: Whether session is archived
        - applicant_count: Number of applicants in this session
        - created_at: Creation timestamp

    @db_tables: sessions, applicant_info
    @joins: LEFT JOIN to count applicants per session
    @order: campus ASC, year DESC

    @example:
        sessions, error = get_all_sessions()
        if not error:
            for session in sessions:
                print(f"{session['name']}: {session['applicant_count']} applicants")
    """
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
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
        
        # Add archived filter if needed
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
        cursor.close()
        conn.close()
        
        # Group by campus
        sessions_by_campus = {"UBC-V": [], "UBC-O": []}
        for sessions in result:
            session_dict = dict(sessions)
            campus = session_dict.get('campus', 'UBC-V')

            if campus not in sessions_by_campus:
                sessions_by_campus[campus] = []
            sessions_by_campus[campus].append(session_dict)
        
        return sessions_by_campus, None
            
    except Exception as e:
        if conn:
            conn.close()
        return None, f"Database error: {str(e)}"


def get_session_by_id(session_id):
    """
    Get a specific session by its ID.

    Retrieves detailed information about a single session including
    its applicant count and all metadata fields.

    @param session_id: Unique identifier for the session
    @param_type session_id: int

    @return: Tuple of (session_dict, error_message)
    @return_type: tuple[dict, None] or tuple[None, str]

    @return_structure:
        Session dict contains:
        - id: Session ID
        - program_code: Program code
        - program: Full program name
        - session_abbrev: Session abbreviation
        - year: Academic year
        - name: Display name
        - campus: Campus code
        - is_archived: Archive status
        - applicant_count: Number of applicants
        - created_at: Creation timestamp
        - updated_at: Last update timestamp

    @db_tables: sessions, applicant_info
    @joins: LEFT JOIN to count applicants

    @example:
        session, error = get_session_by_id(5)
        if not error:
            print(f"Session: {session['name']}")
    """
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
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
        """, (session_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return dict(result), None
        else:
            return None, "Session not found"
            
    except Exception as e:
        if conn:
            conn.close()
        return None, f"Database error: {str(e)}"


def create_session(program_code, program, session_abbrev, year, campus, name=None, description=None):
    """
    Create a new academic session.

    Creates a new session record with the specified parameters. If name is not
    provided, generates one from program_code, campus, and session_abbrev.

    @param program_code: Short program code (e.g., 'MDS')
    @param_type program_code: str
    @param program: Full program name (e.g., 'Master of Data Science')
    @param_type program: str
    @param session_abbrev: Session abbreviation (e.g., '2027W')
    @param_type session_abbrev: str
    @param year: Academic year (e.g., 2027)
    @param_type year: int
    @param campus: Campus code ('UBC-V' or 'UBC-O')
    @param_type campus: str
    @param name: Optional display name (auto-generated if not provided)
    @param_type name: str | None
    @param description: Optional description
    @param_type description: str | None

    @return: Tuple of (session_id, error_message)
    @return_type: tuple[int, None] or tuple[None, str]

    @validation:
        - campus must be 'UBC-V' or 'UBC-O'
        - Unique constraint on (campus, program_code, year, session_abbrev)

    @db_tables: sessions
    @inserts: Single row with provided values

    @example:
        session_id, error = create_session('MDS', 'Master of Data Science', '2027W', 2027, 'UBC-V')
        if not error:
            print(f"Created session with ID: {session_id}")
    """
    # Validate campus
    if campus not in ['UBC-V', 'UBC-O']:
        return None, "Campus must be 'UBC-V' or 'UBC-O'"
    
    # Generate name if not provided
    if not name:
        campus_short = campus.split('-')[1]  # 'V' or 'O'
        name = f"{program_code}-{campus_short} {session_abbrev}"
    
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sessions (program_code, program, session_abbrev, year, campus, name, description, is_archived)
            VALUES (%s, %s, %s, %s, %s, %s, %s, FALSE)
            RETURNING id
        """, (program_code, program, session_abbrev, year, campus, name, description))
        
        session_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        return session_id, None
        
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        if 'unique constraint' in str(e).lower():
            return None, "Session already exists for this campus, program, and year"
        return None, f"Database error: {str(e)}"


def update_session(session_id, **kwargs):
    """
    Update an existing session's fields.

    Updates only the provided fields for a session record. Cannot update
    id or created_at fields.

    @param session_id: ID of the session to update
    @param_type session_id: int
    @param kwargs: Fields to update (program_code, program, session_abbrev, 
                   year, campus, name, description)
    @param_type kwargs: dict

    @return: Tuple of (success, error_message)
    @return_type: tuple[bool, str]

    @validation:
        - At least one field must be provided
        - campus must be 'UBC-V' or 'UBC-O' if provided
        - Cannot change session if it has applicants (optional safety check)

    @db_tables: sessions

    @example:
        success, error = update_session(5, name='MDS-V 2027W Updated')
        if success:
            print("Session updated")
    """
    if not kwargs:
        return False, "No fields provided to update"
    
    # Validate campus if provided
    if 'campus' in kwargs and kwargs['campus'] not in ['UBC-V', 'UBC-O']:
        return False, "Campus must be 'UBC-V' or 'UBC-O'"
    
    # Build dynamic UPDATE query
    allowed_fields = ['program_code', 'program', 'session_abbrev', 'year', 'campus', 'name', 'description']
    updates = []
    values = []
    
    for key, value in kwargs.items():
        if key in allowed_fields:
            updates.append(f"{key} = %s")
            values.append(value)
    
    if not updates:
        return False, "No valid fields to update"
    
    # Add updated_at timestamp
    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(session_id)
    
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        cursor = conn.cursor()
        query = f"UPDATE sessions SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, tuple(values))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return False, "Session not found"
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True, "Session updated successfully"
        
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return False, f"Database error: {str(e)}"


def archive_session(session_id):
    """
    Archive (soft-delete) a session.

    Marks a session as archived, hiding it from the session switcher UI
    while preserving all associated data. Archived sessions can be restored.

    @param session_id: ID of the session to archive
    @param_type session_id: int

    @return: Tuple of (success, message)
    @return_type: tuple[bool, str]

    @validation:
        - Session must exist
        - Session must not already be archived
        - Admin-only operation (enforced at API level)

    @db_tables: sessions
    @updates: Sets is_archived = TRUE

    @example:
        success, message = archive_session(5)
        if success:
            print("Session archived successfully")
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if session exists and is not already archived
        cursor.execute("SELECT is_archived FROM sessions WHERE id = %s", (session_id,))
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            conn.close()
            return False, "Session not found"
        
        if result['is_archived']:
            cursor.close()
            conn.close()
            return False, "Session is already archived"
        
        # Archive the session
        cursor.execute(
            "UPDATE sessions SET is_archived = TRUE, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (session_id,)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return True, "Session archived successfully"
        
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return False, f"Database error: {str(e)}"


def restore_session(session_id):
    """
    Restore an archived session.

    Unarchives a previously archived session, making it visible again
    in the session switcher UI.

    @param session_id: ID of the session to restore
    @param_type session_id: int

    @return: Tuple of (success, message)
    @return_type: tuple[bool, str]

    @validation:
        - Session must exist
        - Session must be archived
        - Admin-only operation (enforced at API level)

    @db_tables: sessions
    @updates: Sets is_archived = FALSE

    @example:
        success, message = restore_session(5)
        if success:
            print("Session restored successfully")
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if session exists and is archived
        cursor.execute("SELECT is_archived FROM sessions WHERE id = %s", (session_id,))
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            conn.close()
            return False, "Session not found"
        
        if not result['is_archived']:
            cursor.close()
            conn.close()
            return False, "Session is not archived"
        
        # Restore the session
        cursor.execute(
            "UPDATE sessions SET is_archived = FALSE, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (session_id,)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return True, "Session restored successfully"
        
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return False, f"Database error: {str(e)}"


def get_sessions_by_campus(campus, include_archived=False):
    """
    Get all sessions for a specific campus.

    Retrieves sessions filtered by campus with applicant counts.
    Used for campus-specific views and filtering.

    @param campus: Campus code ('UBC-V' or 'UBC-O')
    @param_type campus: str
    @param include_archived: Whether to include archived sessions
    @param_type include_archived: bool

    @return: Tuple of (sessions_list, error_message)
    @return_type: tuple[list[dict], None] or tuple[None, str]

    @validation:
        - campus must be 'UBC-V' or 'UBC-O'

    @db_tables: sessions, applicant_info
    @order: year DESC, session_abbrev DESC

    @example:
        sessions, error = get_sessions_by_campus('UBC-V')
        if not error:
            print(f"Found {len(sessions)} Vancouver sessions")
    """
    # Validate campus
    if campus not in ['UBC-V', 'UBC-O']:
        return None, "Campus must be 'UBC-V' or 'UBC-O'"
    
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
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
        sessions = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [dict(session) for session in sessions], None
        
    except Exception as e:
        if conn:
            conn.close()
        return None, f"Database error: {str(e)}"


def get_most_recent_session(campus=None):
    """
    Get the most recent (by year) non-archived session.

    Returns the newest session, optionally filtered by campus.
    Used to auto-select a default session when none is stored.

    @param campus: Optional campus filter ('UBC-V' or 'UBC-O')
    @param_type campus: str | None

    @return: Tuple of (session_dict, error_message)
    @return_type: tuple[dict, None] or tuple[None, str]

    @db_tables: sessions
    @order: year DESC, created_at DESC
    @limit: 1

    @example:
        session, error = get_most_recent_session()
        if not error:
            print(f"Most recent: {session['name']}")
    """
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
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
        
        # Add campus filter if specified
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
        
        if params:
            cursor.execute(query, tuple(params))
        else:
            cursor.execute(query)
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return dict(result), None
        else:
            return None, "No sessions found"
            
    except Exception as e:
        if conn:
            conn.close()
        return None, f"Database error: {str(e)}"


def get_session_applicant_count(session_id):
    """
    Get the count of applicants in a specific session.

    Returns the number of applicants associated with the given session.
    Used for display in session switcher and validation.

    @param session_id: ID of the session
    @param_type session_id: int

    @return: Tuple of (count, error_message)
    @return_type: tuple[int, None] or tuple[None, str]

    @db_tables: applicant_info

    @example:
        count, error = get_session_applicant_count(5)
        if not error:
            print(f"Session has {count} applicants")
    """
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM applicant_info WHERE session_id = %s",
            (session_id,)
        )
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        return count, None
        
    except Exception as e:
        if conn:
            conn.close()
        return None, f"Database error: {str(e)}"
