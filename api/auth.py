from flask import Blueprint, request, jsonify, session, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from models.users import authenticate_user, get_user_by_email
from datetime import datetime
from utils.activity_logger import log_activity
import bcrypt
from utils.database import get_db_connection

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
            return jsonify({"success": False, "message": "Email and password are required"}), 400

        # Authenticate user
        user = authenticate_user(email, password)

        if user:
            login_user(user, remember=remember)
            
            log_activity(
                action_type="login", 
                additional_metadata={"remember": remember}
            )

            return jsonify({
                "success": True,
                "message": "Login successful",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role_name,
                    "role_id": user.role_user_id # Added for frontend logic
                },
                "redirect": url_for("index"),
            })
        else:
            log_activity(
                action_type="login_failed", 
                additional_metadata={"email": email}
            )
            return jsonify({"success": False, "message": "Invalid email or password"}), 401

    except Exception as e:
        return jsonify({"success": False, "message": f"Login error: {str(e)}"}), 500


@auth_api.route("/logout", methods=["POST"])
@login_required
def logout():
    """Handle user logout"""
    try:
        logout_user()
        return jsonify({
            "success": True,
            "message": "Logout successful",
            "redirect": url_for("login_page"),
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Logout error: {str(e)}"}), 500


@auth_api.route("/user", methods=["GET"])
@login_required
def get_current_user():
    """Get current logged in user info"""
    return jsonify({
        "success": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role_name,
            "role_id": current_user.role_user_id, # Crucial for Frontend Admin checks
            "is_admin": current_user.is_admin,
            "is_faculty": current_user.is_faculty,
            "is_viewer": current_user.is_viewer,
        },
    })


@auth_api.route("/users", methods=["GET"])
@login_required
def get_users():
    """
    Get users with optional search.
    @requires: Admin (role_user_id == 1)
    """
    if current_user.role_user_id != 1: 
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    search_query = request.args.get('q', '').strip()
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Base query
        # We use CONCAT to allow searching "John Doe" (Space handling)
        sql = '''
            SELECT id, first_name, last_name, email, role_user_id, created_at 
            FROM "user"
        '''
        params = []

        if search_query:
            # Search against full name (combined) OR email
            sql += ''' 
                WHERE CONCAT(first_name, ' ', last_name) ILIKE %s 
                OR email ILIKE %s 
            '''
            term = f"%{search_query}%"
            params = [term, term]
        
        sql += ' ORDER BY created_at DESC LIMIT 50'

        cursor.execute(sql, tuple(params))
        users = cursor.fetchall()
        
        user_list = []
        for u in users:
            user_list.append({
                "id": u[0],
                "full_name": f"{u[1]} {u[2]}",
                "email": u[3],
                "role_id": u[4],
                "created_at": u[5].isoformat() if u[5] else None
            })
            
        cursor.close()
        conn.close()
        return jsonify({"success": True, "users": user_list})
    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "message": str(e)}), 500

@auth_api.route("/create-user", methods=["POST"])
@login_required
def create_user():
    """
    Create a new user.
    @requires: Admin (role_user_id == 1)
    """
    if current_user.role_user_id != 1:
        return jsonify({"success": False, "message": "Unauthorized access"}), 403

    data = request.get_json()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    role_id = data.get('role_user_id', 3) 

    if not all([first_name, last_name, email, password]):
        return jsonify({"success": False, "message": "All fields are required"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if email exists
        cursor.execute('SELECT id FROM "user" WHERE email = %s', (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Email already exists"}), 400

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        cursor.execute(
            'INSERT INTO "user" (first_name, last_name, email, password, role_user_id, created_at) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id',
            (first_name, last_name, email, hashed, role_id, datetime.now())
        )
        new_id = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()

        log_activity(
            action_type="user_created",
            target_entity="user",
            target_id=str(new_id),
            additional_metadata={"created_by": current_user.email}
        )

        return jsonify({"success": True, "message": "User created successfully"})
    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "message": str(e)}), 500

@auth_api.route("/delete-user/<int:user_id>", methods=["DELETE"],strict_slashes=False)
@login_required
def delete_user(user_id):
    """
    Delete a specific user by ID.
    @requires: Admin (role_user_id == 1)
    """
    if current_user.role_user_id != 1:
        return jsonify({"success": False, "message": "Unauthorized access"}), 403

    if user_id == current_user.id:
        return jsonify({"success": False, "message": "You cannot delete your own account"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # First check if user exists
        cursor.execute('SELECT id FROM "user" WHERE id = %s', (user_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "User not found"}), 404

        # Log activity BEFORE deletion (while user still exists)
        log_activity(
            action_type="user_deleted",
            target_entity="user",
            target_id=str(user_id),
            additional_metadata={"deleted_by": current_user.email}
        )

        # Delete all related data first to avoid foreign key violations
        # 1. Delete ratings created by this user
        cursor.execute('DELETE FROM ratings WHERE user_id = %s', (user_id,))

        # 2. Set activity_log user_id to NULL (preserve audit trail)
        cursor.execute('UPDATE activity_log SET user_id = NULL WHERE user_id = %s', (user_id,))

        # 3. Now safe to delete the user
        cursor.execute('DELETE FROM "user" WHERE id = %s', (user_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "User deleted successfully"})
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@auth_api.route("/delete-users", methods=["DELETE"], strict_slashes=False)
@login_required
def delete_users():
    """
    Delete multiple users by their IDs.
    @requires: Admin (role_user_id == 1)
    @param: user_ids - List of user IDs to delete
    """
    if current_user.role_user_id != 1:
        return jsonify({"success": False, "message": "Unauthorized access"}), 403

    data = request.get_json()
    user_ids = data.get("user_ids", [])

    if not user_ids or not isinstance(user_ids, list):
        return jsonify({"success": False, "message": "Invalid user_ids parameter"}), 400

    # Remove current user from the list if present
    user_ids = [uid for uid in user_ids if uid != current_user.id]

    if not user_ids:
        return jsonify({"success": False, "message": "No valid users to delete"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        deleted_count = 0

        for user_id in user_ids:
            # Check if user exists
            cursor.execute('SELECT id FROM "user" WHERE id = %s', (user_id,))
            if not cursor.fetchone():
                continue  # Skip non-existent users

            # Log activity BEFORE deletion
            log_activity(
                action_type="user_deleted",
                target_entity="user",
                target_id=str(user_id),
                additional_metadata={"deleted_by": current_user.email, "bulk_delete": True}
            )

            # Delete related data
            cursor.execute('DELETE FROM ratings WHERE user_id = %s', (user_id,))
            cursor.execute('UPDATE activity_log SET user_id = NULL WHERE user_id = %s', (user_id,))
            cursor.execute('DELETE FROM "user" WHERE id = %s', (user_id,))

            deleted_count += 1

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": f"Successfully deleted {deleted_count} user{'s' if deleted_count != 1 else ''}",
            "deleted_count": deleted_count
        })
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

#ACCOUNT SETTINGS ROUTES

@auth_api.route("/update-email", methods=["POST"])
@login_required
def update_email():
    """Update user email address"""
    data = request.get_json()
    new_email = data.get("new_email")
    password = data.get("password")
    
    if not new_email or not password:
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Verify password
        cursor.execute('SELECT password FROM "user" WHERE id = %s', (current_user.id,))
        result = cursor.fetchone()
        
        if not result or not bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Incorrect password"}), 401
            
        # Check if email taken
        cursor.execute('SELECT id FROM "user" WHERE email = %s AND id != %s', (new_email, current_user.id))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Email already in use"}), 400

        cursor.execute(
            'UPDATE "user" SET email = %s, updated_at = %s WHERE id = %s',
            (new_email, datetime.now(), current_user.id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Email updated successfully"})
    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "message": str(e)}), 500

@auth_api.route("/edit-user", methods=["POST"])
@login_required
def edit_user():
    """
    Edit a user's email and/or password.
    @requires: Admin (role_user_id == 1)
    """
    if current_user.role_user_id != 1:
        return jsonify({"success": False, "message": "Unauthorized access"}), 403

    data = request.get_json()
    user_id = data.get("user_id")
    new_email = data.get("email")
    new_password = data.get("password")

    if not user_id:
        return jsonify({"success": False, "message": "user_id is required"}), 400

    if not new_email and not new_password:
        return jsonify({"success": False, "message": "At least one field (email or password) must be provided"}), 400

    if new_password and len(new_password) < 8:
        return jsonify({"success": False, "message": "Password must be at least 8 characters"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute('SELECT id FROM "user" WHERE id = %s', (user_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "User not found"}), 404

        # Check if new email is already in use (if provided)
        if new_email:
            cursor.execute('SELECT id FROM "user" WHERE email = %s AND id != %s', (new_email, user_id))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({"success": False, "message": "Email already in use"}), 400

        # Build update query
        updates = []
        params = []

        if new_email:
            updates.append('email = %s')
            params.append(new_email)

        if new_password:
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            updates.append('password = %s')
            params.append(hashed_password)

        updates.append('updated_at = %s')
        params.append(datetime.now())
        params.append(user_id)

        sql = f'UPDATE "user" SET {", ".join(updates)} WHERE id = %s'
        cursor.execute(sql, tuple(params))
        conn.commit()
        cursor.close()
        conn.close()

        log_activity(
            action_type="user_edited",
            target_entity="user",
            target_id=str(user_id),
            additional_metadata={"edited_by": current_user.email, "fields": list(updates)}
        )

        return jsonify({"success": True, "message": "User updated successfully"})
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({"success": False, "message": str(e)}), 500

@auth_api.route("/reset-password", methods=["POST"])
@login_required
def reset_password():
    """Reset authenticated user's password."""
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
        
        cursor.execute('SELECT password FROM "user" WHERE id = %s', (current_user.id,))
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "User not found"}), 404
        
        stored_password_hash = result[0]
        
        if not bcrypt.checkpw(current_password.encode('utf-8'), stored_password_hash.encode('utf-8')):
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Current password is incorrect"}), 401
        
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute(
            'UPDATE "user" SET password = %s, updated_at = %s WHERE id = %s',
            (hashed_password, datetime.now(), current_user.id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity(
            action_type="password_reset",
            target_entity="user",
            target_id=str(current_user.id),
            additional_metadata={"user_email": current_user.email}
        )
        
        return jsonify({"success": True, "message": "Password reset successfully"})
        
    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "message": str(e)}), 500

@auth_api.route("/check-session", methods=["GET"])
def check_session():
    """Check if user is logged in"""
    if current_user.is_authenticated:
        return jsonify({
            "authenticated": True,
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "full_name": current_user.full_name,
                "role": current_user.role_name,
                "role_id": current_user.role_user_id
            },
        })
    else:
        return jsonify({"authenticated": False})

# For grabbing users for editing.

@auth_api.route("/user/<int:user_id>", methods=["GET"])
@login_required
def get_user_by_id(user_id):
    """Get a single user by ID for editing - Admin only"""
    if current_user.role_user_id != 1:
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.first_name, u.last_name, u.email, u.role_user_id, u.created_at, r.name
            FROM "user" u
            JOIN role_user r ON u.role_user_id = r.id
            WHERE u.id = %s
        ''', (user_id,))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        return jsonify({
            "success": True,
            "user": {
                "id": user[0],
                "first_name": user[1],
                "last_name": user[2],
                "email": user[3],
                "role_user_id": user[4],
                "created_at": user[5].isoformat() if user[5] else None,
                "role": user[6]
            }
        })
    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "message": str(e)}), 500


@auth_api.route("/register", methods=["POST"])
@login_required
def register_user():
    """Create a new user - Admin only (uses /register endpoint for users.js)"""
    if current_user.role_user_id != 1:
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    data = request.get_json()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    role_id = data.get('role_user_id', 3)

    if not all([first_name, last_name, email, password]):
        return jsonify({"success": False, "message": "All fields are required"}), 400

    if len(password) < 8:
        return jsonify({"success": False, "message": "Password must be at least 8 characters"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM "user" WHERE email = %s', (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Email already exists"}), 400

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        cursor.execute(
            'INSERT INTO "user" (first_name, last_name, email, password, role_user_id, created_at) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id',
            (first_name, last_name, email, hashed, role_id, datetime.now())
        )
        new_id = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()

        log_activity(
            action_type="user_created",
            target_entity="user",
            target_id=str(new_id),
            additional_metadata={"created_by": current_user.email}
        )

        return jsonify({"success": True, "message": "User created successfully"})
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({"success": False, "message": str(e)}), 500


@auth_api.route("/user/<int:user_id>", methods=["PUT"])
@login_required  
def update_user(user_id):
    """Update user information - Admin only"""
    if current_user.role_user_id != 1:
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    if current_user.id == user_id:
        return jsonify({"success": False, "message": "You cannot edit your own account here, use Account Settings"}), 400
    data = request.get_json()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    role_id = data.get('role_user_id')

    if not all([first_name, last_name, email, role_id]):
        return jsonify({"success": False, "message": "First name, last name, email, and role are required"}), 400

    if password and len(password) < 8:
        return jsonify({"success": False, "message": "Password must be at least 8 characters"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM "user" WHERE id = %s', (user_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "User not found"}), 404

        cursor.execute('SELECT id FROM "user" WHERE email = %s AND id != %s', (email, user_id))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Email already in use"}), 400

        if password:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            sql = 'UPDATE "user" SET first_name = %s, last_name = %s, email = %s, password = %s, role_user_id = %s, updated_at = %s WHERE id = %s'
            params = (first_name, last_name, email, hashed, role_id, datetime.now(), user_id)
        else:
            sql = 'UPDATE "user" SET first_name = %s, last_name = %s, email = %s, role_user_id = %s, updated_at = %s WHERE id = %s'
            params = (first_name, last_name, email, role_id, datetime.now(), user_id)

        cursor.execute(sql, params)
        conn.commit()
        cursor.close()
        conn.close()

        log_activity(
            action_type="user_updated",
            target_entity="user",
            target_id=str(user_id),
            additional_metadata={"updated_by": current_user.email}
        )

        return jsonify({"success": True, "message": "User updated successfully"})
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({"success": False, "message": str(e)}), 500