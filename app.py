# app.py - Flask Backend with Upload Timestamps
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import io
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
import pytz

app = Flask(__name__)
CORS(app)

# Database configuration
DB_CONFIG = {
    'host': '',
    'database': '',
    'user': '',
    'password': '',
    'port': ''
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

def upsert_students(students_data, upload_timestamp):
    """Insert new students or update existing ones with upload timestamp"""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    
    try:
        cursor = conn.cursor()
        
        upsert_query = """
        INSERT INTO students (student_id, student_name, university, year, degree, uploaded_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (student_id) 
        DO UPDATE SET 
            student_name = EXCLUDED.student_name,
            university = EXCLUDED.university,
            year = EXCLUDED.year,
            degree = EXCLUDED.degree,
            updated_at = CURRENT_TIMESTAMP
        WHERE students.student_name != EXCLUDED.student_name 
           OR students.university != EXCLUDED.university 
           OR students.year != EXCLUDED.year 
           OR students.degree != EXCLUDED.degree;
        """
        
        records_processed = 0
        
        # Execute upsert for each student
        for _, student in students_data.iterrows():
            cursor.execute(upsert_query, (
                student['student_id'],
                student['student_name'],
                student['university'],
                int(student['year']),
                student['degree'],
                upload_timestamp,
                upload_timestamp
            ))
            records_processed += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        return True, f"Students data processed successfully", records_processed
    
    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"Database error: {str(e)}", 0

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_csv():
    """Handle CSV file upload and processing"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    if not file.filename.lower().endswith('.csv'):
        return jsonify({'success': False, 'message': 'Please upload a CSV file'})
    
    try:
        # Get upload timestamp from request or use current time
        upload_timestamp_str = request.form.get('upload_timestamp')
        if upload_timestamp_str:
            try:
                upload_timestamp = datetime.fromisoformat(upload_timestamp_str.replace('Z', '+00:00'))
            except:
                upload_timestamp = datetime.now()
        else:
            upload_timestamp = datetime.now()
        
        # Ensure timestamp is timezone-aware
        if upload_timestamp.tzinfo is None:
            upload_timestamp = upload_timestamp.replace(tzinfo=timezone.utc)
        
        # Read CSV file
        csv_data = file.read().decode('utf-8')
        df = pd.read_csv(io.StringIO(csv_data))
        
        # Validate required columns
        required_columns = ['student_id', 'student_name', 'university', 'year', 'degree']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({
                'success': False, 
                'message': f'Missing required columns: {", ".join(missing_columns)}'
            })
        
        # Clean and validate data
        df = df.dropna()  # Remove rows with missing values
        df['student_id'] = df['student_id'].astype(str)
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df = df.dropna()  # Remove rows where year conversion failed
        
        if df.empty:
            return jsonify({'success': False, 'message': 'No valid data found in CSV'})
        
        # Upsert data to database with upload timestamp
        success, message, records_processed = upsert_students(df, upload_timestamp)
        
        if success:
            return jsonify({
                'success': True, 
                'message': message,
                'records_processed': records_processed,
                'upload_timestamp': upload_timestamp.isoformat(),
                'processed_at': datetime.now().isoformat()
            })
        else:
            return jsonify({'success': False, 'message': message})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error processing file: {str(e)}'})

@app.route('/api/students', methods=['GET'])
def get_students():
    """Get all students from database"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'})
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT student_id, student_name, university, year, degree, 
                   created_at, updated_at, uploaded_at,
                   EXTRACT(EPOCH FROM (NOW() - updated_at)) as seconds_since_update
            FROM students 
            ORDER BY updated_at DESC, student_name
        """)
        students = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'students': students})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'})

@app.route('/api/students/<student_id>', methods=['PUT'])
def update_student(student_id):
    """Update a specific student record"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'})
    
    try:
        data = request.get_json()
        cursor = conn.cursor()
        
        # Update the student record with current timestamp
        update_query = """
            UPDATE students 
            SET student_name = %s, university = %s, year = %s, degree = %s, updated_at = CURRENT_TIMESTAMP
            WHERE student_id = %s
        """
        
        cursor.execute(update_query, (
            data.get('student_name'),
            data.get('university'),
            data.get('year'),
            data.get('degree'),
            student_id
        ))
        
        if cursor.rowcount > 0:
            conn.commit()
            message = 'Student updated successfully'
            success = True
        else:
            message = 'Student not found'
            success = False
        
        cursor.close()
        conn.close()
        return jsonify({'success': success, 'message': message})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'})

@app.route('/api/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Delete a specific student"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'})
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE student_id = %s", (student_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            message = 'Student deleted successfully'
            success = True
        else:
            message = 'Student not found'
            success = False
        
        cursor.close()
        conn.close()
        return jsonify({'success': success, 'message': message})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'})

@app.route('/api/upload-history', methods=['GET'])
def get_upload_history():
    """Get upload history with timestamps"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'})
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT uploaded_at, COUNT(*) as record_count
            FROM students 
            GROUP BY uploaded_at 
            ORDER BY uploaded_at DESC
            LIMIT 10
        """)
        history = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'history': history})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'})

if __name__ == '__main__':
    init_database()
    app.run(debug=True)