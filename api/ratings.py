from flask import Blueprint, request, jsonify
from flask_login import current_user

# Create a Blueprint for ratings API routes
ratings_api = Blueprint("ratings_api", __name__)


@ratings_api.route("/ratings/<user_code>", methods=["GET"])
def get_ratings(user_code):
    """Get all ratings for a specific user"""
    from models.ratings import get_user_ratings

    ratings, error = get_user_ratings(user_code)
    if error:
        return jsonify({"success": False, "message": error}), 400

    return jsonify({"success": True, "ratings": ratings})


@ratings_api.route("/ratings/<user_code>/my-rating", methods=["GET"])
def get_my_ratings(user_code):
    """Get current user's rating for a specific applicant"""
    if not current_user.is_authenticated:
        return jsonify({"success": False, "message": "Authentication required"}), 401

    from models.ratings import get_user_own_rating

    ratings, error = get_user_own_rating(user_code, current_user.id)
    if error:
        return jsonify({"success": False, "message": error}), 400

    return jsonify({"success": True, "rating": ratings})


@ratings_api.route("/ratings/<user_code>", methods=["POST"])
def add_or_update_ratings(user_code):
    """Add or update a rating for a user (Admin/Faculty only)"""
    if not current_user.is_authenticated:
        return jsonify({"success": False, "message": "Authentication required"}), 401

    if current_user.is_viewer:
        return jsonify({"success": False, "message": "Viewers cannot add ratings"}), 403

    from models.ratings import add_or_update_user_ratings

    data = request.get_json()
    ratings = data.get("rating")
    comment = data.get("comment", "")

    if ratings is None or ratings == "":
        return jsonify({"success": False, "message": "Rating is required"}), 400

    # Validate rating format
    try:
        ratings_float = float(ratings)
        if ratings_float < 0.0 or ratings_float > 10.0:
            return (
                jsonify(
                    {"success": False, "message": "Rating must be between 0.0 and 10.0"}
                ),
                400,
            )
        # Check decimal places
        if round(ratings_float, 1) != ratings_float:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Rating can only have one decimal place",
                    }
                ),
                400,
            )
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid rating format"}), 400

    success, message = add_or_update_user_ratings(
        user_code, current_user.id, ratings, comment
    )

    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400
