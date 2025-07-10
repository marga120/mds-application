from utils.database import get_db_connection
from psycopg2.extras import RealDictCursor

def upsert_students(students_data, upload_timestamp):
    """Insert new students or update existing ones with upload timestamp"""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed", 0
    
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
        return True, "Students data processed successfully", records_processed
    
    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"Database error: {str(e)}", 0

def get_all_students():
    """Get all students from database"""
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"
    
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
        
        return students, None
    
    except Exception as e:
        return None, f"Database error: {str(e)}"

def update_student(student_id, data):
    """Update a specific student record"""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    
    try:
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
        return success, message
    
    except Exception as e:
        return False, f"Database error: {str(e)}"

def delete_student(student_id):
    """Delete a specific student"""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    
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
        return success, message
    
    except Exception as e:
        return False, f"Database error: {str(e)}"

def get_upload_history():
    """Get upload history with timestamps"""
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"
    
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
        
        return history, None
    
    except Exception as e:
        return None, f"Database error: {str(e)}"