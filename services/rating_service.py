"""
Rating Service — business logic for applicant ratings.
No Flask, no SQL. Calls models.ratings, logs activity.
"""

from models.ratings import (
    get_user_ratings as _get_ratings,
    get_user_own_rating as _get_own_rating,
    add_or_update_user_ratings as _upsert_rating,
)
from utils.activity_logger import log_activity


class RatingService:

    def get_ratings(self, user_code: str) -> list:
        """Return all ratings for an applicant."""
        ratings, error = _get_ratings(user_code)
        if error:
            raise ValueError(error)
        return ratings or []

    def get_my_rating(self, user_code: str, user_id: int) -> dict | None:
        """Return the current user's rating for an applicant, or None."""
        rating, error = _get_own_rating(user_code, user_id)
        if error:
            raise ValueError(error)
        return rating

    def upsert_rating(self, user_code: str, user_id: int, rating, comment: str) -> str:
        """Validate and upsert a rating. Returns success message."""
        if (rating is None or rating == "") and not comment:
            raise ValueError("Either rating or comment is required")

        if rating is not None and rating != "":
            try:
                r = float(rating)
                if r < 0.0 or r > 10.0:
                    raise ValueError("Rating must be between 0.0 and 10.0")
                if round(r, 2) != r:
                    raise ValueError("Rating can only have up to two decimal places")
            except (TypeError, ValueError) as e:
                if "Rating" in str(e):
                    raise
                raise ValueError("Invalid rating format")

        success, message = _upsert_rating(user_code, user_id, rating, comment)
        if not success:
            raise ValueError(message)

        log_activity(
            action_type="add_rating",
            target_entity="applicant",
            target_id=user_code,
            additional_metadata={"user_id": user_id},
        )
        return message
