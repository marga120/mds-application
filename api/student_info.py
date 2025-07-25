from flask import Blueprint, request, jsonify
import pandas as pd
import io
from datetime import datetime, timezone

# Import our model functions
from models.student_info import process_csv_data, get_all_student_status

# Create a Blueprint for student info API routes
student_info_api = Blueprint("student_info_api", __name__)


@student_info_api.route("/upload", methods=["POST"])
def upload_csv():
    """Handle CSV file upload and processing"""
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
