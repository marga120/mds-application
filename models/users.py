from utils.database import get_db_connection
from psycopg2.extras import RealDictCursor
import bcrypt
from flask_login import UserMixin

class User(UserMixin):
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
        return self.role_name == 'Admin'
    
    @property
    def is_faculty(self):
        return self.role_name == 'Faculty'
    
    @property
    def is_viewer(self):
        return self.role_name == 'Viewer'

def hash_password(password):
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, password_hash):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def get_user_by_email(email):
    """Get user by email address"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT u.id, u.first_name, u.last_name, u.email, u.password, u.role_user_id, r.name as role_name
            FROM "user" u
            JOIN role_user r ON u.role_user_id = r.id
            WHERE u.email = %s
        """, (email,))
        
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user_data:
            return User(
                id=user_data['id'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                email=user_data['email'],
                password_hash=user_data['password'],
                role_user_id=user_data['role_user_id'],
                role_name=user_data['role_name']
            )
        return None
    
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def get_user_by_id(user_id):
    """Get user by ID (required for Flask-Login)"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT u.id, u.first_name, u.last_name, u.email, u.password, u.role_user_id, r.name as role_name
            FROM "user" u
            JOIN role_user r ON u.role_user_id = r.id
            WHERE u.id = %s
        """, (user_id,))
        
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user_data:
            return User(
                id=user_data['id'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                email=user_data['email'],
                password_hash=user_data['password'],
                role_user_id=user_data['role_user_id'],
                role_name=user_data['role_name']
            )
        return None
    
    except Exception as e:
        print(f"Error getting user by ID: {e}")
        return None

def authenticate_user(email, password):
    """Authenticate a user with email and password"""
    user = get_user_by_email(email)
    if user and verify_password(password, user.password_hash):
        return user
    return None

def create_user(first_name, last_name, email, password, role_user_id):
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
        cursor.execute("""
            INSERT INTO "user" (first_name, last_name, email, password, role_user_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (first_name, last_name, email, password_hash, role_user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True, "User created successfully"
    
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return False, f"Error creating user: {str(e)}"