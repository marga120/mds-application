"""
Statistics API — session comparison endpoints.
All business logic delegated to StatisticsService.
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required
from services.statistics_service import StatisticsService

statistics_api = Blueprint("statistics_api", __name__)
_svc = StatisticsService()


@statistics_api.route("/statistics/compare", methods=["GET"])
@login_required
def compare_sessions():
    """Compare stats for two explicitly chosen sessions."""
    session_a = request.args.get("session_a", type=int)
    session_b = request.args.get("session_b", type=int)
    if not session_a or not session_b:
        return jsonify({"success": False, "message": "session_a and session_b are required"}), 400
    try:
        return jsonify({"success": True, **_svc.compare_sessions(session_a, session_b)}), 200
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@statistics_api.route("/statistics/compare-range", methods=["GET"])
@login_required
def compare_range():
    """Compare a session against the averaged stats of sessions in a year range."""
    session_id = request.args.get("session_id", type=int)
    year_from = request.args.get("year_from", type=int)
    year_to = request.args.get("year_to", type=int)
    if not session_id or not year_from or not year_to:
        return jsonify({"success": False, "message": "session_id, year_from, and year_to are required"}), 400
    try:
        return jsonify({"success": True, **_svc.compare_range(session_id, year_from, year_to)}), 200
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
