"""
Status Configuration Model

Handles CRUD operations for the dynamic review status configuration system.
Statuses are stored in the status_configuration table and used for application review workflow.
"""

from utils.database import get_db_connection
from psycopg2.extras import RealDictCursor
import pandas as pd
from datetime import datetime


def get_all_statuses():
    """
    Get all active review statuses for use in dropdowns.

    Retrieves only active statuses from the status_configuration table,
    ordered by display_order for consistent dropdown rendering across the application.

    @return: Tuple of (statuses list, error message)
    @return_type: tuple[list[dict] | None, str | None]

    @return_structure:
        statuses list contains dicts with:
        - id: Status ID
        - status_name: Display name of the status
        - display_order: Order for dropdowns
        - badge_color: Tailwind color name (e.g., 'green', 'red')
        - is_active: Always TRUE (filtered)
        - is_default: Whether this is the default status
        - created_at: Creation timestamp
        - updated_at: Last update timestamp

    @db_tables: status_configuration
    @filters: WHERE is_active = TRUE
    @order: display_order ASC

    @example:
        statuses, error = get_all_statuses()
        if error:
            print(f"Error: {error}")
        else:
            for status in statuses:
                print(f"{status['status_name']} - {status['badge_color']}")
    """
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
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
        statuses = cursor.fetchall()
        cursor.close()
        conn.close()

        return statuses, None 

    except Exception as e:
        if conn:
            conn.close()
        return None, f"Database error: {str(e)}"


def get_all_statuses_admin():
    """
    Get all review statuses including inactive ones for admin management.

    Retrieves ALL statuses from the status_configuration table regardless of active status,
    used by admin interface for status configuration management.

    @return: Tuple of (statuses list, error message)
    @return_type: tuple[list[dict] | None, str | None]

    @return_structure:
        statuses list contains dicts with:
        - id: Status ID
        - status_name: Display name of the status
        - display_order: Order for dropdowns
        - badge_color: Tailwind color name
        - is_active: Whether status is currently active
        - is_default: Whether this is the default status
        - created_at: Creation timestamp
        - updated_at: Last update timestamp

    @db_tables: status_configuration
    @filters: None (returns all)
    @order: display_order ASC

    @example:
        statuses, error = get_all_statuses_admin()
        if not error:
            active = [s for s in statuses if s['is_active']]
            inactive = [s for s in statuses if not s['is_active']]
    """
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
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
        statuses = cursor.fetchall()
        cursor.close()
        conn.close()

        return statuses, None

    except Exception as e:
        if conn:
            conn.close()
        return None, f"Database error: {str(e)}"


def create_status(status_name, badge_color='gray', display_order=None):
    """
    Create a new review status.

    Inserts a new status into the status_configuration table with automatic
    display_order assignment if not provided.

    @param status_name: Name of the new status (must be unique)
    @param_type status_name: str
    @param badge_color: Tailwind color name for badge styling
    @param_type badge_color: str
    @param display_order: Position in dropdown list, auto-assigned if None
    @param_type display_order: int | None

    @return: Tuple of (success status, message)
    @return_type: tuple[bool, str]

    @validation:
        - status_name must be unique (enforced by DB constraint)
        - If display_order is None, sets to max(display_order) + 1
        - New statuses are active by default (is_active = TRUE)
        - is_default is always FALSE for new statuses

    @db_tables: status_configuration
    @inserts: Single row with provided values

    @example:
        success, msg = create_status("Under Review", "blue", 5)
        success, msg = create_status("Pending Decision", "yellow")
        if success:
            print(f"Status created: {msg}")
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    
    try:
        cursor = conn.cursor()
        
        if display_order is None:
            cursor.execute("SELECT COALESCE(MAX(display_order), 0) + 1 FROM status_configuration")
            display_order = cursor.fetchone()[0]
        
        cursor.execute(
            """
            INSERT INTO status_configuration (status_name, display_order, badge_color, is_active, is_default)
            VALUES (%s, %s, %s, TRUE, FALSE)
            """,
            (status_name, display_order, badge_color)
        )
        
        conn.commit()
        cursor.close()
        conn.close()

        return True, f"Status '{status_name}' created successfully"

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return False, f"Database error: {str(e)}"


def update_status(status_id, status_name=None, badge_color=None, display_order=None, is_active=None):
    """
    Update an existing review status.

    Updates only the provided fields for a status record, automatically
    updating the updated_at timestamp.

    @param status_id: ID of the status to update
    @param_type status_id: int
    @param status_name: New name for the status
    @param_type status_name: str | None
    @param badge_color: New Tailwind color name
    @param_type badge_color: str | None
    @param display_order: New position in dropdown
    @param_type display_order: int | None
    @param is_active: Whether status should be active
    @param_type is_active: bool | None

    @return: Tuple of (success status, message)
    @return_type: tuple[bool, str]

    @validation:
        - Only updates fields that are provided (not None)
        - Cannot update is_default via this function
        - At least one field must be provided for update

    @db_tables: status_configuration
    @updates: Single row matching status_id

    @example:
        success, msg = update_status(1, status_name="Reviewed")
        success, msg = update_status(2, badge_color="green", is_active=True)
        success, msg = update_status(3, display_order=10)
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    
    try:
        cursor = conn.cursor()
        
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
            conn.close()
            return False, f"Status with ID {status_id} not found"
        
        conn.commit()
        cursor.close()
        conn.close()

        return True, f"Status updated successfully"

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return False, f"Database error: {str(e)}"


def delete_status(status_id):
    """
    Delete a review status and reassign all applicants to default status.

    Removes a status from the system after reassigning any applicants who have
    that status to the default status.

    @param status_id: ID of the status to delete
    @param_type status_id: int

    @return: Tuple of (success status, message with count of reassigned applicants)
    @return_type: tuple[bool, str]

    @process:
        1. Check if status is the default (cannot delete)
        2. Get the default status name
        3. Count applicants with this status
        4. Update all applicants to default status
        5. Delete the status record

    @validation:
        - Cannot delete the default status (is_default = TRUE)
        - Auto-reassigns applicants to prevent orphaned records

    @db_tables: status_configuration, application_info
    @deletes: Single row from status_configuration
    @updates: Multiple rows in application_info (if applicants exist)

    @example:
        success, msg = delete_status(5)
        if success:
            print(msg)  # "Status deleted and 15 applicants reassigned to default"
        else:
            print(f"Error: {msg}")
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT is_default, status_name FROM status_configuration WHERE id = %s", (status_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return False, f"Status with ID {status_id} not found"
        
        is_default, status_name = result
        
        if is_default:
            conn.close()
            return False, "Cannot delete the default status"
        
        default_status = get_default_status()
        if not default_status:
            conn.close()
            return False, "Default status not found in system"
        
        cursor.execute("SELECT COUNT(*) FROM application_info WHERE sent = %s", (status_name,))
        affected_count = cursor.fetchone()[0]
        
        if affected_count > 0:
            cursor.execute(
                "UPDATE application_info SET sent = %s WHERE sent = %s",
                (default_status['status_name'], status_name)
            )
        
        cursor.execute("DELETE FROM status_configuration WHERE id = %s", (status_id,))
        
        conn.commit()
        cursor.close()
        conn.close()

        if affected_count > 0:
            return True, f"Status deleted and {affected_count} applicants reassigned to default"
        else:
            return True, "Status deleted successfully"

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return False, f"Database error: {str(e)}"


def get_default_status():
    """
    Get the default review status for reassignment operations.

    Retrieves the status marked as default (is_default = TRUE), used when
    deleting other statuses or resetting applicant status.

    @return: Default status dict or None if not found
    @return_type: dict | None

    @return_structure:
        status dict contains:
        - id: Status ID
        - status_name: Display name (typically "Not Reviewed")
        - display_order: Order position
        - badge_color: Color for badge
        - is_active: Active status
        - is_default: Always TRUE
        - created_at: Creation timestamp
        - updated_at: Last update timestamp

    @db_tables: status_configuration
    @filters: WHERE is_default = TRUE
    @limit: LIMIT 1

    @example:
        default = get_default_status()
        if default:
            print(f"Default status: {default['status_name']}")
        else:
            print("No default status configured!")
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
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
        status = cursor.fetchone()
        cursor.close()
        conn.close()

        return status

    except Exception as e:
        if conn:
            conn.close()
        return None
