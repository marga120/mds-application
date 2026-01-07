from utils.database import get_db_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime


def get_user_ratings(user_code):
    """
    Get all ratings for a specific applicant.
    
    Retrieves all faculty and admin ratings for an applicant including
    reviewer information (name, email) and rating details.
    
    @param user_code: Unique identifier for the applicant
    @param_type user_code: str
    
    @return: Tuple of (ratings_list, error_message)
    @return_type: tuple[list, None] or tuple[None, str]
    
    @db_tables: ratings, user
    @joins: JOIN with user table for reviewer information
    @ordering: Ordered by reviewer first name, last name
    
    @example:
        ratings, error = get_user_ratings("12345")
        if not error:
            for rating in ratings:
                print(f"{rating['first_name']} {rating['last_name']}: {rating['rating']}/10")
    """

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
    """
    Add or update a rating for an applicant.

    Creates a new rating record or updates an existing one using PostgreSQL's
    ON CONFLICT functionality. Validates rating format and range.

    @param user_code: Unique identifier for the applicant
    @param_type user_code: str
    @param user_id: ID of the user providing the rating
    @param_type user_id: int
    @param rating: Optional numerical rating (0.0-10.0, one decimal place), can be None
    @param_type rating: float, str, or None
    @param comment: Optional comment about the applicant
    @param_type comment: str

    @return: Tuple of (success, message)
    @return_type: tuple[bool, str]

    @validation:
        - Rating must be between 0.0 and 10.0 (if provided)
        - Rating rounded to 1 decimal place (if provided)
        - Converts string ratings to float (if provided)
        - At least one of rating or comment should be provided

    @db_tables: ratings
    @upsert: Uses PostgreSQL ON CONFLICT DO UPDATE
    @composite_key: (user_id, user_code) primary key

    @example:
        success, msg = add_or_update_user_ratings("12345", user.id, 8.5, "Strong candidate")
        success, msg = add_or_update_user_ratings("12345", user.id, None, "Just a comment")
        if success:
            print("Rating/comment saved successfully")
    """

    """Add or update a rating for a user"""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        cursor = conn.cursor()
        current_time = datetime.now()

        # Validate rating (allow None/empty for comment-only saves)
        ratings_decimal = None
        if rating is not None and rating != "":
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

        # Update message based on what was saved
        if ratings_decimal is not None and comment:
            message = "Rating and comment saved successfully"
        elif ratings_decimal is not None:
            message = "Rating saved successfully"
        else:
            message = "Comment saved successfully"

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
    """
    Get the current user's rating for a specific applicant.
    
    Retrieves only the rating and comment that the specified user has
    assigned to the given applicant.
    
    @param user_code: Unique identifier for the applicant
    @param_type user_code: str
    @param user_id: ID of the user whose rating to retrieve
    @param_type user_id: int
    
    @return: Tuple of (rating_dict, error_message)
    @return_type: tuple[dict, None] or tuple[None, str]
    
    @db_tables: ratings
    @composite_key: Uses (user_id, user_code) composite primary key
    
    @example:
        rating, error = get_user_own_rating("12345", current_user.id)
        if not error and rating:
            print(f"Your rating: {rating['rating']}/10")
            print(f"Your comment: {rating['user_comment']}")
    """

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
