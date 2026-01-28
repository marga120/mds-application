"""
Sessions API

REST API endpoints for managing academic sessions. Provides endpoints for listing,
retrieving, and archiving sessions. Supports campus-based filtering and session
switching for multi-campus deployment.
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models.sessions import (
    get_session_name,
    get_all_sessions,
    get_session_by_id,
    get_sessions_by_campus,
    get_most_recent_session,
    archive_session,
    restore_session
)
from utils.activity_logger import log_activity

sessions_api = Blueprint("sessions_api", __name__)


@sessions_api.route("/sessions", methods=["GET"])
@login_required
def get_sessions_route():
    """
    Get all sessions grouped by campus.

    Returns all non-archived sessions with applicant counts, organized by campus
    for display in the session switcher UI. Supports optional query parameters
    for filtering.

    @http_method: GET
    @route: /api/sessions
    @auth: Required (all roles)

    @query_params:
        - include_archived: Include archived sessions (default: false)
        - campus: Filter by campus ('UBC-V' or 'UBC-O')

    @return: JSON response with sessions grouped by campus
    @return_type: application/json

    @response_structure:
        {
            "success": true,
            "sessions": {
                "UBC-V": [
                    {
                        "id": 1,
                        "name": "MDS-V 2027W",
                        "program_code": "MDS",
                        "year": 2027,
                        "session_abbrev": "2027W",
                        "campus": "UBC-V",
                        "applicant_count": 145,
                        "is_archived": false
                    },
                    ...
                ],
                "UBC-O": [...]
            }
        }

    @http_codes:
        200: Sessions retrieved successfully
        500: Database error

    @example:
        fetch('/api/sessions')
            .then(res => res.json())
            .then(data => console.log(data.sessions));

        fetch('/api/sessions?campus=UBC-V')
            .then(res => res.json())
            .then(data => console.log(data.sessions));
    """
    #Include_archived
    if not current_user.is_authenticated:
        return jsonify({"success": False, "message": "Authentication required"}), 401

    include_archived = request.args.get('include_archived', 'false').lower() == 'true'
    campus_filter = request.args.get('campus', None)
    
    sessions, error = get_all_sessions(include_archived)
    #sessions grouped by campus
    
    if error:
        return jsonify({"success": False, "message": error}), 400
    #if the campus filter is specified, 
    if campus_filter and campus_filter in sessions:
        session = {campus_filter: sessions[campus_filter]}

    return jsonify({"success": True, "rating": sessions}), 200
    pass


@sessions_api.route("/sessions/current", methods=["GET"])
@login_required
def get_current_session_route():
    """
    Get the current/default session.

    Returns information about the most recent session, used for auto-selection
    when no session is stored in the client. Falls back to a default response
    if no sessions exist.

    @http_method: GET
    @route: /api/sessions/current
    @auth: Required (all roles)

    @return: JSON response with current session information
    @return_type: application/json

    @response_structure:
        {
            "success": true,
            "session": {
                "id": 1,
                "name": "MDS-V 2027W",
                "program_code": "MDS",
                "year": 2027,
                "campus": "UBC-V",
                "applicant_count": 145
            }
        }

    @http_codes:
        200: Session retrieved successfully
        404: No sessions found

    @example:
        fetch('/api/sessions/current')
            .then(res => res.json())
            .then(data => console.log(data.session));
    """
    # TODO: Call get_most_recent_session()
    # TODO: Return session data or 404 if none exist
    pass


@sessions_api.route("/sessions/<int:session_id>", methods=["GET"])
@login_required
def get_session_route(session_id):
    """
    Get a specific session by ID.

    Retrieves detailed information about a single session including
    all metadata and applicant count.

    @http_method: GET
    @route: /api/sessions/<session_id>
    @auth: Required (all roles)

    @path_param session_id: ID of the session to retrieve
    @path_param_type session_id: int

    @return: JSON response with session details
    @return_type: application/json

    @response_structure:
        {
            "success": true,
            "session": {
                "id": 1,
                "name": "MDS-V 2027W",
                "program_code": "MDS",
                "program": "Master of Data Science",
                "year": 2027,
                "session_abbrev": "2027W",
                "campus": "UBC-V",
                "description": "...",
                "applicant_count": 145,
                "is_archived": false,
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z"
            }
        }

    @http_codes:
        200: Session retrieved successfully
        404: Session not found
        500: Database error

    @example:
        fetch('/api/sessions/1')
            .then(res => res.json())
            .then(data => console.log(data.session));
    """
    # TODO: Call get_session_by_id(session_id)
    # TODO: Return session data or 404 if not found
    pass


@sessions_api.route("/sessions/<int:session_id>/archive", methods=["PUT"])
@login_required
def archive_session_route(session_id):
    """
    Archive a session (Admin only).

    Soft-deletes a session by marking it as archived. Archived sessions
    are hidden from the session switcher but all data is preserved.
    This action can be reversed with the restore endpoint.

    @http_method: PUT
    @route: /api/sessions/<session_id>/archive
    @auth: Required (Admin only)

    @path_param session_id: ID of the session to archive
    @path_param_type session_id: int

    @return: JSON response with operation result
    @return_type: application/json

    @response_structure:
        {
            "success": true,
            "message": "Session archived successfully"
        }

    @http_codes:
        200: Session archived successfully
        400: Session already archived or invalid
        403: Access denied (non-Admin)
        404: Session not found
        500: Database error

    @activity_log: Logs archive action with session details

    @example:
        fetch('/api/sessions/1/archive', { method: 'PUT' })
            .then(res => res.json())
            .then(data => console.log(data.message));
    """
    # TODO: Check admin privileges
    # TODO: Call archive_session(session_id)
    # TODO: Log activity
    # TODO: Return result
    pass


@sessions_api.route("/sessions/<int:session_id>/restore", methods=["PUT"])
@login_required
def restore_session_route(session_id):
    """
    Restore an archived session (Admin only).

    Unarchives a previously archived session, making it visible again
    in the session switcher UI.

    @http_method: PUT
    @route: /api/sessions/<session_id>/restore
    @auth: Required (Admin only)

    @path_param session_id: ID of the session to restore
    @path_param_type session_id: int

    @return: JSON response with operation result
    @return_type: application/json

    @response_structure:
        {
            "success": true,
            "message": "Session restored successfully"
        }

    @http_codes:
        200: Session restored successfully
        400: Session not archived or invalid
        403: Access denied (non-Admin)
        404: Session not found
        500: Database error

    @activity_log: Logs restore action with session details

    @example:
        fetch('/api/sessions/1/restore', { method: 'PUT' })
            .then(res => res.json())
            .then(data => console.log(data.message));
    """
    # TODO: Check admin privileges
    # TODO: Call restore_session(session_id)
    # TODO: Log activity
    # TODO: Return result
    pass


# Legacy endpoint for backward compatibility
@sessions_api.route("/session-name", methods=["GET"])
@login_required
def api_get_session_name():
    """
    Get current session name (legacy endpoint).

    Maintained for backward compatibility with existing code.
    New code should use /api/sessions/current instead.

    @http_method: GET
    @route: /api/session-name
    @auth: Required (all roles)
    @deprecated: Use /api/sessions/current instead

    @return: JSON response with session name
    @return_type: application/json

    @response_structure:
        {
            "success": true,
            "session_name": "MDS-V 2027W",
            "message": "Session retrieved successfully"
        }

    @http_codes:
        200: Session name retrieved
        500: Server error
    """
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
