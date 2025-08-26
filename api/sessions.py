from flask import Blueprint, jsonify
from flask_login import login_required
from utils.database import get_db_connection
from psycopg2.extras import RealDictCursor

sessions_api = Blueprint("sessions_api", __name__)


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
            return result["name"], None
        else:
            return None, "No session found"

    except Exception as e:
        if conn:
            conn.close()
        return None, f"Database error: {str(e)}"

@sessions_api.route("/sessions", methods=["GET"])
@login_required
def api_get_session():
    """
    Get current session information.
    
    Retrieves information about the current academic session. Session
    information is read-only and available to all authenticated users
    for display purposes.
    
    @requires: Any authenticated user
    @method: GET
    
    @return: JSON response with session information
    @return_type: flask.Response
    @status_codes:
        - 200: Session information retrieved
        - 500: Server error
    
    @db_tables: sessions
    @fallback: Returns default session name if no session found
    
    @example:
        GET /api/sessions
        
        Response:
        {
            "success": true,
            "session_name": "Session 2025 - 2026",
            "message": "Session retrieved successfully"
        }
        
        Response (fallback):
        {
            "success": true,
            "session_name": "Default Session",
            "message": "No session found, using default"
        }
    """

    """API endpoint to get session information"""
    # Session info is read-only, so all authenticated users can access
    try:
        session_name, error = get_session_name()

        if error:
            return jsonify(
                {
                    "success": True,
                    "session_name": "Default Session",
                    "message": "No session found, using default",
                }
            )

        return jsonify(
            {
                "success": True,
                "session_name": session_name,
                "message": "Session retrieved successfully",
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Server error: {str(e)}",
                    "session_name": None,
                }
            ),
            500,
        )
