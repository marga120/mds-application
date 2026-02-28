"""
Status Service — business logic for review status management.
No Flask, no SQL. Calls models.statuses, logs activity.
"""

from models.statuses import (
    get_all_statuses as _get_all_statuses,
    get_all_statuses_admin as _get_all_statuses_admin,
    get_default_status as _get_default_status,
    create_status as _create_status,
    update_status as _update_status,
    delete_status as _delete_status,
)
from utils.activity_logger import log_activity


class StatusService:

    def get_active_statuses(self) -> list:
        """Return active statuses for dropdowns."""
        statuses, error = _get_all_statuses()
        if error:
            raise ValueError(error)
        return statuses or []

    def get_all_statuses(self) -> list:
        """Return all statuses including inactive (admin view)."""
        statuses, error = _get_all_statuses_admin()
        if error:
            raise ValueError(error)
        return statuses or []

    def get_default_status(self) -> dict | None:
        """Return the default status, or None."""
        return _get_default_status()

    def create_status(self, status_name: str, badge_color: str, display_order, user) -> str:
        """Create a new status. Returns success message."""
        if not status_name or not status_name.strip():
            raise ValueError("Status name is required")

        success, message = _create_status(status_name.strip(), badge_color or "gray", display_order)
        if not success:
            raise ValueError(message)

        log_activity(
            action_type="create_status",
            target_entity="status_configuration",
            target_id=status_name,
            additional_metadata={
                "status_name": status_name,
                "badge_color": badge_color,
                "created_by": user.email,
            },
        )
        return message

    def update_status(self, status_id: int, status_name, badge_color, display_order, is_active, user) -> str:
        """Update a status. Returns success message."""
        success, message = _update_status(status_id, status_name, badge_color, display_order, is_active)
        if not success:
            raise ValueError(message)

        log_activity(
            action_type="update_status",
            target_entity="status_configuration",
            target_id=str(status_id),
            additional_metadata={
                "status_id": status_id,
                "updated_by": user.email,
            },
        )
        return message

    def delete_status(self, status_id: int, user) -> str:
        """Delete a status, reassigning applicants to default. Returns message."""
        success, message = _delete_status(status_id)
        if not success:
            raise ValueError(message)

        log_activity(
            action_type="delete_status",
            target_entity="status_configuration",
            target_id=str(status_id),
            additional_metadata={
                "status_id": status_id,
                "deleted_by": user.email,
                "result": message,
            },
        )
        return message

    def reorder_statuses(self, statuses: list, user) -> str:
        """Batch update display_order. Returns success message."""
        if not statuses or not isinstance(statuses, list):
            raise ValueError("statuses array is required")
        for s in statuses:
            if "id" not in s or "display_order" not in s:
                raise ValueError("Each status must have 'id' and 'display_order'")

        # Direct DB call (no dedicated model fn for batch reorder yet)
        from utils.database import get_db_connection
        conn = get_db_connection()
        if not conn:
            raise ValueError("Database connection failed")
        try:
            cursor = conn.cursor()
            for s in statuses:
                cursor.execute(
                    "UPDATE status_configuration SET display_order = %s, updated_at = NOW() WHERE id = %s",
                    (s["display_order"], s["id"]),
                )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            conn.rollback()
            conn.close()
            raise ValueError(f"Database error: {str(e)}")

        log_activity(
            action_type="reorder_statuses",
            target_entity="status_configuration",
            target_id="bulk",
            additional_metadata={
                "count": len(statuses),
                "reordered_by": user.email,
                "status_ids": [s["id"] for s in statuses],
            },
        )
        return "Statuses reordered successfully"
