"""
Applicants API — HTTP only.
All business logic delegated to ApplicantService, CSVImportService, ExportService.
File streaming (make_response / send_file) stays here as an HTTP concern.
"""

from flask import Blueprint, make_response, request, jsonify
from flask_login import current_user, login_required
from utils.permissions import require_admin, require_faculty_or_admin
from services.applicant_service import ApplicantService
from services.csv_import_service import CSVImportService
from services.export_service import ExportService

applicants_api = Blueprint("applicants_api", __name__)
_applicant_svc = ApplicantService()
_csv_svc = CSVImportService()
_export_svc = ExportService()

_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@applicants_api.route("/upload", methods=["POST"])
def upload_csv():
    """Handle CSV file upload and processing (Admin only)."""
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied"}), 403

    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file uploaded"})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "message": "No file selected"})

    if not file.filename.lower().endswith(".csv"):
        return jsonify({"success": False, "message": "Please upload a CSV file"})

    try:
        result = _csv_svc.import_file(file.read(), current_user.email)
        from datetime import datetime
        return jsonify({
            "success": True,
            "message": result["message"],
            "records_processed": result["records_processed"],
            "processed_at": datetime.now().isoformat(),
        })
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error processing file: {str(e)}"})


@applicants_api.route("/applicants", methods=["GET"])
def get_applicants():
    """Get all applicants, optionally filtered by session."""
    session_id = request.args.get("session_id", type=int)
    try:
        applicants = _applicant_svc.get_all(session_id=session_id)
        return jsonify({"success": True, "applicants": applicants})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@applicants_api.route("/applicant-info/<user_code>", methods=["GET"])
def get_applicant_info(user_code):
    """Get detailed applicant information by user code."""
    try:
        return jsonify({"success": True, "applicant": _applicant_svc.get_info(user_code)})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@applicants_api.route("/applicant-test-scores/<user_code>", methods=["GET"])
def get_applicant_test_scores(user_code):
    """Get all test scores for an applicant."""
    try:
        return jsonify({"success": True, "test_scores": _applicant_svc.get_test_scores(user_code)})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@applicants_api.route("/applicant-institutions/<user_code>", methods=["GET"])
def get_applicant_institutions(user_code):
    """Get all institution history for an applicant."""
    try:
        return jsonify({"success": True, "institutions": _applicant_svc.get_institutions(user_code)})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@applicants_api.route("/applicant-application-info/<user_code>", methods=["GET"])
def get_applicant_application_info(user_code):
    """Get application info for an applicant."""
    try:
        return jsonify({"success": True, "application_info": _applicant_svc.get_application_info(user_code)})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@applicants_api.route("/applicant-application-info/<user_code>/status", methods=["PUT"])
def update_applicant_status(user_code):
    """Update applicant status (Admin only)."""
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied"}), 403
    data = request.get_json() or {}
    try:
        message = _applicant_svc.update_status(user_code, data.get("status"))
        return jsonify({"success": True, "message": message})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@applicants_api.route("/applicant-application-info/<user_code>/prerequisites", methods=["PUT"])
def update_applicant_prerequisites(user_code):
    """Update prerequisite courses and GPA (Admin/Faculty only)."""
    if not current_user.is_authenticated or current_user.is_viewer:
        return jsonify({"success": False, "message": "Access denied"}), 403
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Invalid request data"}), 400
    if not user_code or not user_code.strip():
        return jsonify({"success": False, "message": "Invalid user code"}), 400

    cs = str(data.get("cs", "")).strip()[:1000]
    stat = str(data.get("stat", "")).strip()[:1000]
    math = str(data.get("math", "")).strip()[:1000]
    additional_comments = str(data.get("additional_comments", "")).strip()[:2000]
    gpa_raw = data.get("gpa", "")
    gpa = str(gpa_raw).strip()[:50] if gpa_raw and gpa_raw != "" else None

    try:
        message = _applicant_svc.update_prerequisites(
            user_code, cs, stat, math, gpa, additional_comments,
            data.get("mds_v"), data.get("mds_cl"), data.get("mds_o"),
        )
        return jsonify({"success": True, "message": message})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@applicants_api.route("/applicant-application-info/<user_code>/english-comment", methods=["PUT"])
def update_english_comment(user_code):
    """Update English proficiency comment (Admin only)."""
    if not current_user.is_authenticated or current_user.is_viewer or current_user.is_faculty:
        return jsonify({"success": False, "message": "Access denied"}), 403
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Invalid request data"}), 400
    if not user_code or not user_code.strip():
        return jsonify({"success": False, "message": "Invalid user code"}), 400

    comment = str(data.get("english_comment", "")).strip()[:2000]
    try:
        message = _applicant_svc.update_english_comment(user_code, comment)
        return jsonify({"success": True, "message": message})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@applicants_api.route("/applicant-application-info/<user_code>/english-status", methods=["PUT"])
def update_english_status(user_code):
    """Update English status (Admin only)."""
    if not current_user.is_authenticated or current_user.is_viewer or current_user.is_faculty:
        return jsonify({"success": False, "message": "Access denied"}), 403
    data = request.get_json() or {}
    try:
        message = _applicant_svc.update_english_status(user_code, data.get("english_status"))
        return jsonify({"success": True, "message": message})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@applicants_api.route("/applicant-application-info/<user_code>/scholarship", methods=["PUT"])
@require_admin
def update_applicant_scholarship_endpoint(user_code):
    """Update scholarship decision (Admin only)."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Invalid request data"}), 400
    try:
        message = _applicant_svc.update_scholarship(user_code, data.get("scholarship", "Undecided"))
        return jsonify({"success": True, "message": message})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@applicants_api.route("/export/all", methods=["GET"])
def export_all_applicants():
    """Export all applicants as XLSX (Admin/Faculty only)."""
    if not current_user.is_authenticated or current_user.is_viewer:
        return jsonify({"success": False, "message": "Access denied"}), 403
    try:
        output, filename = _export_svc.export_all(current_user.email)
        response = make_response(output.getvalue())
        response.headers["Content-Type"] = _XLSX_MIME
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return response
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "message": f"Export failed: {str(e)}"}), 500


@applicants_api.route("/export/selected", methods=["POST"])
def export_selected_applicants():
    """Export selected applicants as XLSX (Admin/Faculty only)."""
    if not current_user.is_authenticated or current_user.is_viewer:
        return jsonify({"success": False, "message": "Access denied"}), 403
    data = request.get_json() or {}
    try:
        output, filename = _export_svc.export_selected(
            data.get("user_codes", []),
            data.get("sections"),
            current_user.email,
        )
        response = make_response(output.getvalue())
        response.headers["Content-Type"] = _XLSX_MIME
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return response
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Export failed: {str(e)}"}), 500


@applicants_api.route("/clear-all-data", methods=["DELETE"])
@login_required
def clear_all_data():
    """Clear all applicant data (Admin only)."""
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied. Admin privileges required."}), 403
    try:
        result = _applicant_svc.clear_all_data(current_user.email)
        return jsonify({"success": True, "message": result["message"], "tables_cleared": result["tables_cleared"]})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
