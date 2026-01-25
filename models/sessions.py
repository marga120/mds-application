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
    # TODO: Implement query to fetch all sessions with applicant counts
    # TODO: Filter by is_archived based on include_archived parameter
    # TODO: Group results by campus for frontend consumption
    pass


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
    # TODO: Implement query to fetch single session by ID
    # TODO: Include applicant count in response
    pass


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
    # TODO: Validate campus value
    # TODO: Generate name if not provided (e.g., 'MDS-V 2027W')
    # TODO: Insert session record
    # TODO: Handle unique constraint violations
    pass


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
    # TODO: Build dynamic UPDATE query from kwargs
    # TODO: Validate campus value if provided
    # TODO: Update updated_at timestamp
    pass


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
    # TODO: Verify session exists
    # TODO: Set is_archived = TRUE
    # TODO: Update updated_at timestamp
    pass


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
    # TODO: Verify session exists and is archived
    # TODO: Set is_archived = FALSE
    # TODO: Update updated_at timestamp
    pass


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
    # TODO: Validate campus value
    # TODO: Query sessions filtered by campus
    # TODO: Include applicant counts
    pass


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
    # TODO: Query for most recent non-archived session
    # TODO: Optionally filter by campus
    pass


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
    # TODO: Count applicants where session_id matches
    pass
