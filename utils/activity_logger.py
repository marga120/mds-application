from utils.database import get_db_connection
from flask_login import current_user
from flask import request
import json
from datetime import datetime


def log_activity(
    action_type,
    target_entity=None,
    target_id=None,
    old_value=None,
    new_value=None,
    additional_metadata=None,
):
    """
    Log user activity to the database

    Args:
        action_type (str): Type of action (e.g., 'login', 'status_change', 'gpa_update')
        target_entity (str): What was affected (e.g., 'applicant', 'rating', 'session')
        target_id (str): Specific ID (e.g., user_code, rating_id)
        old_value (str): Previous value (for changes)
        new_value (str): New value (for changes)
        additional_metadata (dict): Extra info as JSON
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        cursor = conn.cursor()

        # Get user info
        user_id = current_user.id if current_user.is_authenticated else None

        # Convert metadata to JSON if provided
        metadata_json = json.dumps(additional_metadata) if additional_metadata else None

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

        conn.commit()
        cursor.close()
        conn.close()
        return True, "Activity logged successfully"

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return False, f"Error logging activity: {str(e)}"


def get_activity_logs(
    limit=100, offset=0, filter_action_type=None, filter_user_id=None
):
    """Get activity logs with optional filtering"""
    conn = get_db_connection()
    if not conn:
        return [], "Database connection failed"

    try:
        cursor = conn.cursor()

        # Build query with filters
        where_conditions = []
        params = []

        if filter_action_type:
            where_conditions.append("action_type = %s")
            params.append(filter_action_type)

        if filter_user_id:
            where_conditions.append("user_id = %s")
            params.append(filter_user_id)

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
                    "id": row[0],
                    "user_id": row[1],
                    "action_type": row[2],
                    "target_entity": row[3],
                    "target_id": row[4],
                    "old_value": row[5],
                    "new_value": row[6],
                    "additional_metadata": row[7],
                    "created_at": row[8].isoformat() if row[8] else None,
                    "user_name": (
                        f"{row[9]} {row[10]}" if row[9] and row[10] else "Unknown User"
                    ),
                    "user_email": row[11],
                    "user_role": row[12],
                }
            )

        cursor.close()
        conn.close()
        return logs, None

    except Exception as e:
        if conn:
            conn.close()
        return [], f"Error fetching activity logs: {str(e)}"
