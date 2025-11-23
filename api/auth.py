from flask import Blueprint, request, jsonify, session, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from models.users import authenticate_user, get_user_by_email, create_user
from datetime import datetime
from utils.activity_logger import log_activity
import bcrypt
from utils.database import get_db_connection
auth_api = Blueprint("auth_api", __name__)


@auth_api.route("/login", methods=["POST"])
def login():
    """
    Handle user authentication and session creation.

    Authenticates users using email and password, creates a session using
    Flask-Login, and logs the activity. Supports optional "remember me" functionality.

    @method: POST
    @param email: User's email address (JSON body)
    @param_type email: str
    @param password: User's password (JSON body)
    @param_type password: str
    @param remember: Whether to remember the session (JSON body, optional)
    @param_type remember: bool

    @return: JSON response with authentication result and user info
    @return_type: flask.Response
    @status_codes:
        - 200: Login successful
        - 400: Missing email or password
        - 401: Invalid credentials
        - 500: Server error

    @logs: Activity logging for successful and failed login attempts
    @session: Creates Flask-Login session

    @example:
        POST /api/auth/login
        Content-Type: application/json

        Request:
        {
            "email": "admin@example.com",
            "password": "password123",
            "remember": true
        }

        Response:
        {
            "success": true,
            "message": "Login successful",
            "user": {
                "id": 1,
                "email": "admin@example.com",
                "full_name": "Admin User",
                "role": "Admin"
            },
            "redirect": "/"
        }
    """

    """Handle user login"""
    try:
        data = request.get_json()
        email = data.get("email", "").strip()
        password = data.get("password", "")
        remember = data.get("remember", False)

        if not email or not password:
            return (
                jsonify(
                    {"success": False, "message": "Email and password are required"}
                ),
                400,
            )

        # Authenticate user
        user = authenticate_user(email, password)

        if user:
            # Log the user in with Flask-Login
            login_user(user, remember=remember)

            log_activity(
                action_type="login", additional_metadata={"remember": remember}
            )

            return jsonify(
                {
                    "success": True,
                    "message": "Login successful",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.full_name,
                        "role": user.role_name,
                    },
                    "redirect": url_for("index"),
                }
            )
        else:
            # Log failed login attempt
            log_activity(
                action_type="login_failed", additional_metadata={"email": email}
            )
            return (
                jsonify({"success": False, "message": "Invalid email or password"}),
                401,
            )

    except Exception as e:
        return jsonify({"success": False, "message": f"Login error: {str(e)}"}), 500


@auth_api.route("/logout", methods=["POST"])
@login_required
def logout():
    """
    Handle user logout and session termination.

    Terminates the current user session using Flask-Login logout functionality.

    @requires: Valid user session
    @method: POST

    @return: JSON response with logout confirmation
    @return_type: flask.Response
    @status_codes:
        - 200: Logout successful
        - 500: Server error

    @session: Destroys Flask-Login session

    @example:
        POST /api/auth/logout

        Response:
        {
            "success": true,
            "message": "Logout successful",
            "redirect": "/login"
        }
    """

    """Handle user logout"""
    try:
        logout_user()
        return jsonify(
            {
                "success": True,
                "message": "Logout successful",
                "redirect": url_for("login_page"),
            }
        )
    except Exception as e:
        return jsonify({"success": False, "message": f"Logout error: {str(e)}"}), 500


@auth_api.route("/user", methods=["GET"])
@login_required
def get_current_user():
    """
    Get information about the currently authenticated user.

    Returns detailed information about the logged-in user including role
    information and permission flags.

    @requires: Valid user session
    @method: GET

    @return: JSON response with current user information
    @return_type: flask.Response
    @status_codes:
        - 200: User information retrieved successfully

    @example:
        GET /api/auth/user

        Response:
        {
            "success": true,
            "user": {
                "id": 1,
                "email": "admin@example.com",
                "full_name": "Admin User",
                "role": "Admin",
                "is_admin": true,
                "is_faculty": false,
                "is_viewer": false
            }
        }
    """

    """Get current logged in user info"""
    return jsonify(
        {
            "success": True,
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "full_name": current_user.full_name,
                "role": current_user.role_name,
                "is_admin": current_user.is_admin,
                "is_faculty": current_user.is_faculty,
                "is_viewer": current_user.is_viewer,
            },
        }
    )


@auth_api.route("/register", methods=["POST"])
def register():
    """
    Handle user registration and account creation.

    Creates new user accounts in the system. Only Admin users can create
    new accounts for security purposes. Validates input data and enforces
    password requirements.

    @requires: Admin authentication
    @method: POST
    @param first_name: User's first name (JSON body)
    @param_type first_name: str
    @param last_name: User's last name (JSON body)
    @param_type last_name: str
    @param email: User's email address (JSON body)
    @param_type email: str
    @param password: User's password (JSON body, min 6 chars)
    @param_type password: str
    @param role_user_id: Role ID (JSON body, optional, defaults to 3=Viewer)
    @param_type role_user_id: int
    @valid_roles: [1=Admin, 2=Faculty, 3=Viewer]

    @return: JSON response with registration result
    @return_type: flask.Response
    @status_codes:
        - 200: User created successfully
        - 400: Invalid input data or email format
        - 403: Access denied (non-Admin user)
        - 500: Server error

    @validation:
        - Email format validation
        - Password minimum 6 characters
        - Valid role ID (1-3)
        - All required fields present

    @security: Password hashed using bcrypt before storage

    @example:
        POST /api/auth/register
        Content-Type: application/json

        Request:
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "password": "password123",
            "role_user_id": 2
        }

        Response:
        {
            "success": true,
            "message": "User created successfully"
        }
    """

    """Handle user registration (Admin only)"""
    if not current_user.is_authenticated or not current_user.is_admin:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Access denied. Admin privileges required.",
                }
            ),
            403,
        )

    try:
        data = request.get_json()
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")
        role_user_id = data.get("role_user_id", 3)  # Default to Viewer role

        if not all([first_name, last_name, email, password]):
            return (
                jsonify({"success": False, "message": "All fields are required"}),
                400,
            )

        # Validate email format (basic)
        if "@" not in email or "." not in email:
            return jsonify({"success": False, "message": "Invalid email format"}), 400

        # Validate password length
        if len(password) < 6:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Password must be at least 6 characters long",
                    }
                ),
                400,
            )

        # Validate role_user_id
        valid_role_ids = [1, 2, 3]  # Admin, Faculty, Viewer
        if role_user_id not in valid_role_ids:
            return jsonify({"success": False, "message": "Invalid role specified"}), 400

        # Create user
        success, message = create_user(
            first_name, last_name, email, password, role_user_id
        )

        if success:
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "message": message}), 400

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Registration error: {str(e)}"}),
            500,
        )


@auth_api.route("/check-session", methods=["GET"])
def check_session():
    """
    Check if the current user has a valid session.

    Verifies if a user is currently logged in and returns authentication
    status along with basic user information if authenticated.

    @method: GET

    @return: JSON response with authentication status
    @return_type: flask.Response
    @status_codes:
        - 200: Session check completed (authenticated or not)

    @example:
        GET /api/auth/check-session

        Response (authenticated):
        {
            "authenticated": true,
            "user": {
                "id": 1,
                "email": "admin@example.com",
                "full_name": "Admin User",
                "role": "Admin"
            }
        }

        Response (not authenticated):
        {
            "authenticated": false
        }
    """

    """Check if user is logged in"""
    if current_user.is_authenticated:
        return jsonify(
            {
                "authenticated": True,
                "user": {
                    "id": current_user.id,
                    "email": current_user.email,
                    "full_name": current_user.full_name,
                    "role": current_user.role_name,
                },
            }
        )
    else:
        return jsonify({"authenticated": False})
@auth_api.route("/reset-password", methods=["POST"])
@login_required
def reset_password():
    """
    Reset authenticated user's password.

    Allows users to change their password by providing their current password
    and a new password. verifies the current password before updating to the
    new password.all password changes are logged for security auditing.

    @requires: Any authenticated user (Admin, Faculty, or Viewer)
    @method: POST
    @param current_password: User's current password for verification (JSON body)
    @param_type current_password: str
    @param new_password: New password to set (JSON body, min 8 chars)
    @param_type new_password: str

    @return: JSON response with password reset result
    @return_type: flask.Response
    @status_codes:
        - 200: Password reset successfully
        - 400: Missing required fields or invalid password length
        - 401: Current password is incorrect
        - 404: User not found in database
        - 500: Database error

    @validation:
        - Both current and new passwords required
        - New password minimum 8 characters
        - Current password must match stored hash

    @security: 
        - Password verified using bcrypt
        - New password hashed with bcrypt and salt before storage
        - Activity logged for audit trail

    @db_tables: user
    @logs: Activity log entry created for password_reset action

    @example:
        POST /api/auth/reset-password
        Content-Type: application/json

        Request:
        {
            "current_password": "oldPassword123",
            "new_password": "newSecurePass456"
        }

        Response:
        {
            "success": true,
            "message": "Password reset successfully"
        }
    """
    data = request.get_json()
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    
    if not current_password or not new_password:
        return jsonify({"success": False, "message": "Missing required fields"}), 400
    
    if len(new_password) < 8:
        return jsonify({"success": False, "message": "Password must be at least 8 characters"}), 400
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get current user's password hash from database
        cursor.execute('SELECT password FROM "user" WHERE id = %s', (current_user.id,))
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "User not found"}), 404
        
        stored_password_hash = result[0]
        
        # Verify current password
        if not bcrypt.checkpw(current_password.encode('utf-8'), stored_password_hash.encode('utf-8')):
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Current password is incorrect"}), 401
        
        # Hash new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update password in database
        cursor.execute(
            'UPDATE "user" SET password = %s, updated_at = %s WHERE id = %s',
            (hashed_password, datetime.now(), current_user.id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        # Log the activity
        log_activity(
            action_type="password_reset",
            target_entity="user",
            target_id=str(current_user.id),
            additional_metadata={"user_email": current_user.email}
        )
        
        return jsonify({"success": True, "message": "Password reset successfully"})
        
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500