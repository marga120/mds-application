"""
api/auth.py
HTTP layer only. All routes delegate to AuthService.
No SQL. No bcrypt. No business logic.
"""
from flask import Blueprint, request, jsonify, url_for
from flask_login import login_user, logout_user, login_required, current_user
from utils.permissions import require_admin, require_super_admin
from services.auth_service import AuthService

auth_api = Blueprint("auth_api", __name__)
_service = AuthService()


@auth_api.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    remember = data.get("remember", False)

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."}), 400

    try:
        user = _service.authenticate(email, password)
        if user:
            login_user(user, remember=remember)
            return jsonify({
                "success": True,
                "message": "Login successful",
                "user": _service.get_current_user_info(user),
                "redirect": url_for("index"),
            })
        return jsonify({"success": False, "message": "Invalid email or password."}), 401
    except Exception:
        return jsonify({"success": False, "message": "Login error. Please try again."}), 500


@auth_api.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"success": True, "message": "Logged out.", "redirect": url_for("login_page")})


@auth_api.route("/check-session", methods=["GET"])
def check_session():
    if current_user.is_authenticated:
        return jsonify({"authenticated": True, "user": _service.get_current_user_info(current_user)})
    return jsonify({"authenticated": False})


@auth_api.route("/user", methods=["GET"])
@login_required
def get_current_user():
    return jsonify({"success": True, "user": _service.get_current_user_info(current_user)})


@auth_api.route("/users", methods=["GET"])
@login_required
@require_admin
def get_users():
    search = (request.args.get("q") or "").strip()
    try:
        users = _service.get_all_users(search or None)
        return jsonify({"success": True, "users": users})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@auth_api.route("/user/<int:user_id>", methods=["GET"])
@login_required
@require_admin
def get_user_by_id(user_id):
    try:
        user = _service.get_user_by_id(user_id)
        if not user:
            return jsonify({"success": False, "message": "User not found."}), 404
        return jsonify({"success": True, "user": user})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@auth_api.route("/register", methods=["POST"])
@login_required
@require_admin
def register_user():
    data = request.get_json()
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    role_id = data.get("role_user_id", 3)
    campus = (data.get("campus") or "").strip() or None
    program = (data.get("program") or "").strip() or None

    if not all([first_name, last_name, email, password]):
        return jsonify({"success": False, "message": "All fields are required."}), 400
    try:
        user = _service.create_user(
            email, password, first_name, last_name, role_id,
            campus=campus, program=program,
            caller_is_super_admin=current_user.is_super_admin,
        )
        return jsonify({"success": True, "message": "User created successfully.", "user": user})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception:
        return jsonify({"success": False, "message": "An error occurred."}), 500


@auth_api.route("/user/<int:user_id>", methods=["PUT"])
@login_required
@require_admin
def update_user(user_id):
    if current_user.id == user_id:
        return jsonify({"success": False, "message": "Use Account Settings to edit your own account."}), 400

    data = request.get_json()
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    email = (data.get("email") or "").strip()
    role_id = data.get("role_user_id")
    password = data.get("password") or ""
    campus = (data.get("campus") or "").strip() or None
    program = (data.get("program") or "").strip() or None

    if not all([first_name, last_name, email, role_id]):
        return jsonify({"success": False, "message": "First name, last name, email, and role are required."}), 400
    try:
        user = _service.update_user(
            user_id, email, first_name, last_name, role_id, password or None,
            campus=campus, program=program,
            caller_is_super_admin=current_user.is_super_admin,
        )
        return jsonify({"success": True, "message": "User updated successfully.", "user": user})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception:
        return jsonify({"success": False, "message": "An error occurred."}), 500


@auth_api.route("/delete-user/<int:user_id>", methods=["DELETE"], strict_slashes=False)
@login_required
@require_admin
def delete_user(user_id):
    try:
        _service.delete_user(user_id, current_user.id, caller_is_super_admin=current_user.is_super_admin)
        return jsonify({"success": True, "message": "User deleted successfully."})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception:
        return jsonify({"success": False, "message": "An error occurred."}), 500


@auth_api.route("/delete-users", methods=["DELETE"], strict_slashes=False)
@login_required
@require_admin
def delete_users():
    data = request.get_json()
    user_ids = data.get("user_ids", [])
    if not user_ids or not isinstance(user_ids, list):
        return jsonify({"success": False, "message": "Invalid user_ids."}), 400
    try:
        count = _service.delete_users_bulk(user_ids, current_user.id, caller_is_super_admin=current_user.is_super_admin)
        return jsonify({
            "success": True,
            "message": f'Deleted {count} user{"s" if count != 1 else ""}.',
            "deleted_count": count,
        })
    except Exception:
        return jsonify({"success": False, "message": "An error occurred."}), 500


@auth_api.route("/update-email", methods=["POST"])
@login_required
def update_email():
    data = request.get_json()
    new_email = (data.get("new_email") or "").strip()
    password = data.get("password") or ""
    if not new_email or not password:
        return jsonify({"success": False, "message": "Missing required fields."}), 400
    try:
        _service.update_email(current_user.id, new_email, password)
        return jsonify({"success": True, "message": "Email updated successfully."})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception:
        return jsonify({"success": False, "message": "An error occurred."}), 500


@auth_api.route("/reset-password", methods=["POST"])
@login_required
def reset_password():
    data = request.get_json()
    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or ""
    if not current_password or not new_password:
        return jsonify({"success": False, "message": "Missing required fields."}), 400
    try:
        _service.reset_password(current_user.id, current_password, new_password)
        return jsonify({"success": True, "message": "Password changed successfully."})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception:
        return jsonify({"success": False, "message": "An error occurred."}), 500
