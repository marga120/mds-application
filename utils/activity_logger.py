"""
ACTIVITY LOGGER UTILITY

This module provides system-wide activity logging and audit trail functionality.
It tracks user actions, status changes, data modifications, and system events
for security, compliance, and debugging purposes. Logs are stored in the
activity_log database table with user attribution and metadata support.
"""

from utils.db_helpers import db_connection, db_transaction
from flask_login import current_user
import json
from datetime import datetime


def log_activity(
    action_type,
    target_entity=None,
    target_id=None,
    old_value=None,
    new_value=None,
    additional_metadata=None,
    user=None,
):
    """
    Log user activity to the database.

    Args:
        action_type (str): Type of action (e.g., 'login', 'status_change', 'gpa_update')
        target_entity (str): What was affected (e.g., 'applicant', 'rating', 'session')
        target_id (str): Specific ID (e.g., user_code, rating_id)
        old_value (str): Previous value (for changes)
        new_value (str): New value (for changes)
        additional_metadata (dict): Extra info as JSON
        user (object): Optional user object to log. If not provided, uses current_user.
                       Pass the user explicitly for login events before session is established.
    """
    try:
        if user is not None:
            user_id = user.id if hasattr(user, "id") else None
        elif current_user and current_user.is_authenticated:
            user_id = current_user.id
        else:
            user_id = None

        metadata_json = json.dumps(additional_metadata) if additional_metadata else None

        with db_transaction() as (conn, cursor):
            cursor.execute(
                """
                INSERT INTO activity_log
                (user_id, action_type, target_entity, target_id, old_value, new_value,
                 additional_metadata, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    action_type,
                    target_entity,
                    target_id,
                    old_value,
                    new_value,
                    metadata_json,
                    datetime.now(),
                ),
            )
        return True, "Activity logged successfully"
    except Exception as e:
        return False, f"Error logging activity: {str(e)}"


def get_activity_logs(
    limit=50, offset=0, filter_action_type=None, filter_user_search=None, filter_target_id=None
):
    """Get activity logs with optional filtering."""
    try:
        with db_connection() as (conn, cursor):
            where_conditions = []
            params = []

            where_conditions.append("action_type IN ('login', 'status_change', 'clear_all_data')")

            if filter_action_type:
                where_conditions = ["action_type = %s"]
                params = [filter_action_type]

            if filter_target_id:
                where_conditions.append("al.target_id = %s")
                params.append(filter_target_id)

            if filter_user_search:
                where_conditions.append("(u.first_name ILIKE %s OR u.last_name ILIKE %s)")
                search_param = f"%{filter_user_search}%"
                params.extend([search_param, search_param])

            where_clause = (
                " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            )

            query = f"""
                SELECT al.*, u.first_name, u.last_name, u.email, ru.name as role_name
                FROM activity_log al
                LEFT JOIN "user" u ON al.user_id = u.id
                LEFT JOIN role_user ru ON u.role_user_id = ru.id
                {where_clause}
                ORDER BY al.created_at DESC
                LIMIT %s OFFSET %s
            """

            params.extend([limit, offset])
            cursor.execute(query, params)

            logs = []
            for row in cursor.fetchall():
                logs.append(
                    {
                        "id": row["id"],
                        "user_id": row["user_id"],
                        "action_type": row["action_type"],
                        "target_entity": row["target_entity"],
                        "target_id": row["target_id"],
                        "old_value": row["old_value"],
                        "new_value": row["new_value"],
                        "additional_metadata": row["additional_metadata"],
                        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                        "user_name": (
                            f"{row['first_name']} {row['last_name']}"
                            if row.get("first_name") and row.get("last_name")
                            else "Unknown User"
                        ),
                        "user_email": row.get("email"),
                        "user_role": row.get("role_name"),
                    }
                )

        return logs, None
    except Exception as e:
        return [], f"Error fetching activity logs: {str(e)}"
