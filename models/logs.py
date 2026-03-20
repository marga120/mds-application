"""
Log Model Functions

Database queries for activity log data, joined with applicant information.
"""

from utils.db_helpers import db_connection


def get_status_change_history(session_id, status_filter=None, accepted_filter=None, direction=None):
    """
    Get all instances where an applicant was moved to a given status,
    joined with their current applicant data.

    @param session_id: Session ID to scope results to
    @param status_filter: Optional status name to filter by (e.g. "Offer Sent to Student")
    @param accepted_filter: Optional "accepted" or "not_accepted" to filter by current status
    @return: Tuple of (rows_list, error_message)
    """
    try:
        with db_connection() as (conn, cursor):
            params = [session_id]

            status_clause = ""
            if status_filter:
                if direction == "to":
                    status_clause = "AND al.new_value = %s"
                    params.append(status_filter)
                elif direction == "from":
                    status_clause = "AND al.old_value = %s"
                    params.append(status_filter)
                else:
                    status_clause = "AND (al.new_value = %s OR al.old_value = %s)"
                    params.append(status_filter)
                    params.append(status_filter)

            accepted_clause = ""
            if accepted_filter == "accepted":
                accepted_clause = "AND app.sent = 'Offer Accepted'"
            elif accepted_filter == "not_accepted":
                accepted_clause = "AND app.sent != 'Offer Accepted'"

            query = f"""
                SELECT
                    al.id AS log_id,
                    al.created_at AS status_changed_at,
                    al.new_value AS status_reached,
                    al.old_value AS previous_status,
                    ai.user_code,
                    ai.given_name,
                    ai.family_name,
                    aps.student_number,
                    aps.submit_date,
                    app.sent AS current_status,
                    COALESCE(u.first_name || ' ' || u.last_name, 'Unknown User') AS changed_by
                FROM activity_log al
                JOIN applicant_info ai ON al.target_id = ai.user_code
                JOIN applicant_status aps ON ai.user_code = aps.user_code
                JOIN application_info app ON ai.user_code = app.user_code
                LEFT JOIN "user" u ON al.user_id = u.id
                WHERE al.action_type = 'status_change'
                  AND ai.session_id = %s
                  {status_clause}
                  {accepted_clause}
                ORDER BY al.created_at DESC
            """

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            serialized = []
            for row in rows:
                serialized.append({
                    "log_id": row["log_id"],
                    "status_changed_at": row["status_changed_at"].isoformat() if row["status_changed_at"] else None,
                    "status_reached": row["status_reached"],
                    "previous_status": row["previous_status"],
                    "user_code": row["user_code"],
                    "given_name": row["given_name"],
                    "family_name": row["family_name"],
                    "student_number": row["student_number"],
                    "submit_date": row["submit_date"].isoformat() if row["submit_date"] else None,
                    "current_status": row["current_status"],
                    "changed_by": row["changed_by"],
                })

            return serialized, None

    except Exception as e:
        return None, f"Database error: {str(e)}"
