from flask import Blueprint, request, jsonify, session, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from models.users import authenticate_user, get_user_by_email, create_user
from datetime import datetime
from utils.activity_logger import log_activity

auth_api = Blueprint("auth_api", __name__)


@auth_api.route("/login", methods=["POST"])
def login():
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
    """Handle user registration (Admin only)"""
    # SECURITY FIX: Add authorization check
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
