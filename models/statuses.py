"""
Status Configuration Model

Handles CRUD operations for the dynamic review status configuration system.
Statuses are stored in the status_configuration table and used for application review workflow.
"""

from utils.db_helpers import db_connection, db_transaction


def get_all_statuses():
    """
    Get all active review statuses for use in dropdowns.

    Retrieves only active statuses from the status_configuration table,
    ordered by display_order for consistent dropdown rendering across the application.

    @return: Tuple of (statuses list, error message)
    @return_type: tuple[list[dict] | None, str | None]

    @db_tables: status_configuration
    @filters: WHERE is_active = TRUE
    @order: display_order ASC
    """
    try:
        with db_connection() as (conn, cursor):
            cursor.execute(
                """
                SELECT
                    s.id,
                    s.status_name,
                    s.display_order,
                    s.badge_color,
                    s.is_active,
                    s.is_default,
                    s.created_at,
                    s.updated_at
                FROM status_configuration AS s
                WHERE s.is_active = TRUE
                ORDER BY s.display_order ASC
                """
            )
            return cursor.fetchall(), None
    except Exception as e:
        return None, f"Database error: {str(e)}"


def get_all_statuses_admin():
    """
    Get all review statuses including inactive ones for admin management.

    Retrieves ALL statuses from the status_configuration table regardless of active status,
    used by admin interface for status configuration management.

    @return: Tuple of (statuses list, error message)
    @return_type: tuple[list[dict] | None, str | None]

    @db_tables: status_configuration
    @filters: None (returns all)
    @order: display_order ASC
    """
    try:
        with db_connection() as (conn, cursor):
            cursor.execute(
                """
                SELECT
                    id,
                    status_name,
                    display_order,
                    badge_color,
                    is_active,
                    is_default,
                    created_at,
                    updated_at
                FROM status_configuration
                ORDER BY display_order ASC
                """
            )
            return cursor.fetchall(), None
    except Exception as e:
        return None, f"Database error: {str(e)}"


def create_status(status_name, badge_color='gray', display_order=None):
    """
    Create a new review status.

    @param status_name: Name of the new status (must be unique)
    @param badge_color: Tailwind color name for badge styling
    @param display_order: Position in dropdown list, auto-assigned if None

    @return: Tuple of (success status, message)
    @return_type: tuple[bool, str]

    @db_tables: status_configuration
    """
    try:
        with db_transaction() as (conn, cursor):
            if display_order is None:
                cursor.execute(
                    "SELECT COALESCE(MAX(display_order), 0) + 1 AS next_order FROM status_configuration"
                )
                display_order = cursor.fetchone()["next_order"]

            cursor.execute(
                """
                INSERT INTO status_configuration (status_name, display_order, badge_color, is_active, is_default)
                VALUES (%s, %s, %s, TRUE, FALSE)
                """,
                (status_name, display_order, badge_color),
            )
        return True, f"Status '{status_name}' created successfully"
    except Exception as e:
        return False, f"Database error: {str(e)}"


def update_status(status_id, status_name=None, badge_color=None, display_order=None, is_active=None):
    """
    Update an existing review status.

    Updates only the provided fields. If status_name is changed, also updates
    all applicants who have that status to use the new name.

    @param status_id: ID of the status to update
    @param status_name: New name for the status
    @param badge_color: New Tailwind color name
    @param display_order: New position in dropdown
    @param is_active: Whether status should be active

    @return: Tuple of (success status, message)
    @return_type: tuple[bool, str]

    @db_tables: status_configuration, application_info
    """
    try:
        with db_transaction() as (conn, cursor):
            # If renaming, get the old name first to update applicants
            old_status_name = None
            if status_name is not None:
                cursor.execute(
                    "SELECT status_name FROM status_configuration WHERE id = %s",
                    (status_id,),
                )
                result = cursor.fetchone()
                if result:
                    old_status_name = result["status_name"]

            updates = []
            params = []

            if status_name is not None:
                updates.append("status_name = %s")
                params.append(status_name)
            if badge_color is not None:
                updates.append("badge_color = %s")
                params.append(badge_color)
            if display_order is not None:
                updates.append("display_order = %s")
                params.append(display_order)
            if is_active is not None:
                updates.append("is_active = %s")
                params.append(is_active)

            if not updates:
                return False, "No fields provided for update"

            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(status_id)

            query = f"""
                UPDATE status_configuration
                SET {', '.join(updates)}
                WHERE id = %s
            """
            cursor.execute(query, params)

            if cursor.rowcount == 0:
                return False, f"Status with ID {status_id} not found"

            # If status name changed, cascade to applicants
            applicants_updated = 0
            if old_status_name and status_name and old_status_name != status_name:
                cursor.execute(
                    "UPDATE application_info SET sent = %s WHERE sent = %s",
                    (status_name, old_status_name),
                )
                applicants_updated = cursor.rowcount

        if applicants_updated > 0:
            return True, f"Status updated successfully and {applicants_updated} applicant(s) updated to new status name"
        return True, "Status updated successfully"
    except Exception as e:
        return False, f"Database error: {str(e)}"


def delete_status(status_id):
    """
    Delete a review status and reassign all applicants to default status.

    @param status_id: ID of the status to delete

    @return: Tuple of (success status, message with count of reassigned applicants)
    @return_type: tuple[bool, str]

    @process:
        1. Check if status is the default (cannot delete)
        2. Get the default status name in the same transaction
        3. Count and reassign applicants with this status
        4. Delete the status record

    @db_tables: status_configuration, application_info
    """
    try:
        affected_count = 0
        with db_transaction() as (conn, cursor):
            cursor.execute(
                "SELECT is_default, status_name FROM status_configuration WHERE id = %s",
                (status_id,),
            )
            result = cursor.fetchone()

            if not result:
                return False, f"Status with ID {status_id} not found"
            if result["is_default"]:
                return False, "Cannot delete the default status"

            status_name = result["status_name"]

            cursor.execute(
                "SELECT status_name FROM status_configuration WHERE is_default = TRUE LIMIT 1"
            )
            default_row = cursor.fetchone()
            if not default_row:
                return False, "Default status not found in system"

            default_name = default_row["status_name"]

            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM application_info WHERE sent = %s",
                (status_name,),
            )
            affected_count = cursor.fetchone()["cnt"]

            if affected_count > 0:
                cursor.execute(
                    "UPDATE application_info SET sent = %s WHERE sent = %s",
                    (default_name, status_name),
                )

            cursor.execute("DELETE FROM status_configuration WHERE id = %s", (status_id,))

        if affected_count > 0:
            return True, f"Status deleted and {affected_count} applicants reassigned to default"
        return True, "Status deleted successfully"
    except Exception as e:
        return False, f"Database error: {str(e)}"


def get_default_status():
    """
    Get the default review status for reassignment operations.

    @return: Default status dict or None if not found
    @return_type: dict | None

    @db_tables: status_configuration
    @filters: WHERE is_default = TRUE
    """
    try:
        with db_connection() as (conn, cursor):
            cursor.execute(
                """
                SELECT
                    id,
                    status_name,
                    display_order,
                    badge_color,
                    is_active,
                    is_default,
                    created_at,
                    updated_at
                FROM status_configuration
                WHERE is_default = TRUE
                LIMIT 1
                """
            )
            return cursor.fetchone()
    except Exception:
        return None


def reorder_statuses(statuses):
    """
    Batch update display_order for multiple statuses.

    @param statuses: List of dicts with 'id' and 'display_order' keys
    @param_type statuses: list[dict]

    @return: Tuple of (success, message)
    @return_type: tuple[bool, str]

    @db_tables: status_configuration
    """
    try:
        with db_transaction() as (conn, cursor):
            for s in statuses:
                cursor.execute(
                    "UPDATE status_configuration SET display_order = %s, updated_at = NOW() WHERE id = %s",
                    (s["display_order"], s["id"]),
                )
        return True, "Statuses reordered successfully"
    except Exception as e:
        return False, f"Database error: {str(e)}"
