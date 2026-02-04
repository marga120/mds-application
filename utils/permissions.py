"""
Permission Decorators

This module provides decorators for route-level permission checking,
replacing repetitive permission check patterns throughout the API layer.

Usage:
    from utils.permissions import require_admin, require_faculty_or_admin

    @app.route('/admin-only')
    @require_admin
    def admin_endpoint():
        return jsonify({"success": True})

    @app.route('/faculty-or-admin')
    @require_faculty_or_admin
    def faculty_endpoint():
        return jsonify({"success": True})
"""

from functools import wraps
from flask import jsonify
from flask_login import current_user, login_required


def require_authenticated(f):
    """
    Decorator that ensures user is authenticated.

    Wrapper around flask_login's login_required with consistent JSON response.

    @example:
        @app.route('/protected')
        @require_authenticated
        def protected_endpoint():
            return jsonify({"user": current_user.email})
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function


def require_admin(f):
    """
    Decorator that ensures only Admin users can access the route.

    Returns 403 JSON response if user is not authenticated or not an Admin.

    @example:
        @app.route('/admin/users')
        @require_admin
        def manage_users():
            return jsonify({"users": get_all_users()})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                "success": False,
                "message": "Authentication required"
            }), 401

        if not current_user.is_admin:
            return jsonify({
                "success": False,
                "message": "Admin access required"
            }), 403

        return f(*args, **kwargs)
    return decorated_function


def require_faculty_or_admin(f):
    """
    Decorator that ensures only Admin or Faculty users can access the route.

    Viewers are denied access. Returns 403 JSON response if user lacks permission.

    @example:
        @app.route('/ratings')
        @require_faculty_or_admin
        def submit_rating():
            return jsonify({"success": True})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                "success": False,
                "message": "Authentication required"
            }), 401

        if current_user.is_viewer:
            return jsonify({
                "success": False,
                "message": "Access denied. Faculty or Admin role required."
            }), 403

        return f(*args, **kwargs)
    return decorated_function


def require_not_viewer(f):
    """
    Alias for require_faculty_or_admin for semantic clarity.

    Use when the logic is "anyone except viewers can do this".

    @example:
        @app.route('/export')
        @require_not_viewer
        def export_data():
            return send_file(...)
    """
    return require_faculty_or_admin(f)


def check_permission(required_role):
    """
    Factory function to create permission decorators with custom role checks.

    @param required_role: Role name to check ('Admin', 'Faculty', 'Viewer')
    @return: Decorator function

    @example:
        @app.route('/custom')
        @check_permission('Faculty')
        def faculty_only():
            return jsonify({"success": True})
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({
                    "success": False,
                    "message": "Authentication required"
                }), 401

            user_role = None
            if current_user.is_admin:
                user_role = 'Admin'
            elif current_user.is_faculty:
                user_role = 'Faculty'
            elif current_user.is_viewer:
                user_role = 'Viewer'

            # Admin can access everything
            if user_role == 'Admin':
                return f(*args, **kwargs)

            # Check if user has required role
            role_hierarchy = {'Admin': 3, 'Faculty': 2, 'Viewer': 1}
            required_level = role_hierarchy.get(required_role, 0)
            user_level = role_hierarchy.get(user_role, 0)

            if user_level < required_level:
                return jsonify({
                    "success": False,
                    "message": f"Access denied. {required_role} role or higher required."
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator
