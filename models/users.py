from utils.database import get_db_connection
from psycopg2.extras import RealDictCursor
import bcrypt
from flask_login import UserMixin


class User(UserMixin):
    """Flask-Login user model. Keep this class — required by Flask-Login."""

    def __init__(self, id, first_name, last_name, email, password_hash, role_user_id, role_name=None):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password_hash = password_hash
        self.role_user_id = role_user_id
        self.role_name = role_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self):
        return self.role_name == "Admin"

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
           u.role_user_id, r.name AS role_name, u.created_at, u.updated_at
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
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
    }


# ---------------------------------------------------------------------------
# SQL functions — data access only
# ---------------------------------------------------------------------------

def authenticate_user(email, password):
    """Return User object if credentials valid, else None."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(_USER_SELECT + " WHERE u.email = %s", (email,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row and bcrypt.checkpw(password.encode("utf-8"), row["password"].encode("utf-8")):
            return _to_user(row)
        return None
    except Exception:
        conn.close()
        return None


def get_user_by_id(user_id):
    """Return User object — used by Flask-Login user_loader."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(_USER_SELECT + " WHERE u.id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return _to_user(row)
    except Exception:
        conn.close()
        return None


def get_user_by_id_dict(user_id):
    """Return user as dict for API responses."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(_USER_SELECT + " WHERE u.id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return _to_dict(row)
    except Exception:
        conn.close()
        return None


def get_user_by_email(email):
    """Return user dict if email exists, else None. Used for duplicate checks."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(_USER_SELECT + " WHERE u.email = %s", (email,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return _to_dict(row)
    except Exception:
        conn.close()
        return None


def get_user_password_hash(user_id):
    """Return stored bcrypt hash for a user. Used for password verification."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM "user" WHERE id = %s', (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row[0] if row else None
    except Exception:
        conn.close()
        return None


def get_all_users(search_query=None):
    """Return list of user dicts, optionally filtered by name/email."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        sql = """
            SELECT u.id, u.first_name, u.last_name, u.email, u.role_user_id,
                   r.name AS role_name, u.created_at, u.updated_at
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
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [_to_dict(r) for r in rows]
    except Exception:
        conn.close()
        return []


def create_user(email, password_hash, first_name, last_name, role_id):
    """INSERT new user. Returns created user dict."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            INSERT INTO "user" (first_name, last_name, email, password, role_user_id,
                                created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id, first_name, last_name, email, role_user_id, created_at, updated_at
            """,
            (first_name, last_name, email, password_hash, role_id),
        )
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return {
            "id": row["id"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "full_name": f"{row['first_name']} {row['last_name']}",
            "email": row["email"],
            "role_id": row["role_user_id"],
            "role_user_id": row["role_user_id"],
            "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        }
    except Exception:
        conn.rollback()
        conn.close()
        raise


def update_user(user_id, email, first_name, last_name, role_id, password_hash=None):
    """UPDATE user fields. Returns updated user dict."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if password_hash:
            cursor.execute(
                'UPDATE "user" SET first_name=%s, last_name=%s, email=%s, role_user_id=%s, '
                "password=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s",
                (first_name, last_name, email, role_id, password_hash, user_id),
            )
        else:
            cursor.execute(
                'UPDATE "user" SET first_name=%s, last_name=%s, email=%s, role_user_id=%s, '
                "updated_at=CURRENT_TIMESTAMP WHERE id=%s",
                (first_name, last_name, email, role_id, user_id),
            )
        conn.commit()
        cursor.close()
        conn.close()
        return get_user_by_id_dict(user_id)
    except Exception:
        conn.rollback()
        conn.close()
        raise


def delete_user(user_id):
    """DELETE a user. Handles cascade: ratings, activity_log null. Returns True."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ratings WHERE user_id = %s", (user_id,))
        cursor.execute("UPDATE activity_log SET user_id = NULL WHERE user_id = %s", (user_id,))
        cursor.execute('DELETE FROM "user" WHERE id = %s', (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception:
        conn.rollback()
        conn.close()
        raise


def delete_users_bulk(user_ids):
    """DELETE multiple users in one transaction. Returns count deleted."""
    if not user_ids:
        return 0
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ratings WHERE user_id = ANY(%s)", (user_ids,))
        cursor.execute("UPDATE activity_log SET user_id = NULL WHERE user_id = ANY(%s)", (user_ids,))
        cursor.execute('DELETE FROM "user" WHERE id = ANY(%s)', (user_ids,))
        count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        return count
    except Exception:
        conn.rollback()
        conn.close()
        raise


def update_email(user_id, email):
    """UPDATE user email. Returns updated user dict."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE "user" SET email=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s',
            (email, user_id),
        )
        conn.commit()
        cursor.close()
        conn.close()
        return get_user_by_id_dict(user_id)
    except Exception:
        conn.rollback()
        conn.close()
        raise


def update_password(user_id, password_hash):
    """UPDATE user password hash. Returns True."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE "user" SET password=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s',
            (password_hash, user_id),
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception:
        conn.rollback()
        conn.close()
        raise
