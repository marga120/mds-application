"""
Log Service — thin wrapper for activity log queries.
No Flask, no SQL. Delegates to utils.activity_logger and utils.db_helpers.
"""

from utils.activity_logger import get_activity_logs
from utils.db_helpers import fetch_all


class LogService:

    def get_logs(self, limit: int = 50, offset: int = 0, action_type=None, user_search=None, target_id=None) -> list:
        """Return activity logs with optional filters."""
        limit = min(limit, 50)
        logs, error = get_activity_logs(
            limit=limit,
            offset=offset,
            filter_action_type=action_type,
            filter_user_search=user_search,
            filter_target_id=target_id,
        )
        if error:
            raise ValueError(error)
        return logs or []

    def export_status_changes(self, user_ids: list | None = None) -> list:
        """Return status change log rows formatted for CSV export."""
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
        return export_rows
