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
    
    Returns:
        tuple: (list of status dicts, error_message)
            Each status dict contains:
            - id: int - Status ID
            - status_name: str - Display name of the status
            - display_order: int - Order for dropdowns
            - badge_color: str - Tailwind color name (e.g., 'green', 'red')
            
    Notes:
        - Only returns statuses where is_active = TRUE
        - Ordered by display_order ASC
        - Used by frontend to populate status dropdowns
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
    
    Returns:
        tuple: (list of status dicts, error_message)
            Each status dict contains:
            - id: int - Status ID
            - status_name: str - Display name of the status
            - display_order: int - Order for dropdowns
            - badge_color: str - Tailwind color name
            - is_active: bool - Whether status is currently active
            - is_default: bool - Whether this is the default status
            - created_at: datetime - Creation timestamp
            - updated_at: datetime - Last update timestamp
            
    Notes:
        - Returns ALL statuses regardless of is_active
        - Ordered by display_order ASC
        - Used by admin UI for status management
    """
    pass


def create_status(status_name, badge_color='gray', display_order=None):
    """
    Create a new review status.
    
    Args:
        status_name (str): Name of the new status (must be unique)
        badge_color (str, optional): Tailwind color name. Defaults to 'gray'
        display_order (int, optional): Position in dropdown. If None, appends to end
        
    Returns:
        tuple: (success: bool, message: str)
        
    Notes:
        - Status name must be unique (enforced by DB constraint)
        - If display_order is None, sets to max(display_order) + 1
        - New statuses are active by default (is_active = TRUE)
        - is_default is always FALSE for new statuses
    """
    pass


def update_status(status_id, status_name=None, badge_color=None, display_order=None, is_active=None):
    """
    Update an existing review status.
    
    Args:
        status_id (int): ID of the status to update
        status_name (str, optional): New name for the status
        badge_color (str, optional): New Tailwind color name
        display_order (int, optional): New position in dropdown
        is_active (bool, optional): Whether status should be active
        
    Returns:
        tuple: (success: bool, message: str)
        
    Notes:
        - Only updates fields that are provided (not None)
        - Cannot update is_default via this function
        - Renaming updates all existing applicants with this status
        - Sets updated_at to current timestamp
    """
    pass


def delete_status(status_id):
    """
    Delete a review status and reassign all applicants to default status.
    
    Args:
        status_id (int): ID of the status to delete
        
    Returns:
        tuple: (success: bool, message: str)
        
    Process:
        1. Get the default status (is_default = TRUE)
        2. Update all applicants with this status to default status
        3. Delete the status from status_configuration table
        
    Notes:
        - Cannot delete the default status
        - Auto-reassigns applicants to prevent orphaned records
        - Deletion is permanent (not a soft delete)
        - Logs activity for each applicant status change
    """
    pass


def get_default_status():
    """
    Get the default review status (used when deleting other statuses).
    
    Returns:
        dict or None: Default status dict with all fields, or None if not found
        
    Notes:
        - Returns the status where is_default = TRUE
        - Should always return 'Not Reviewed' from seed data
        - If multiple defaults exist, returns the first one
    """
    pass

