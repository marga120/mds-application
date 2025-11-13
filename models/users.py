from utils.database import get_db_connection
from psycopg2.extras import RealDictCursor
import bcrypt
from flask_login import UserMixin


class User(UserMixin):
    """
    User model class for Flask-Login integration.

    Represents a system user with authentication credentials and role information.
    Integrates with Flask-Login for session management and provides role-based
    property accessors.

    @param id: Unique user identifier
    @param_type id: int
    @param first_name: User's first name
    @param_type first_name: str
    @param last_name: User's last name
    @param_type last_name: str
    @param email: User's email address
    @param_type email: str
    @param password_hash: Hashed password
    @param_type password_hash: str
    @param role_user_id: Foreign key to role table
    @param_type role_user_id: int
    @param role_name: Role name (optional)
    @param_type role_name: str or None

    @property full_name: Returns formatted full name
    @property is_admin: Returns True if user role is Admin
    @property is_faculty: Returns True if user role is Faculty
    @property is_viewer: Returns True if user role is Viewer
    """

    def __init__(
        self,
        id,
        first_name,
        last_name,
        email,
        password_hash,
        role_user_id,
        role_name=None,
    ):
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


def hash_password(password):
    """
    Hash a password using bcrypt with salt.

    Securely hashes a plaintext password using bcrypt algorithm with
    automatically generated salt for secure storage in database.

    @param password: Plaintext password to hash
    @param_type password: str

    @return: Hashed password string
    @return_type: str

    @security: Uses bcrypt.gensalt() for random salt generation
    @encoding: Handles UTF-8 encoding/decoding

    @example:
        hashed = hash_password("user_password123")
        # Returns bcrypt hashed string like "$2b$12$..."
    """

    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password, password_hash):
    """
    Verify a password against its hash.

    Verifies that a plaintext password matches a previously hashed password
    using bcrypt verification algorithm.

    @param password: Plaintext password to verify
    @param_type password: str
    @param password_hash: Stored password hash
    @param_type password_hash: str

    @return: True if password matches hash, False otherwise
    @return_type: bool

    @security: Uses bcrypt.checkpw() for secure verification
    @encoding: Handles UTF-8 encoding

    @example:
        is_valid = verify_password("user_password123", stored_hash)
        if is_valid:
            print("Password is correct")
    """

    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def get_user_by_email(email):
    """
    Retrieve user information by email address.

    Searches the database for a user with the specified email address
    and returns a User object with role information if found.

    @param email: Email address to search for
    @param_type email: str

    @return: User object if found, None otherwise
    @return_type: User or None

    @db_tables: user, role_user
    @joins: JOIN with role_user table for role information

    @example:
        user = get_user_by_email("admin@example.com")
        if user:
            print(f"Found user: {user.full_name} ({user.role_name})")
    """

    """Get user by email address"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT u.id, u.first_name, u.last_name, u.email, u.password, u.role_user_id, r.name as role_name
            FROM "user" u
            JOIN role_user r ON u.role_user_id = r.id
            WHERE u.email = %s
        """,
            (email,),
        )

        user_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if user_data:
            return User(
                id=user_data["id"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                email=user_data["email"],
                password_hash=user_data["password"],
                role_user_id=user_data["role_user_id"],
                role_name=user_data["role_name"],
            )
        return None

    except Exception as e:
        print(f"Error getting user: {e}")
        return None


def get_user_by_id(user_id):
    """
    Retrieve user information by user ID.

    Searches the database for a user with the specified ID and returns
    a User object with role information. Used by Flask-Login user loader.

    @param user_id: User ID to search for
    @param_type user_id: int

    @return: User object if found, None otherwise
    @return_type: User or None

    @db_tables: user, role_user
    @joins: JOIN with role_user table for role information
    @flask_login: Used as user_loader callback

    @example:
        user = get_user_by_id(1)
        if user:
            print(f"Loaded user: {user.email}")
    """

    """Get user by ID (required for Flask-Login)"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT u.id, u.first_name, u.last_name, u.email, u.password, u.role_user_id, r.name as role_name
            FROM "user" u
            JOIN role_user r ON u.role_user_id = r.id
            WHERE u.id = %s
        """,
            (user_id,),
        )

        user_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if user_data:
            return User(
                id=user_data["id"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                email=user_data["email"],
                password_hash=user_data["password"],
                role_user_id=user_data["role_user_id"],
                role_name=user_data["role_name"],
            )
        return None

    except Exception as e:
        print(f"Error getting user by ID: {e}")
        return None


def authenticate_user(email, password):
    """
    Authenticate user with email and password.

    Verifies user credentials by checking email exists and password
    matches the stored hash. Returns User object if authentication succeeds.

    @param email: User's email address
    @param_type email: str
    @param password: User's plaintext password
    @param_type password: str

    @return: User object if authenticated, None if invalid credentials
    @return_type: User or None

    @security: Uses bcrypt password verification
    @process:
        1. Look up user by email
        2. Verify password against stored hash
        3. Return user object if both checks pass

    @example:
        user = authenticate_user("admin@example.com", "password123")
        if user:
            print(f"Authentication successful for {user.full_name}")
        else:
            print("Invalid credentials")
    """

    """Authenticate a user with email and password"""
    user = get_user_by_email(email)
    if user and verify_password(password, user.password_hash):
        return user
    return None


def create_user(first_name, last_name, email, password, role_user_id):
    """
    Create a new user account in the system.

    Creates a new user record with hashed password and specified role.
    Validates that email is unique and handles database transaction rollback
    on errors.

    @param first_name: User's first name
    @param_type first_name: str
    @param last_name: User's last name
    @param_type last_name: str
    @param email: User's email address (must be unique)
    @param_type email: str
    @param password: User's plaintext password
    @param_type password: str
    @param role_user_id: Role ID (1=Admin, 2=Faculty, 3=Viewer)
    @param_type role_user_id: int

    @return: Tuple of (success, message)
    @return_type: tuple[bool, str]

    @validation:
        - Checks for duplicate email addresses
        - Automatically hashes password before storage
        - Sets created_at and updated_at timestamps

    @security: Password hashed using bcrypt before database storage
    @transaction: Uses database transaction with rollback on error

    @example:
        success, message = create_user("John", "Doe", "john@example.com", "password123", 2)
        if success:
            print("User created successfully")
        else:
            print(f"Error: {message}")
    """

    """Create a new user"""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        cursor = conn.cursor()

        # Check if user already exists
        cursor.execute('SELECT id FROM "user" WHERE email = %s', (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return False, "User with this email already exists"

        # Hash password
        password_hash = hash_password(password)
  

        # Insert new user
        cursor.execute(
            """
            INSERT INTO "user" (first_name, last_name, email, password, role_user_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
            (first_name, last_name, email, password_hash, role_user_id),
        )

        conn.commit()
        cursor.close()
        conn.close()
        return True, "User created successfully"

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return False, f"Error creating user: {str(e)}"
