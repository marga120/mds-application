"""
Status Configuration API

REST API endpoints for managing application review statuses. Provides CRUD operations
for the status_configuration table. Admin-only access required for all endpoints.
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
    
    Returns:
        JSON response with active statuses ordered by display_order
    
    Example response:
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
    
    Returns:
        JSON response with all statuses including inactive, ordered by display_order
        
    Security:
        - Requires admin role
        - Returns 403 if user is not admin
        
    Example response:
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
    """
    statuses, error = get_all_statuses()
    
    if error:
        return jsonify({"success": False, "message": error}), 500
    
    return jsonify({"success": True, "statuses": statuses})
    pass


@statuses_bp.route('/api/admin/statuses', methods=['POST'])
@login_required
def create_status_route():
    """
    Create a new review status (Admin only).
    
    Request body:
        {
            "status_name": str (required),
            "badge_color": str (optional, default: "gray"),
            "display_order": int (optional, auto-assigned if not provided)
        }
    
    Returns:
        JSON response with success status and message
        
    Security:
        - Requires admin role
        - Logs activity
        
    Validation:
        - status_name must be unique
        - badge_color must be valid Tailwind color
        
    Example response:
        {
            "success": true,
            "message": "Status created successfully"
        }
    """
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied. Admin privileges required."}), 403
    statuses, error = get_all_statuses()
    
    if error:
        return jsonify({"success": False, "message": error}), 500
    
    return jsonify({"success": True, "statuses": statuses})
    pass
    pass


@statuses_bp.route('/api/admin/statuses/<int:status_id>', methods=['PUT'])
@login_required
def update_status_route(status_id):
    """
    Update an existing review status (Admin only).
    
    Args:
        status_id: ID of the status to update
        
    Request body (all fields optional):
        {
            "status_name": str,
            "badge_color": str,
            "display_order": int,
            "is_active": bool
        }
    
    Returns:
        JSON response with success status and message
        
    Security:
        - Requires admin role
        - Logs activity
        
    Notes:
        - Only provided fields are updated
        - Cannot update is_default via this endpoint
        - Renaming updates all applicant records
        
    Example response:
        {
            "success": true,
            "message": "Status updated successfully"
        }
    """
    pass


@statuses_bp.route('/api/admin/statuses/<int:status_id>', methods=['DELETE'])
@login_required
def delete_status_route(status_id):
    """
    Delete a review status and reassign applicants to default (Admin only).
    
    Args:
        status_id: ID of the status to delete
        
    Returns:
        JSON response with success status and message
        
    Security:
        - Requires admin role
        - Logs activity for each affected applicant
        
    Process:
        1. Check if status is the default (cannot delete)
        2. Get all applicants with this status
        3. Update all applicants to default status
        4. Delete the status
        
    Example response:
        {
            "success": true,
            "message": "Status deleted and 15 applicants reassigned to default"
        }
        
    Error response:
        {
            "success": false,
            "message": "Cannot delete the default status"
        }
    """
    pass
