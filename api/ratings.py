"""
Ratings API — HTTP only.
All business logic delegated to RatingService.
"""

from flask import Blueprint, request, jsonify
from flask_login import current_user
from utils.permissions import require_faculty_or_admin
from services.rating_service import RatingService

ratings_api = Blueprint("ratings_api", __name__)
_service = RatingService()


@ratings_api.route("/ratings/<user_code>", methods=["GET"])
def get_ratings(user_code):
    """Get all ratings for an applicant."""
    try:
        return jsonify({"success": True, "ratings": _service.get_ratings(user_code)})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@ratings_api.route("/ratings/<user_code>/my-rating", methods=["GET"])
def get_my_ratings(user_code):
    """Get the current user's rating for an applicant."""
    if not current_user.is_authenticated:
        return jsonify({"success": False, "message": "Authentication required"}), 401
    try:
        return jsonify({"success": True, "rating": _service.get_my_rating(user_code, current_user.id)})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@ratings_api.route("/ratings/<user_code>", methods=["POST"])
@require_faculty_or_admin
def add_or_update_ratings(user_code):
    """Add or update a rating (Admin/Faculty only)."""
    data = request.get_json() or {}
    try:
        message = _service.upsert_rating(
            user_code,
            current_user.id,
            data.get("rating"),
            data.get("comment", ""),
        )
        return jsonify({"success": True, "message": message})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
