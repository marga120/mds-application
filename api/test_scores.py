from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from utils.database import get_db_connection
from datetime import datetime, date

# Create a Blueprint for ratings API routes
test_scores_api = Blueprint("test_scores_api", __name__)


@test_scores_api.route("/duolingo-score/<user_code>", methods=["POST"])
@login_required
def save_duolingo_score(user_code):
    """Save Duolingo score for an applicant (Admin only)"""
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Invalid request data"}), 400

    score = data.get("score")
    description = data.get("description", "").strip()
    date_written = data.get("date_written")

    # Validate score
    if score is not None:
        try:
            score = int(score)
            if score < 0 or score > 160:
                return (
                    jsonify(
                        {"success": False, "message": "Score must be between 0 and 160"}
                    ),
                    400,
                )
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Invalid score format"}), 400

    # Parse date
    parsed_date = None
    if date_written:
        try:
            parsed_date = datetime.strptime(date_written, "%Y-%m-%d").date()
            # Validate date is not in the future
            if parsed_date > datetime.now().date():
                return (
                    jsonify(
                        {"success": False, "message": "Date cannot be in the future"}
                    ),
                    400,
                )
        except ValueError:
            return jsonify({"success": False, "message": "Invalid date format"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()

        # Check if record exists
        cursor.execute(
            "SELECT user_code FROM duolingo WHERE user_code = %s", (user_code,)
        )
        exists = cursor.fetchone()

        current_time = datetime.now()

        if exists:
            # Update existing record
            cursor.execute(
                """
                UPDATE duolingo 
                SET score = %s, description = %s, date_written = %s, updated_at = %s
                WHERE user_code = %s
                """,
                (score, description, parsed_date, current_time, user_code),
            )
        else:
            # Insert new record
            cursor.execute(
                """
                INSERT INTO duolingo (user_code, score, description, date_written, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    user_code,
                    score,
                    description,
                    parsed_date,
                    current_time,
                    current_time,
                ),
            )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify(
            {"success": True, "message": "Duolingo score saved successfully"}
        )

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
