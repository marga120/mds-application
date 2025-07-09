import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # Database Configuration
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'database': os.environ.get('DB_NAME', 'student_db'),
        'user': os.environ.get('DB_USER', 'your_username'),
        'password': os.environ.get('DB_PASSWORD', 'your_password'),
        'port': os.environ.get('DB_PORT', '5432')
    }
    
    # Upload Configuration
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size