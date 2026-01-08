from flask import Blueprint, request, jsonify
from flask_login import current_user

# Create a Blueprint for ratings API routes
ratings_api = Blueprint("ratings_api", __name__)


@ratings_api.route("/ratings/<user_code>", methods=["GET"])
def get_ratings(user_code):
    """
    Get all ratings for a specific applicant.

    Retrieves all faculty/admin ratings and comments for an applicant,
    including reviewer information.

    @requires: Any authenticated user
    @method: GET
    @param user_code: Unique identifier for the applicant (URL parameter)
    @param_type user_code: str

    @return: JSON response with all ratings for the applicant
    @return_type: flask.Response
    @status_codes:
        - 200: Ratings retrieved successfully
        - 400: Database error

    @db_tables: ratings, user

    @example:
        GET /api/ratings/12345

        Response:
        {
            "success": true,
            "ratings": [
                {
                    "user_code": "12345",
                    "user_id": 2,
                    "rating": 8.5,
                    "user_comment": "Strong candidate",
                    "first_name": "Jane",
                    "last_name": "Faculty",
                    "email": "jane@university.edu"
                }
            ]
        }
    """

    """Get all ratings for a specific user"""
    from models.ratings import get_user_ratings

    ratings, error = get_user_ratings(user_code)
    if error:
        return jsonify({"success": False, "message": error}), 400

    return jsonify({"success": True, "ratings": ratings})


@ratings_api.route("/ratings/<user_code>/my-rating", methods=["GET"])
def get_my_ratings(user_code):
    """
    Get the current user's rating for a specific applicant.

    Retrieves only the rating and comment that the current user has
    assigned to the specified applicant.

    @requires: Any authenticated user
    @method: GET
    @param user_code: Unique identifier for the applicant (URL parameter)
    @param_type user_code: str

    @return: JSON response with current user's rating
    @return_type: flask.Response
    @status_codes:
        - 200: Rating retrieved successfully
        - 400: Database error
        - 401: Authentication required

    @db_tables: ratings

    @example:
        GET /api/ratings/12345/my-rating

        Response:
        {
            "success": true,
            "rating": {
                "user_code": "12345",
                "user_id": 2,
                "rating": 8.5,
                "user_comment": "Strong technical background"
            }
        }
    """

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
    """
    Add or update a rating for an applicant.

    Creates a new rating or updates an existing rating for the specified
    applicant. Only Admin and Faculty users can add/update ratings.
    Viewer users are restricted from rating functionality.

    @requires: Admin or Faculty authentication (Viewer access denied)
    @method: POST
    @param user_code: Unique identifier for the applicant (URL parameter)
    @param_type user_code: str
    @param rating: Optional numerical rating value (JSON body, 0.0-10.0, one decimal)
    @param_type rating: float
    @param comment: Optional comment about the applicant (JSON body)
    @param_type comment: str

    @return: JSON response with operation result
    @return_type: flask.Response
    @status_codes:
        - 200: Rating/comment added/updated successfully
        - 400: Invalid rating format or missing data
        - 401: Authentication required
        - 403: Access denied (Viewer user)
        - 500: Database error

    @validation:
        - At least one of rating or comment must be provided
        - Rating must be between 0.0 and 10.0 (if provided)
        - Rating can have maximum one decimal place (if provided)

    @db_tables: ratings
    @upsert: Uses PostgreSQL ON CONFLICT to update existing ratings

    @example:
        POST /api/ratings/12345
        Content-Type: application/json

        Request:
        {
            "rating": 8.5,
            "comment": "Excellent academic background and strong programming skills"
        }

        Response:
        {
            "success": true,
            "message": "Rating updated successfully"
        }
    """

    """Add or update a rating for a user (Admin/Faculty only)"""
    if not current_user.is_authenticated:
        return jsonify({"success": False, "message": "Authentication required"}), 401

    if current_user.is_viewer:
        return jsonify({"success": False, "message": "Viewers cannot add ratings"}), 403

    from models.ratings import add_or_update_user_ratings

    data = request.get_json()
    ratings = data.get("rating")
    comment = data.get("comment", "")

    # Allow either rating or comment (or both), but at least one must be provided
    if (ratings is None or ratings == "") and not comment:
        return jsonify({"success": False, "message": "Either rating or comment is required"}), 400

    # Validate rating format if provided
    if ratings is not None and ratings != "":
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
