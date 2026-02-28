"""
Sessions API — HTTP only.
All business logic delegated to SessionService.
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from services.session_service import SessionService

sessions_api = Blueprint("sessions_api", __name__)
_service = SessionService()


@sessions_api.route("/sessions", methods=["GET"])
@login_required
def get_sessions_route():
    """Get all sessions grouped by campus."""
    include_archived = request.args.get("include_archived", "false").lower() == "true"
    campus_filter = request.args.get("campus")
    try:
        sessions = _service.get_all_sessions(include_archived)
        if campus_filter and campus_filter in sessions:
            sessions = {campus_filter: sessions[campus_filter]}
        return jsonify({"success": True, "sessions": sessions}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@sessions_api.route("/sessions/create", methods=["POST"])
@login_required
def create_session_route():
    """Create a new academic session (Admin only)."""
    if not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied"}), 403
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400
    try:
        session = _service.create_session(
            program_code=data.get("program_code", ""),
            program=data.get("program", ""),
            session_abbrev=data.get("session_abbrev", ""),
            year=data.get("year"),
            campus=data.get("campus", ""),
            description=data.get("description", ""),
            user=current_user,
        )
        return jsonify({"success": True, "message": "Session created successfully", "session": session}), 201
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


@sessions_api.route("/sessions/current", methods=["GET"])
@login_required
def get_current_session_route():
    """Get all sessions (used as the 'current' endpoint)."""
    include_archived = request.args.get("include_archived", "false").lower() == "true"
    campus_filter = request.args.get("campus")
    try:
        sessions = _service.get_all_sessions(include_archived)
        if campus_filter and campus_filter in sessions:
            sessions = {campus_filter: sessions[campus_filter]}
        return jsonify({"success": True, "sessions": sessions}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@sessions_api.route("/sessions/<int:session_id>/archive", methods=["PUT"])
@login_required
def archive_session_route(session_id):
    """Archive a session (Admin only)."""
    if not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied"}), 403
    try:
        message = _service.archive_session(session_id, current_user)
        return jsonify({"success": True, "message": message}), 200
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


@sessions_api.route("/sessions/<int:session_id>/restore", methods=["PUT"])
@login_required
def restore_session_route(session_id):
    """Restore an archived session (Admin only)."""
    if not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied"}), 403
    try:
        message = _service.restore_session(session_id, current_user)
        return jsonify({"success": True, "message": message}), 200
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


@sessions_api.route("/session-name", methods=["GET"])
@login_required
def api_get_session_name():
    """Get current session name (legacy endpoint)."""
    try:
        session_name = _service.get_session_name()
        if not session_name:
            return jsonify({"success": True, "session_name": "Default Session", "message": "No session found, using default"})
        return jsonify({"success": True, "session_name": session_name, "message": "Session retrieved successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}", "session_name": None}), 500
