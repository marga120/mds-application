from utils.db_helpers import db_connection, db_transaction
import bcrypt
from flask_login import UserMixin


class User(UserMixin):
    """Flask-Login user model. Keep this class — required by Flask-Login."""

    def __init__(self, id, first_name, last_name, email, password_hash, role_user_id, role_name=None, campus=None, program=None):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password_hash = password_hash
        self.role_user_id = role_user_id
        self.role_name = role_name
        self.campus = campus
        self.program = program

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_super_admin(self):
        return self.role_name == "Super Admin"

    @property
    def is_admin(self):
        return self.role_name in ("Admin", "Super Admin")

    @property
    def is_faculty(self):
        return self.role_name == "Faculty"

    @property
    def is_viewer(self):
        return self.role_name == "Viewer"


# ---------------------------------------------------------------------------
# Utility kept for seed.py compatibility
# ---------------------------------------------------------------------------

def hash_password(password):
    """Hash a plaintext password with bcrypt. Used by seed.py."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_USER_SELECT = """
    SELECT u.id, u.first_name, u.last_name, u.email, u.password,
           u.role_user_id, r.name AS role_name, u.campus, u.program,
           u.created_at, u.updated_at
    FROM "user" u
    JOIN role_user r ON u.role_user_id = r.id
"""


def _to_user(row):
    if not row:
        return None
    return User(
        id=row["id"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        email=row["email"],
        password_hash=row["password"],
        role_user_id=row["role_user_id"],
        role_name=row["role_name"],
        campus=row.get("campus"),
        program=row.get("program"),
    )


def _to_dict(row):
    if not row:
        return None
    return {
        "id": row["id"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "full_name": f"{row['first_name']} {row['last_name']}",
        "email": row["email"],
        "role_id": row["role_user_id"],
        "role_user_id": row["role_user_id"],
        "role_name": row.get("role_name"),
        "campus": row.get("campus"),
        "program": row.get("program"),
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
    }


# ---------------------------------------------------------------------------
# SQL functions — data access only
# ---------------------------------------------------------------------------

def get_role_by_id(role_id):
    """Return {id, name} dict for a role, or None."""
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("SELECT id, name FROM role_user WHERE id = %s", (role_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception:
        return None


def authenticate_user(email, password):
    """Return User object if credentials valid, else None."""
    try:
        with db_connection() as (conn, cursor):
            cursor.execute(_USER_SELECT + " WHERE u.email = %s", (email,))
            row = cursor.fetchone()
        if row and bcrypt.checkpw(password.encode("utf-8"), row["password"].encode("utf-8")):
            return _to_user(row)
        return None
    except Exception:
        return None


def get_user_by_id(user_id):
    """Return User object — used by Flask-Login user_loader."""
    try:
        with db_connection() as (conn, cursor):
            cursor.execute(_USER_SELECT + " WHERE u.id = %s", (user_id,))
            return _to_user(cursor.fetchone())
    except Exception:
        return None


def get_user_by_id_dict(user_id):
    """Return user as dict for API responses."""
    try:
        with db_connection() as (conn, cursor):
            cursor.execute(_USER_SELECT + " WHERE u.id = %s", (user_id,))
            return _to_dict(cursor.fetchone())
    except Exception:
        return None


def get_user_by_email(email):
    """Return user dict if email exists, else None. Used for duplicate checks."""
    try:
        with db_connection() as (conn, cursor):
            cursor.execute(_USER_SELECT + " WHERE u.email = %s", (email,))
            return _to_dict(cursor.fetchone())
    except Exception:
        return None


def get_user_password_hash(user_id):
    """Return stored bcrypt hash for a user. Used for password verification."""
    try:
        with db_connection() as (conn, cursor):
            cursor.execute('SELECT password FROM "user" WHERE id = %s', (user_id,))
            row = cursor.fetchone()
            return row["password"] if row else None
    except Exception:
        return None


def get_all_users(search_query=None):
    """Return list of user dicts, optionally filtered by name/email."""
    try:
        with db_connection() as (conn, cursor):
            sql = """
                SELECT u.id, u.first_name, u.last_name, u.email, u.role_user_id,
                       r.name AS role_name, u.campus, u.program, u.created_at, u.updated_at
                FROM "user" u
                JOIN role_user r ON u.role_user_id = r.id
            """
            params = []
            if search_query:
                sql += " WHERE CONCAT(u.first_name, ' ', u.last_name) ILIKE %s OR u.email ILIKE %s"
                term = f"%{search_query}%"
                params = [term, term]
            sql += " ORDER BY u.created_at DESC LIMIT 50"
            cursor.execute(sql, params)
            return [_to_dict(r) for r in cursor.fetchall()]
    except Exception:
        return []


def create_user(email, password_hash, first_name, last_name, role_id, campus=None, program=None):
    """INSERT new user. Returns created user dict."""
    with db_transaction() as (conn, cursor):
        cursor.execute(
            """
            INSERT INTO "user" (first_name, last_name, email, password, role_user_id,
                                campus, program, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id, first_name, last_name, email, role_user_id, campus, program,
                      created_at, updated_at
            """,
            (first_name, last_name, email, password_hash, role_id, campus, program),
        )
        row = cursor.fetchone()
        return {
            "id": row["id"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "full_name": f"{row['first_name']} {row['last_name']}",
            "email": row["email"],
            "role_id": row["role_user_id"],
            "role_user_id": row["role_user_id"],
            "campus": row.get("campus"),
            "program": row.get("program"),
            "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        }


def update_user(user_id, email, first_name, last_name, role_id, password_hash=None, campus=None, program=None):
    """UPDATE user fields. Returns updated user dict."""
    with db_transaction() as (conn, cursor):
        if password_hash:
            cursor.execute(
                'UPDATE "user" SET first_name=%s, last_name=%s, email=%s, role_user_id=%s, '
                "password=%s, campus=%s, program=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s",
                (first_name, last_name, email, role_id, password_hash, campus, program, user_id),
            )
        else:
            cursor.execute(
                'UPDATE "user" SET first_name=%s, last_name=%s, email=%s, role_user_id=%s, '
                "campus=%s, program=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s",
                (first_name, last_name, email, role_id, campus, program, user_id),
            )
    return get_user_by_id_dict(user_id)


def delete_user(user_id):
    """DELETE a user. Handles cascade: ratings, activity_log null. Returns True."""
    with db_transaction() as (conn, cursor):
        cursor.execute("DELETE FROM ratings WHERE user_id = %s", (user_id,))
        cursor.execute("UPDATE activity_log SET user_id = NULL WHERE user_id = %s", (user_id,))
        cursor.execute('DELETE FROM "user" WHERE id = %s', (user_id,))
    return True


def delete_users_bulk(user_ids):
    """DELETE multiple users in one transaction. Returns count deleted."""
    if not user_ids:
        return 0
    with db_transaction() as (conn, cursor):
        cursor.execute("DELETE FROM ratings WHERE user_id = ANY(%s)", (user_ids,))
        cursor.execute("UPDATE activity_log SET user_id = NULL WHERE user_id = ANY(%s)", (user_ids,))
        cursor.execute('DELETE FROM "user" WHERE id = ANY(%s)', (user_ids,))
        return cursor.rowcount


def update_email(user_id, email):
    """UPDATE user email. Returns updated user dict."""
    with db_transaction() as (conn, cursor):
        cursor.execute(
            'UPDATE "user" SET email=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s',
            (email, user_id),
        )
    return get_user_by_id_dict(user_id)


def update_password(user_id, password_hash):
    """UPDATE user password hash. Returns True."""
    with db_transaction() as (conn, cursor):
        cursor.execute(
            'UPDATE "user" SET password=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s',
            (password_hash, user_id),
        )
    return True
