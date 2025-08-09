from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from utils.activity_logger import get_activity_logs

logs_api = Blueprint("logs_api", __name__)


@logs_api.route("/logs", methods=["GET"])
@login_required
def get_logs():
    """Get activity logs (Admin only)"""
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied"}), 403

    # Get query parameters
    limit = min(int(request.args.get("limit", 100)), 500)  # Max 500 records
    offset = int(request.args.get("offset", 0))
    action_filter = request.args.get("action_type")
    user_filter = request.args.get("user_id")

    logs, error = get_activity_logs(
        limit=limit,
        offset=offset,
        filter_action_type=action_filter,
        filter_user_id=user_filter,
    )

    if error:
        return jsonify({"success": False, "message": error}), 500

    return jsonify(
        {
            "success": True,
            "logs": logs,
            "count": len(logs),
            "limit": limit,
            "offset": offset,
        }
    )
