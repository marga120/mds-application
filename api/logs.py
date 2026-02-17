from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from utils.activity_logger import get_activity_logs
from utils.db_helpers import fetch_all
from utils.csv_helpers import create_csv_response, generate_export_filename

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
    target_id = request.args.get("target_id")

    logs, error = get_activity_logs(
        limit=limit,
        offset=offset,
        filter_action_type=action_filter,
        filter_user_search=user_search,
        filter_target_id=target_id,
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


@logs_api.route("/logs/export/status-changes", methods=["GET"])
@login_required
def export_status_changes():
    """Export applicant status change logs as a CSV file.

    Returns all status_change activity log entries as a downloadable CSV.
    Optionally filtered to a specific admin's changes via user_id query param.

    @requires: Admin authentication
    @method: GET
    @param user_id: Filter by admin user ID (query param, optional)
    @param_type user_id: int

    @return: CSV file attachment
    @status_codes:
        - 200: CSV file returned
        - 403: Access denied (non-Admin user)
        - 500: Database or generation error
    """
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied"}), 403

    user_ids_param = request.args.get("user_ids", "")
    user_ids = [int(uid) for uid in user_ids_param.split(",") if uid.strip().isdigit()]

    try:
        where_clause = "WHERE al.action_type = 'status_change'"
        params = []
        if user_ids:
            placeholders = ",".join(["%s"] * len(user_ids))
            where_clause += f" AND al.user_id IN ({placeholders})"
            params.extend(user_ids)

        rows = fetch_all(
            f"""
            SELECT al.created_at, u.first_name, u.last_name, u.email,
                   al.target_id, al.old_value, al.new_value
            FROM activity_log al
            LEFT JOIN "user" u ON al.user_id = u.id
            {where_clause}
            ORDER BY al.created_at DESC
            """,
            params if params else None,
        )

        fieldnames = ["Date/Time", "Admin Name", "Admin Email", "Applicant Code", "Old Status", "New Status"]

        export_rows = []
        for row in rows:
            first = row["first_name"]
            last = row["last_name"]
            admin_name = f"{first} {last}".strip() if (first or last) else "Unknown User"
            export_rows.append({
                "Date/Time": row["created_at"].strftime("%Y-%m-%d %H:%M:%S") if row["created_at"] else "",
                "Admin Name": admin_name,
                "Admin Email": row["email"] or "",
                "Applicant Code": row["target_id"] or "",
                "Old Status": row["old_value"] or "",
                "New Status": row["new_value"] or "",
            })

        filename = generate_export_filename("status_change_logs", len(export_rows))
        return create_csv_response(export_rows, filename, fieldnames)

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
