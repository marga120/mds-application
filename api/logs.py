from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from utils.activity_logger import get_activity_logs

logs_api = Blueprint("logs_api", __name__)


@logs_api.route("/logs", methods=["GET"])
@login_required
def get_logs():
    """
    Get system activity logs for administrative monitoring.

    Retrieves activity logs including user actions, status changes, logins,
    and other system activities. Only Admin users can access system logs
    for security and privacy purposes.

    @requires: Admin authentication
    @method: GET
    @param limit: Maximum number of records to return (query param, max 50)
    @param_type limit: int
    @param offset: Number of records to skip for pagination (query param)
    @param_type offset: int
    @param action_type: Filter by specific action type (query param, optional)
    @param_type action_type: str
    @param user_search: Search for specific user (query param, optional)
    @param_type user_search: str

    @return: JSON response with activity logs
    @return_type: flask.Response
    @status_codes:
        - 200: Logs retrieved successfully
        - 403: Access denied (non-Admin user)
        - 500: Database error

    @db_tables: activity_log, user
    @pagination: Supports limit/offset pagination
    @filtering: Supports filtering by action type and user search

    @example:
        GET /api/logs?limit=25&offset=0&action_type=status_change

        Response:
        {
            "success": true,
            "logs": [
                {
                    "id": 123,
                    "user_id": 1,
                    "action_type": "status_change",
                    "target_entity": "applicant",
                    "target_id": "12345",
                    "old_value": "Not Reviewed",
                    "new_value": "Reviewed",
                    "created_at": "2025-08-26T14:30:00",
                    "user_name": "Admin User"
                }
            ],
            "count": 1,
            "limit": 25,
            "offset": 0
        }
    """

    """Get activity logs (Admin only)"""
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied"}), 403

    # Get query parameters
    limit = min(
        int(request.args.get("limit", 50)), 50
    )  # Max 50 records (also might need to update in logs.js)
    offset = int(request.args.get("offset", 0))
    action_filter = request.args.get("action_type")
    user_search = request.args.get("user_search")

    logs, error = get_activity_logs(
        limit=limit,
        offset=offset,
        filter_action_type=action_filter,
        filter_user_search=user_search,
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
