from flask import Blueprint, request, jsonify
import pandas as pd
import io
from datetime import datetime, timezone
from flask_login import current_user

# Import our model functions
from models.student_info import process_csv_data, get_all_student_status

# Create a Blueprint for student info API routes
student_info_api = Blueprint("student_info_api", __name__)


@student_info_api.route("/upload", methods=["POST"])
def upload_csv():
    """Handle CSV file upload and processing (Admin/Faculty only)"""
    if not current_user.is_authenticated or current_user.is_viewer:
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


@student_info_api.route("/students", methods=["GET"])
def get_students():
    """Get all students from database"""
    students, error = get_all_student_status()

    if error:
        return jsonify({"success": False, "message": error})

    return jsonify({"success": True, "students": students})


@student_info_api.route("/student-info/<user_code>", methods=["GET"])
def get_student_info(user_code):
    """Get detailed student information by user code"""
    from models.student_info import get_student_info_by_code

    student_info, error = get_student_info_by_code(user_code)

    if error:
        return jsonify({"success": False, "message": error})

    return jsonify({"success": True, "student": student_info})


@student_info_api.route("/student-test-scores/<user_code>", methods=["GET"])
def get_student_test_scores(user_code):
    """Get all test scores for a student by user code"""
    from models.student_info import get_student_test_scores_by_code

    test_scores, error = get_student_test_scores_by_code(user_code)

    if error:
        return jsonify({"success": False, "message": error})

    return jsonify({"success": True, "test_scores": test_scores})


@student_info_api.route("/student-institutions/<user_code>", methods=["GET"])
def get_student_institutions(user_code):
    """Get all institution information for a student by user code"""
    from models.student_info import get_student_institutions_by_code

    institutions, error = get_student_institutions_by_code(user_code)

    if error:
        return jsonify({"success": False, "message": error})

    return jsonify({"success": True, "institutions": institutions})


@student_info_api.route("/student-app-info/<user_code>", methods=["GET"])
def get_student_app_info(user_code):
    """Get app_info for a student by user code"""
    from models.student_info import get_student_app_info_by_code

    app_info, error = get_student_app_info_by_code(user_code)

    if error:
        return jsonify({"success": False, "message": error})

    return jsonify({"success": True, "app_info": app_info})


@student_info_api.route("/student-app-info/<user_code>/status", methods=["PUT"])
def update_student_status(user_code):
    """Update student status in app_info (Admin/Faculty only)"""
    if not current_user.is_authenticated or current_user.is_viewer:
        return jsonify({"success": False, "message": "Access denied"}), 403

    from models.student_info import update_student_app_status

    data = request.get_json()
    status = data.get("status")

    if not status:
        return jsonify({"success": False, "message": "Status is required"}), 400

    # Validate status values
    valid_statuses = ["Not Reviewed", "Waitlist", "Offer", "CoGS", "Offer Sent"]
    if status not in valid_statuses:
        return jsonify({"success": False, "message": "Invalid status value"}), 400

    success, message = update_student_app_status(user_code, status)

    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400


@student_info_api.route("/student-app-info/<user_code>/prerequisites", methods=["PUT"])
def update_student_prerequisites(user_code):
    """Update student prerequisite courses (Admin/Faculty only)"""
    if not current_user.is_authenticated or current_user.is_viewer:
        return jsonify({"success": False, "message": "Access denied"}), 403

    from models.student_info import update_student_prerequisites

    data = request.get_json()
    cs = data.get("cs", "")
    stat = data.get("stat", "")
    math = data.get("math", "")

    success, message = update_student_prerequisites(user_code, cs, stat, math)

    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400
