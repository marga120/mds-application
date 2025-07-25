from flask import Blueprint, jsonify
from flask_login import login_required
from utils.database import get_db_connection
from psycopg2.extras import RealDictCursor

session_api = Blueprint('session_api', __name__)

def get_session_name():
    """Get the session name from the single session record"""
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT name FROM session LIMIT 1")
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

@session_api.route('/session', methods=['GET'])
@login_required
def api_get_session():
    """API endpoint to get session information"""
    try:
        session_name, error = get_session_name()
        
        if error:
            return jsonify({
                'success': False,
                'message': error,
                'session_name': None
            }), 500
        
        return jsonify({
            'success': True,
            'session_name': session_name,
            'message': 'Session retrieved successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}',
            'session_name': None
        }), 500