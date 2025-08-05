from utils.database import get_db_connection
from psycopg2.extras import RealDictCursor


def get_session_name():
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