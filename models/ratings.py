from utils.database import get_db_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime


def get_user_ratings(user_code):
    """Get all ratings for a specific user"""
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT 
                r.user_code,
                r.user_id,
                r.rating,
                r.user_comment,
                u.first_name,
                u.last_name,
                u.email
            FROM ratings r
            JOIN "user" u ON r.user_id = u.id
            WHERE r.user_code = %s
            ORDER BY u.first_name, u.last_name
        """,
            (user_code,),
        )

        ratings = cursor.fetchall()
        cursor.close()
        conn.close()

        return ratings, None

    except Exception as e:
        if conn:
            conn.close()
        return None, f"Database error: {str(e)}"


def add_or_update_user_ratings(user_code, user_id, rating, comment):
    """Add or update a rating for a user"""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        cursor = conn.cursor()
        current_time = datetime.now()

        # Validate rating
        try:
            ratings_decimal = float(rating)
            if ratings_decimal < 0.0 or ratings_decimal > 10.0:
                return False, "Rating must be between 0.0 and 10.0"
            # Round to 1 decimal place
            ratings_decimal = round(ratings_decimal, 1)
        except (ValueError, TypeError):
            return False, "Invalid rating format"

        # Use INSERT ... ON CONFLICT for PostgreSQL with composite primary key
        cursor.execute(
            """
            INSERT INTO ratings (user_id, user_code, rating, user_comment, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, user_code) 
            DO UPDATE SET 
                rating = EXCLUDED.rating,
                user_comment = EXCLUDED.user_comment,
                updated_at = EXCLUDED.updated_at
        """,
            (user_id, user_code, ratings_decimal, comment, current_time, current_time),
        )

        message = "Rating saved successfully"

        conn.commit()
        cursor.close()
        conn.close()

        return True, message

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return False, f"Database error: {str(e)}"


def get_user_own_rating(user_code, user_id):
    """Get current user's own rating for a specific applicant"""
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT rating, user_comment, user_code
            FROM ratings 
            WHERE user_id = %s AND user_code = %s
        """,
            (user_id, user_code),
        )

        rating = cursor.fetchone()
        cursor.close()
        conn.close()

        return rating, None

    except Exception as e:
        if conn:
            conn.close()
        return None, f"Database error: {str(e)}"
