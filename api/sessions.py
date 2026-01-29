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
    restore_session,
    create_session
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

    return jsonify({"success": True, "sessions": sessions}), 200


@sessions_api.route("/sessions/create", methods=["POST"])
@login_required
def create_session_route():
    """
    Create a new academic session (Admin only).

    Creates a new session record with the provided parameters. Session name
    is auto-generated from program_code, campus, and session_abbrev.

    @http_method: POST
    @route: /api/sessions/create
    @auth: Required (Admin only)

    @request_body:
        {
            "program_code": "OGMMDS",
            "program": "Master of Data Science",
            "session_abbrev": "2025W1",
            "year": 2025,
            "campus": "UBC-V",
            "description": "Optional description"
        }

    @return: JSON response with created session
    @return_type: application/json

    @response_structure:
        {
            "success": true,
            "message": "Session created successfully",
            "session": {
                "id": 5,
                "name": "OGMMDS-V 2025W1",
                "campus": "UBC-V",
                "year": 2025
            }
        }

    @http_codes:
        201: Session created successfully
        400: Validation error or duplicate session
        403: Access denied (non-Admin)
        500: Server error

    @activity_log: Logs session creation with details

    @example:
        fetch('/api/sessions/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                program_code: 'OGMMDS',
                program: 'Master of Data Science',
                session_abbrev: '2025W1',
                year: 2025,
                campus: 'UBC-V'
            })
        })
    """
    # Check admin privileges
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied"}), 403

    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400

        # Extract and validate required fields
        program_code = data.get('program_code', '').strip().upper()
        program = data.get('program', '').strip()
        session_abbrev = data.get('session_abbrev', '').strip()
        year = data.get('year')
        campus = data.get('campus', '').strip()
        description = data.get('description', '').strip() or ''

        # Validate program_code
        if not program_code:
            return jsonify({"success": False, "message": "Program code is required"}), 400
        if len(program_code) < 2 or len(program_code) > 10:
            return jsonify({"success": False, "message": "Program code must be 2-10 characters"}), 400
        if not program_code.isalpha():
            return jsonify({"success": False, "message": "Program code must contain only letters"}), 400

        # Validate program name
        if not program:
            return jsonify({"success": False, "message": "Program name is required"}), 400
        if len(program) > 100:
            return jsonify({"success": False, "message": "Program name must be 100 characters or less"}), 400

        # Validate session_abbrev
        if not session_abbrev:
            return jsonify({"success": False, "message": "Session abbreviation is required"}), 400

        # Validate year
        if not year:
            return jsonify({"success": False, "message": "Year is required"}), 400
        try:
            year = int(year)
            if year < 2024 or year > 2035:
                return jsonify({"success": False, "message": "Year must be between 2024 and 2035"}), 400
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Invalid year format"}), 400

        # Validate campus
        if campus not in ['UBC-V', 'UBC-O']:
            return jsonify({"success": False, "message": "Campus must be 'UBC-V' or 'UBC-O'"}), 400

        # Create the session
        session_id, error = create_session(
            program_code=program_code,
            program=program,
            session_abbrev=session_abbrev,
            year=year,
            campus=campus,
            description=description
        )

        if error:
            return jsonify({"success": False, "message": error}), 400

        # Generate the session name for response
        campus_short = campus.split('-')[1]
        session_name = f"{program_code}-{campus_short} {session_abbrev}"

        # Log the activity
        log_activity(
            current_user.id,
            'create_session',
            'session',
            str(session_id),
            None,
            session_name
        )

        return jsonify({
            "success": True,
            "message": "Session created successfully",
            "session": {
                "id": session_id,
                "name": session_name,
                "campus": campus,
                "year": year,
                "program_code": program_code
            }
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


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

    return jsonify({"success": True, "sessions": sessions}), 200
    pass
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
    # Check admin privileges
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied"}), 403

    try:
        success, message = restore_session(session_id)
        
        if success:
            log_activity(current_user.id, 'restore_session', 'session', str(session_id), None, 'restored')
            return jsonify({"success": True, "message": message}), 200
        else:
            return jsonify({"success": False, "message": message}), 400
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


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
