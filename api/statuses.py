"""
Status Configuration API

REST API endpoints for managing application review statuses. Provides CRUD operations
for the status_configuration table. Admin-only access required for modification endpoints.
Supports GET (list/detail), POST (create), PUT (update), and DELETE operations.
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models.statuses import (
    get_all_statuses,
    get_all_statuses_admin,
    create_status,
    update_status,
    delete_status,
    get_default_status
)
from utils.activity_logger import log_activity

statuses_bp = Blueprint('statuses', __name__)


@statuses_bp.route('/api/statuses', methods=['GET'])
@login_required
def get_statuses_route():
    """
    Get all active review statuses for dropdown population.

    Returns active statuses for use in application status dropdowns throughout
    the application. All authenticated users can access this endpoint.

    @http_method: GET
    @route: /api/statuses
    @auth: Required (all roles)

    @return: JSON response with active statuses list
    @return_type: application/json

    @response_structure:
        {
            "success": true,
            "statuses": [
                {
                    "id": 1,
                    "status_name": "Not Reviewed",
                    "display_order": 1,
                    "badge_color": "gray"
                },
                ...
            ]
        }

    @http_codes:
        200: Success - Returns list of active statuses
        500: Database error

    @example:
        fetch('/api/statuses')
            .then(res => res.json())
            .then(data => console.log(data.statuses));
    """
    statuses, error = get_all_statuses()
    
    if error:
        return jsonify({"success": False, "message": error}), 500
    
    return jsonify({"success": True, "statuses": statuses})


@statuses_bp.route('/api/admin/statuses', methods=['GET'])
@login_required
def get_all_statuses_admin_route():
    """
    Get all review statuses including inactive ones (Admin only).

    Returns complete list of statuses for admin management interface,
    including inactive statuses that are hidden from regular users.

    @http_method: GET
    @route: /api/admin/statuses
    @auth: Required (Admin only)

    @return: JSON response with all statuses
    @return_type: application/json

    @response_structure:
        {
            "success": true,
            "statuses": [
                {
                    "id": 1,
                    "status_name": "Not Reviewed",
                    "display_order": 1,
                    "badge_color": "gray",
                    "is_active": true,
                    "is_default": true,
                    "created_at": "2024-01-01T12:00:00",
                    "updated_at": "2024-01-01T12:00:00"
                },
                ...
            ]
        }

    @http_codes:
        200: Success - Returns all statuses
        403: Access denied - User is not admin
        500: Database error

    @example:
        fetch('/api/admin/statuses', {
            headers: {'Authorization': 'Bearer ' + token}
        }).then(res => res.json());
    """
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied. Admin privileges required."}), 403
    
    statuses, error = get_all_statuses_admin()
    
    if error:
        return jsonify({"success": False, "message": error}), 500
    
    return jsonify({"success": True, "statuses": statuses})


@statuses_bp.route('/api/admin/statuses', methods=['POST'])
@login_required
def create_status_route():
    """
    Create a new review status (Admin only).

    Creates a new status configuration that will be available in status dropdowns.
    Automatically assigns display order if not provided.

    @http_method: POST
    @route: /api/admin/statuses
    @auth: Required (Admin only)

    @request_body:
        {
            "status_name": str (required),
            "badge_color": str (optional, default: "gray"),
            "display_order": int (optional, auto-assigned if not provided)
        }

    @param status_name: Unique name for the new status
    @param_type status_name: str
    @param badge_color: Tailwind color name for badge styling
    @param_type badge_color: str
    @param display_order: Position in dropdown list
    @param_type display_order: int | None

    @return: JSON response with success status
    @return_type: application/json

    @validation:
        - status_name must be unique
        - status_name is required
        - badge_color should be valid Tailwind color

    @activity_log: Logs status creation with metadata

    @response_structure:
        {
            "success": true,
            "message": "Status 'Under Review' created successfully"
        }

    @http_codes:
        200: Status created successfully
        400: Validation error or duplicate name
        403: Access denied - User is not admin

    @example:
        fetch('/api/admin/statuses', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                status_name: 'Under Review',
                badge_color: 'blue'
            })
        }).then(res => res.json());
    """
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied. Admin privileges required."}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Invalid request data"}), 400
    
    status_name = data.get('status_name')
    badge_color = data.get('badge_color', 'gray')
    display_order = data.get('display_order')
    
    if not status_name:
        return jsonify({"success": False, "message": "Status name is required"}), 400
    
    success, message = create_status(status_name, badge_color, display_order)
    
    if not success:
        return jsonify({"success": False, "message": message}), 400
    
    log_activity(
        action_type="create_status",
        target_entity="status_configuration",
        target_id=status_name,
        additional_metadata={
            "status_name": status_name,
            "badge_color": badge_color,
            "created_by": current_user.email
        }
    )
    
    return jsonify({"success": True, "message": message})


@statuses_bp.route('/api/admin/statuses/<int:status_id>', methods=['PUT'])
@login_required
def update_status_route(status_id):
    """
    Update an existing review status (Admin only).

    Updates one or more fields of an existing status configuration.
    Only provided fields are updated.

    @http_method: PUT
    @route: /api/admin/statuses/<status_id>
    @auth: Required (Admin only)

    @path_param status_id: ID of the status to update
    @path_param_type status_id: int

    @request_body (all optional):
        {
            "status_name": str,
            "badge_color": str,
            "display_order": int,
            "is_active": bool
        }

    @param status_name: New name for the status
    @param_type status_name: str | None
    @param badge_color: New Tailwind color name
    @param_type badge_color: str | None
    @param display_order: New position in dropdown
    @param_type display_order: int | None
    @param is_active: Whether status should be visible
    @param_type is_active: bool | None

    @return: JSON response with success status
    @return_type: application/json

    @validation:
        - At least one field must be provided
        - Cannot update is_default flag
        - status_id must exist

    @activity_log: Logs status update with changed fields

    @response_structure:
        {
            "success": true,
            "message": "Status updated successfully"
        }

    @http_codes:
        200: Status updated successfully
        400: Validation error or status not found
        403: Access denied - User is not admin

    @example:
        fetch('/api/admin/statuses/5', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                badge_color: 'green',
                is_active: true
            })
        }).then(res => res.json());
    """
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied. Admin privileges required."}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Invalid request data"}), 400
    
    status_name = data.get('status_name')
    badge_color = data.get('badge_color')
    display_order = data.get('display_order')
    is_active = data.get('is_active')
    
    success, message = update_status(status_id, status_name, badge_color, display_order, is_active)
    
    if not success:
        return jsonify({"success": False, "message": message}), 400
    
    log_activity(
        action_type="update_status",
        target_entity="status_configuration",
        target_id=str(status_id),
        additional_metadata={
            "status_id": status_id,
            "updated_fields": {k: v for k, v in data.items() if v is not None},
            "updated_by": current_user.email
        }
    )
    
    return jsonify({"success": True, "message": message})


@statuses_bp.route('/api/admin/statuses/<int:status_id>', methods=['DELETE'])
@login_required
def delete_status_route(status_id):
    """
    Delete a review status and reassign applicants to default (Admin only).

    Removes a status from the system after reassigning any applicants who have
    that status to the default status. Cannot delete the default status.

    @http_method: DELETE
    @route: /api/admin/statuses/<status_id>
    @auth: Required (Admin only)

    @path_param status_id: ID of the status to delete
    @path_param_type status_id: int

    @return: JSON response with success status and reassignment count
    @return_type: application/json

    @process:
        1. Verify status is not the default
        2. Count affected applicants
        3. Reassign all applicants to default status
        4. Delete the status record

    @validation:
        - Cannot delete default status (is_default = TRUE)
        - status_id must exist

    @activity_log: Logs deletion and applicant reassignments

    @response_structure:
        Success:
        {
            "success": true,
            "message": "Status deleted and 15 applicants reassigned to default"
        }
        
        Error:
        {
            "success": false,
            "message": "Cannot delete the default status"
        }

    @http_codes:
        200: Status deleted successfully
        400: Cannot delete (default status or not found)
        403: Access denied - User is not admin

    @example:
        fetch('/api/admin/statuses/5', {
            method: 'DELETE'
        }).then(res => res.json());
    """
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied. Admin privileges required."}), 403
    
    success, message = delete_status(status_id)
    
    if not success:
        return jsonify({"success": False, "message": message}), 400
    
    log_activity(
        action_type="delete_status",
        target_entity="status_configuration",
        target_id=str(status_id),
        additional_metadata={
            "status_id": status_id,
            "deleted_by": current_user.email,
            "result": message
        }
    )
    
    return jsonify({"success": True, "message": message})


@statuses_bp.route('/api/admin/statuses/reorder', methods=['POST'])
@login_required
def reorder_statuses_route():
    """
    Batch update display_order for multiple statuses (Admin only).
    
    Updates the display_order field for multiple statuses in a single transaction.
    Used for drag-and-drop reordering in the admin interface.
    
    @http_method: POST
    @route: /api/admin/statuses/reorder
    @auth: Required (Admin only)
    
    @body_param statuses: List of {id, display_order} objects
    @body_param_type statuses: list[dict]
    
    @return: JSON response with success status
    @return_type: application/json
    
    @validation:
        - Must be Admin user
        - statuses array required
        - Each status must have 'id' and 'display_order'
    
    @activity_log: Logs bulk reorder operation
    
    @request_structure:
        {
            "statuses": [
                {"id": 1, "display_order": 1},
                {"id": 2, "display_order": 2},
                {"id": 3, "display_order": 3}
            ]
        }
    
    @response_structure:
        Success:
        {
            "success": true,
            "message": "Statuses reordered successfully"
        }
    
    @http_codes:
        200: Statuses reordered successfully
        400: Invalid request data
        403: Access denied (non-Admin)
        500: Database error
    
    @example:
        fetch('/api/admin/statuses/reorder', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                statuses: [{id: 1, display_order: 2}, {id: 2, display_order: 1}]
            })
        }).then(res => res.json());
    """
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied. Admin privileges required."}), 403
    
    data = request.get_json()
    statuses = data.get('statuses', [])
    
    if not statuses or not isinstance(statuses, list):
        return jsonify({"success": False, "message": "statuses array is required"}), 400
    
    for status in statuses:
        if 'id' not in status or 'display_order' not in status:
            return jsonify({"success": False, "message": "Each status must have 'id' and 'display_order'"}), 400
    from utils.database import get_db_connection
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor()
        
        for status in statuses:
            cursor.execute(
                """
                UPDATE status_configuration
                SET display_order = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (status['display_order'], status['id'])
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity(
            action_type="reorder_statuses",
            target_entity="status_configuration",
            target_id="bulk",
            additional_metadata={
                "count": len(statuses),
                "reordered_by": current_user.email,
                "status_ids": [s['id'] for s in statuses]
            }
        )
        
        return jsonify({"success": True, "message": "Statuses reordered successfully"})
        
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
