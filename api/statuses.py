"""
Status Configuration API — HTTP only.
All business logic delegated to StatusService.
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from services.status_service import StatusService

statuses_bp = Blueprint("statuses", __name__)
_service = StatusService()


@statuses_bp.route("/api/statuses", methods=["GET"])
@login_required
def get_statuses_route():
    """Get active statuses for dropdowns. All authenticated users."""
    try:
        return jsonify({"success": True, "statuses": _service.get_active_statuses()})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@statuses_bp.route("/api/admin/statuses", methods=["GET"])
@login_required
def get_all_statuses_admin_route():
    """Get all statuses including inactive (Admin only)."""
    if not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied. Admin privileges required."}), 403
    try:
        return jsonify({"success": True, "statuses": _service.get_all_statuses()})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@statuses_bp.route("/api/admin/statuses", methods=["POST"])
@login_required
def create_status_route():
    """Create a new status (Admin only)."""
    if not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied. Admin privileges required."}), 403
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Invalid request data"}), 400
    try:
        message = _service.create_status(
            data.get("status_name"),
            data.get("badge_color", "gray"),
            data.get("display_order"),
            current_user,
        )
        return jsonify({"success": True, "message": message})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@statuses_bp.route("/api/admin/statuses/<int:status_id>", methods=["PUT"])
@login_required
def update_status_route(status_id):
    """Update a status (Admin only)."""
    if not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied. Admin privileges required."}), 403
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Invalid request data"}), 400
    try:
        message = _service.update_status(
            status_id,
            data.get("status_name"),
            data.get("badge_color"),
            data.get("display_order"),
            data.get("is_active"),
            current_user,
        )
        return jsonify({"success": True, "message": message})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@statuses_bp.route("/api/admin/statuses/<int:status_id>", methods=["DELETE"])
@login_required
def delete_status_route(status_id):
    """Delete a status and reassign applicants (Admin only)."""
    if not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied. Admin privileges required."}), 403
    try:
        message = _service.delete_status(status_id, current_user)
        return jsonify({"success": True, "message": message})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@statuses_bp.route("/api/admin/statuses/reorder", methods=["POST"])
@login_required
def reorder_statuses_route():
    """Batch update display_order (Admin only)."""
    if not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied. Admin privileges required."}), 403
    data = request.get_json() or {}
    try:
        message = _service.reorder_statuses(data.get("statuses", []), current_user)
        return jsonify({"success": True, "message": message})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
