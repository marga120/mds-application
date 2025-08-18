from flask import Blueprint, request, jsonify
import pandas as pd
import io
from datetime import datetime, timezone
from flask_login import current_user
from utils.activity_logger import log_activity

# Import our model functions
from models.applicants import process_csv_data, get_all_applicant_status

# Create a Blueprint for applicant info API routes
applicants_api = Blueprint("applicants_api", __name__)


@applicants_api.route("/upload", methods=["POST"])
def upload_csv():
    """Handle CSV file upload and processing (Admin only)"""
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
        # Read CSV file
        csv_data = file.read().decode("utf-8")
        df = pd.read_csv(io.StringIO(csv_data))

        # Validate that we have the User Code column (primary identifier)
        if "User Code" not in df.columns:
            return jsonify(
                {"success": False, "message": "Missing required column: User Code"}
            )

        # Clean and validate data
        df = df.dropna(subset=["User Code"])  # Remove rows without User Code

        if df.empty:
            return jsonify({"success": False, "message": "No valid data found in CSV"})

        # Use the model function to process data
        success, message, records_processed = process_csv_data(df)

        if success:
            return jsonify(
                {
                    "success": True,
                    "message": message,
                    "records_processed": records_processed,
                    "processed_at": datetime.now().isoformat(),
                }
            )
        else:
            return jsonify({"success": False, "message": message})

    except Exception as e:
        return jsonify(
            {"success": False, "message": f"Error processing file: {str(e)}"}
        )


@applicants_api.route("/applicants", methods=["GET"])
def get_applicants():
    """Get all applicants from database"""
    applicants, error = get_all_applicant_status()

    if error:
        return jsonify({"success": False, "message": error})

    return jsonify({"success": True, "applicants": applicants})


@applicants_api.route("/applicant-info/<user_code>", methods=["GET"])
def get_applicant_info(user_code):
    """Get detailed applicant information by user code"""
    from models.applicants import get_applicant_info_by_code

    applicant_info, error = get_applicant_info_by_code(user_code)

    if error:
        return jsonify({"success": False, "message": error})

    return jsonify({"success": True, "applicant": applicant_info})


@applicants_api.route("/applicant-test-scores/<user_code>", methods=["GET"])
def get_applicant_test_scores(user_code):
    """Get all test scores for a applicant by user code"""
    from models.applicants import get_applicant_test_scores_by_code

    test_scores, error = get_applicant_test_scores_by_code(user_code)

    if error:
        return jsonify({"success": False, "message": error})

    return jsonify({"success": True, "test_scores": test_scores})


@applicants_api.route("/applicant-institutions/<user_code>", methods=["GET"])
def get_applicant_institutions(user_code):
    """Get all institution information for a applicant by user code"""
    from models.applicants import get_applicant_institutions_by_code

    institutions, error = get_applicant_institutions_by_code(user_code)

    if error:
        return jsonify({"success": False, "message": error})

    return jsonify({"success": True, "institutions": institutions})


@applicants_api.route("/applicant-application-info/<user_code>", methods=["GET"])
def get_applicant_application_info(user_code):
    """Get application_info for a applicant by user code"""
    from models.applicants import get_applicant_application_info_by_code

    application_info, error = get_applicant_application_info_by_code(user_code)

    if error:
        return jsonify({"success": False, "message": error})

    return jsonify({"success": True, "application_info": application_info})


@applicants_api.route("/applicant-application-info/<user_code>/status", methods=["PUT"])
def update_applicant_status(user_code):
    """Update applicant status in application_info (Admin only)"""
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied"}), 403

    from models.applicants import update_applicant_application_status

    data = request.get_json()
    status = data.get("status")

    if not status:
        return jsonify({"success": False, "message": "Status is required"}), 400

    # Validate status values
    valid_statuses = [
        "Not Reviewed",
        "Reviewed",
        "Waitlist",
        "Declined",
        "Offer",
        "CoGS",
        "Offer Sent",
    ]
    if status not in valid_statuses:
        return jsonify({"success": False, "message": "Invalid status value"}), 400

    # Get old status first for logging
    from models.applicants import get_applicant_application_info_by_code

    old_info, _ = get_applicant_application_info_by_code(user_code)
    old_status = old_info.get("sent", "Not Reviewed") if old_info else "Not Reviewed"

    success, message = update_applicant_application_status(user_code, status)

    # Log the status change
    if success:
        log_activity(
            action_type="status_change",
            target_entity="applicant",
            target_id=user_code,
            old_value=old_status,
            new_value=status,
            additional_metadata={"user_code": user_code},
        )

    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400


@applicants_api.route(
    "/applicant-application-info/<user_code>/prerequisites", methods=["PUT"]
)
def update_applicant_prerequisites(user_code):
    """Update applicant prerequisites including courses and GPA (Admin/Faculty only)"""
    if not current_user.is_authenticated or current_user.is_viewer:
        return jsonify({"success": False, "message": "Access denied"}), 403

    from models.applicants import update_applicant_prerequisites

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Invalid request data"}), 400

    # Validate user_code format
    if not user_code or not user_code.strip():
        return jsonify({"success": False, "message": "Invalid user code"}), 400

    # Sanitize inputs and limit length
    cs = str(data.get("cs", "")).strip()[:1000]  # Limit to 1000 chars
    stat = str(data.get("stat", "")).strip()[:1000]
    math = str(data.get("math", "")).strip()[:1000]

    # Handle GPA - accept as string input
    gpa = data.get("gpa", "")
    if gpa and gpa != "":
        # Accept any string input, just limit length for database storage
        gpa = str(gpa).strip()[:50]  # Limit to 50 characters
    else:
        gpa = None

    success, message = update_applicant_prerequisites(user_code, cs, stat, math, gpa)

    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400
