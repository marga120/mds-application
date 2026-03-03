"""
services/auth_service.py
Business logic for authentication and user management.
No Flask imports. No SQL. Calls models.users and utils.activity_logger.
"""
import re
import bcrypt
import models.users as users_model
from utils.activity_logger import log_activity


class AuthService:

    def authenticate(self, email, password):
        """Return User object if credentials valid, else None."""
        return users_model.authenticate_user(email, password)

    def get_current_user_info(self, user):
        """Format a User object as a dict for API responses."""
        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "role": user.role_name,
            "role_id": user.role_user_id,
            "is_admin": user.is_admin,
            "is_super_admin": user.is_super_admin,
            "is_faculty": user.is_faculty,
            "is_viewer": user.is_viewer,
            "campus": user.campus,
            "program": user.program,
        }

    def get_all_users(self, search_query=None):
        """Return list of all user dicts, optionally filtered."""
        return users_model.get_all_users(search_query)

    def get_user_by_id(self, user_id):
        """Return user dict or None."""
        return users_model.get_user_by_id_dict(user_id)

    def _is_super_admin_role(self, role_id):
        """Return True if the given role_id maps to the Super Admin role."""
        role = users_model.get_role_by_id(role_id)
        return role is not None and role["name"] == "Super Admin"

    def create_user(self, email, password, first_name, last_name, role_id, campus=None, program=None, caller_is_super_admin=False):
        """
        Validate, check duplicate email, hash password, create user, log activity.
        Raises ValueError on validation failures.
        Only Super Admins may create Super Admin accounts.
        """
        if self._is_super_admin_role(role_id) and not caller_is_super_admin:
            raise ValueError("Only Super Admins can create Super Admin accounts.")
        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
            raise ValueError("Invalid email address.")
        if users_model.get_user_by_email(email):
            raise ValueError("Email already in use.")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters.")

        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user = users_model.create_user(
            email, password_hash, first_name, last_name, role_id,
            campus=campus or None, program=program or None,
        )
        log_activity(
            action_type="user_created",
            target_entity="user",
            target_id=str(user["id"]),
        )
        return user

    def update_user(self, user_id, email, first_name, last_name, role_id, password=None, campus=None, program=None, caller_is_super_admin=False):
        """
        Validate, check duplicate email if changed, optionally re-hash password, update, log.
        Raises ValueError on failures.
        Only Super Admins may edit Super Admin accounts or assign the Super Admin role.
        """
        existing = users_model.get_user_by_id_dict(user_id)
        if not existing:
            raise ValueError("User not found.")

        if existing["role_name"] == "Super Admin" and not caller_is_super_admin:
            raise ValueError("Only Super Admins can edit Super Admin accounts.")
        if self._is_super_admin_role(role_id) and not caller_is_super_admin:
            raise ValueError("Only Super Admins can assign the Super Admin role.")

        if email != existing["email"]:
            dup = users_model.get_user_by_email(email)
            if dup and dup["id"] != user_id:
                raise ValueError("Email already in use.")

        password_hash = None
        if password:
            if len(password) < 8:
                raise ValueError("Password must be at least 8 characters.")
            password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        user = users_model.update_user(
            user_id, email, first_name, last_name, role_id, password_hash,
            campus=campus or None, program=program or None,
        )
        log_activity(
            action_type="user_updated",
            target_entity="user",
            target_id=str(user_id),
        )
        return user

    def delete_user(self, user_id, current_user_id, caller_is_super_admin=False):
        """Log activity then delete. Raises ValueError if deleting own account or a Super Admin (without Super Admin privileges)."""
        if user_id == current_user_id:
            raise ValueError("You cannot delete your own account.")
        target = users_model.get_user_by_id_dict(user_id)
        if target and target["role_name"] == "Super Admin" and not caller_is_super_admin:
            raise ValueError("Only Super Admins can delete Super Admin accounts.")
        log_activity(
            action_type="user_deleted",
            target_entity="user",
            target_id=str(user_id),
        )
        users_model.delete_user(user_id)
        return True

    def delete_users_bulk(self, user_ids, current_user_id, caller_is_super_admin=False):
        """Filter out self (and Super Admins if caller is not Super Admin), log each deletion, bulk delete. Returns count."""
        user_ids = [uid for uid in user_ids if uid != current_user_id]
        if not caller_is_super_admin:
            # Fetch each user to check role; skip Super Admin accounts
            filtered = []
            for uid in user_ids:
                u = users_model.get_user_by_id_dict(uid)
                if u and u["role_name"] != "Super Admin":
                    filtered.append(uid)
            user_ids = filtered
        if not user_ids:
            return 0
        for uid in user_ids:
            log_activity(
                action_type="user_deleted",
                target_entity="user",
                target_id=str(uid),
            )
        return users_model.delete_users_bulk(user_ids)

    def update_email(self, user_id, new_email, current_password):
        """Verify password, check duplicate email, update, log. Raises ValueError."""
        stored_hash = users_model.get_user_password_hash(user_id)
        if not stored_hash or not bcrypt.checkpw(
            current_password.encode("utf-8"), stored_hash.encode("utf-8")
        ):
            raise ValueError("Incorrect password.")

        dup = users_model.get_user_by_email(new_email)
        if dup and dup["id"] != user_id:
            raise ValueError("Email already in use.")

        user = users_model.update_email(user_id, new_email)
        log_activity(
            action_type="email_updated",
            target_entity="user",
            target_id=str(user_id),
        )
        return user

    def reset_password(self, user_id, current_password, new_password):
        """Verify current password, validate new password, hash and update, log."""
        stored_hash = users_model.get_user_password_hash(user_id)
        if not stored_hash or not bcrypt.checkpw(
            current_password.encode("utf-8"), stored_hash.encode("utf-8")
        ):
            raise ValueError("Current password is incorrect.")
        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters.")

        new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        users_model.update_password(user_id, new_hash)
        log_activity(
            action_type="password_reset",
            target_entity="user",
            target_id=str(user_id),
        )
        return True
