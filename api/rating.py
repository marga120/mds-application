from flask import Blueprint, request, jsonify
from flask_login import current_user

# Create a Blueprint for rating API routes
rating_api = Blueprint("rating_api", __name__)

@rating_api.route("/ratings/<user_code>", methods=["GET"])
def get_ratings(user_code):
    """Get all ratings for a specific user"""
    from models.rating import get_user_ratings
    
    ratings, error = get_user_ratings(user_code)
    if error:
        return jsonify({"success": False, "message": error}), 400
    
    return jsonify({"success": True, "ratings": ratings})


@rating_api.route("/ratings/<user_code>/my-rating", methods=["GET"])
def get_my_rating(user_code):
    """Get current user's rating for a specific applicant"""
    if not current_user.is_authenticated:
        return jsonify({"success": False, "message": "Authentication required"}), 401
    
    from models.rating import get_user_own_rating
    
    rating, error = get_user_own_rating(user_code, current_user.id)
    if error:
        return jsonify({"success": False, "message": error}), 400
    
    return jsonify({"success": True, "rating": rating})


@rating_api.route("/ratings/<user_code>", methods=["POST"])
def add_or_update_rating(user_code):
    """Add or update a rating for a user"""
    if not current_user.is_authenticated:
        return jsonify({"success": False, "message": "Authentication required"}), 401
    
    from models.rating import add_or_update_user_rating
    
    data = request.get_json()
    rating = data.get('rating')
    comment = data.get('comment', '')
    
    if rating is None or rating == '':
        return jsonify({"success": False, "message": "Rating is required"}), 400
    
    # Validate rating format
    try:
        rating_float = float(rating)
        if rating_float < 0.0 or rating_float > 10.0:
            return jsonify({"success": False, "message": "Rating must be between 0.0 and 10.0"}), 400
        # Check decimal places
        if round(rating_float, 1) != rating_float:
            return jsonify({"success": False, "message": "Rating can only have one decimal place"}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid rating format"}), 400
    
    success, message = add_or_update_user_rating(
        user_code, current_user.id, rating, comment
    )
    
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400