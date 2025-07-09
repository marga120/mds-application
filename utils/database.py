import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv("HOST"),
    'database': os.getenv("DATABASE"),
    'user': os.getenv("USER"),
    'password': os.getenv("PASSWORD"),
    'port': os.getenv("PORT")
}

def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def init_database():
    """Initialize database and create students table"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            create_table_query = """
            CREATE TABLE IF NOT EXISTS students (
                student_id VARCHAR(50) PRIMARY KEY,
                student_name VARCHAR(255) NOT NULL,
                university VARCHAR(255) NOT NULL,
                year INTEGER NOT NULL,
                degree VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            cursor.execute(create_table_query)
            
            # Check if uploaded_at column exists, if not add it
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='students' AND column_name='uploaded_at';
            """)
            
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE students ADD COLUMN uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
                print("Added uploaded_at column to existing students table")
            
            conn.commit()
            cursor.close()
            conn.close()
            print("Database initialized successfully")
        except Exception as e:
            print(f"Database initialization error: {e}")