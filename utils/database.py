"""
DATABASE CONNECTION AND INITIALIZATION UTILITY

This module handles all database connectivity, configuration, and initialization
for the MDS Application Management System. It provides connection management,
schema initialization from SQL files, database setup functions, and handles
PostgreSQL-specific operations including complex SQL statement execution.
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Database configuration
DB_CONFIG = {
    "host": os.getenv("HOST"),
    "database": os.getenv("DATABASE"),
    "user": os.getenv("USER"),
    "password": os.getenv("PASSWORD"),
    "port": os.getenv("PORT"),
}


def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


def read_schema_file():
    """Read and return the SQL schema file content"""
    try:
        # Get the directory where this script is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to the project root, then to schema.sql
        schema_path = os.path.join(current_dir, "..", "schema.sql")

        with open(schema_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        print(
            "Error: schema.sql file not found. Make sure it exists in the project root."
        )
        return None
    except Exception as e:
        print(f"Error reading schema.sql: {e}")
        return None


def execute_schema_statements(cursor, schema_content):
    """Execute individual SQL statements from schema content, handling PostgreSQL functions"""
    statements = []
    current_statement = ""
    lines = schema_content.split("\n")

    in_function = False

    for line in lines:
        stripped_line = line.strip()

        # Skip empty lines and pure comments
        if not stripped_line or stripped_line.startswith("--"):
            continue

        # Check for function start/end with $$
        if "$$" in stripped_line:
            in_function = not in_function
            current_statement += line + "\n"

            # If we just ended a function, complete the statement
            if not in_function:
                statements.append(current_statement.strip())
                current_statement = ""
        elif in_function:
            # Inside function, preserve formatting
            current_statement += line + "\n"
        elif stripped_line.endswith(";"):
            # Regular statement ending
            current_statement += stripped_line
            statements.append(current_statement.strip())
            current_statement = ""
        else:
            # Continue building statement
            current_statement += stripped_line + " "

    # Add any remaining statement
    if current_statement.strip():
        statements.append(current_statement.strip())

    # Execute each statement (silently)
    for statement in statements:
        if statement:
            cursor.execute(statement)


def init_database():
    """Initialize database using schema.sql file"""
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False

    try:
        # Read schema file
        schema_content = read_schema_file()
        if not schema_content:
            print("❌ Failed to read schema file")
            return False

        cursor = conn.cursor()

        # Execute schema statements
        execute_schema_statements(cursor, schema_content)

        # Commit all changes
        conn.commit()
        cursor.close()
        conn.close()

        print("✅ Database initialized successfully")
        return True

    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


def check_uploaded_at_column():
    """Check if uploaded_at column exists in students table and add if missing"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Check if uploaded_at column exists
        cursor.execute(
            """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='students' AND column_name='uploaded_at';
        """
        )

        if not cursor.fetchone():
            print("Adding uploaded_at column to students table...")
            cursor.execute(
                """
                ALTER TABLE students 
                ADD COLUMN uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
            """
            )
            conn.commit()
            print("✓ Added uploaded_at column to students table")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"Error checking/adding uploaded_at column: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False