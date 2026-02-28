"""
Logs API — HTTP only.
All business logic delegated to LogService.
CSV streaming stays here as an HTTP concern.
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from utils.csv_helpers import create_csv_response, generate_export_filename
from services.log_service import LogService

logs_api = Blueprint("logs_api", __name__)
_service = LogService()

_STATUS_CHANGE_FIELDNAMES = ["Date/Time", "Admin Name", "Admin Email", "Applicant Code", "Old Status", "New Status"]


@logs_api.route("/logs", methods=["GET"])
@login_required
def get_logs():
    """Get activity logs (Admin only)."""
    if not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied"}), 403
    try:
        limit = min(int(request.args.get("limit", 50)), 50)
        offset = int(request.args.get("offset", 0))
        logs = _service.get_logs(
            limit=limit,
            offset=offset,
            action_type=request.args.get("action_type"),
            user_search=request.args.get("user_search"),
            target_id=request.args.get("target_id"),
        )
        return jsonify({"success": True, "logs": logs, "count": len(logs), "limit": limit, "offset": offset})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@logs_api.route("/logs/export/status-changes", methods=["GET"])
@login_required
def export_status_changes():
    """Export status change logs as CSV (Admin only)."""
    if not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied"}), 403
    try:
        user_ids_param = request.args.get("user_ids", "")
        user_ids = [int(uid) for uid in user_ids_param.split(",") if uid.strip().isdigit()]
        rows = _service.export_status_changes(user_ids or None)
        filename = generate_export_filename("status_change_logs", len(rows))
        return create_csv_response(rows, filename, _STATUS_CHANGE_FIELDNAMES)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
