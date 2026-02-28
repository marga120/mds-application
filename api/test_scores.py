from flask import Blueprint, request, jsonify
from flask_login import login_required
from utils.permissions import require_admin
from models.test_scores import save_duolingo_score
from datetime import datetime

# Create a Blueprint for test scores API routes
test_scores_api = Blueprint("test_scores_api", __name__)


@test_scores_api.route("/duolingo-score/<user_code>", methods=["POST"])
@require_admin
def save_duolingo_score_route(user_code):
    """
    Save or update Duolingo English test score for an applicant.

    @requires: Admin authentication
    @param user_code: Unique identifier for the applicant (URL parameter)
    @param score: Duolingo test score (JSON body, 0-160)
    @param description: Test description or notes (JSON body, optional)
    @param date_written: Test date in YYYY-MM-DD format (JSON body, optional)
    """
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
                return jsonify({"success": False, "message": "Score must be between 0 and 160"}), 400
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Invalid score format"}), 400

    # Parse date
    parsed_date = None
    if date_written:
        try:
            parsed_date = datetime.strptime(date_written, "%Y-%m-%d").date()
            if parsed_date > datetime.now().date():
                return jsonify({"success": False, "message": "Date cannot be in the future"}), 400
        except ValueError:
            return jsonify({"success": False, "message": "Invalid date format"}), 400

    try:
        save_duolingo_score(user_code, score, description, parsed_date, datetime.now())
        return jsonify({"success": True, "message": "Duolingo score saved successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
