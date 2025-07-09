import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    
    
    # Database Configuration
    DB_CONFIG = {
        'host': os.getenv("HOST"),
        'database': os.getenv("DATABASE"),
        'user': os.getenv("USER"),
        'password': os.getenv("PASSWORD"),
        'port': os.getenv("PORT")
    }
    
    # Upload Configuration
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size