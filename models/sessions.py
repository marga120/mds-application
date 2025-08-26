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