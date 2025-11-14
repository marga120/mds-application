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
    """
    Handle CSV file upload and processing for applicant data.

    This endpoint processes uploaded CSV files containing student application data,
    validates the format, and inserts the data into the database. Only Admin users
    can access this functionality.

    @requires: Admin authentication
    @method: POST
    @content_type: multipart/form-data
    @param file: CSV file containing applicant data with required "User Code" column

    @return: JSON response with success status, message, and processing details
    @return_type: flask.Response
    @status_codes:
        - 200: File processed successfully
        - 403: Access denied (non-Admin user)
        - 400: Invalid file format or missing data
        - 500: Processing error

    @raises Exception: If file processing fails
    @logs: Activity logging for file upload actions

    @example:
        POST /api/upload
        Content-Type: multipart/form-data

        Response:
        {
            "success": true,
            "message": "CSV processed successfully",
            "records_processed": 150,
            "processed_at": "2025-08-26T14:30:00"
        }
    """

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

        # Trim trailing whitespace from all column names
        df.columns = df.columns.str.rstrip()

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
    """
    Retrieve all applicants from the database with their basic information.

    Fetches a list of all applicants including their status, contact information,
    ratings, and timeline data. Available to all authenticated users.

    @requires: Any authenticated user (Admin, Faculty, Viewer)
    @method: GET

    @return: JSON response containing list of all applicants
    @return_type: flask.Response
    @status_codes:
        - 200: Applicants retrieved successfully
        - 500: Database error

    @db_tables: applicant_status, applicant_info, ratings

    @example:
        GET /api/applicants

        Response:
        {
            "success": true,
            "applicants": [
                {
                    "user_code": "12345",
                    "family_name": "Smith",
                    "given_name": "John",
                    "email": "john.smith@email.com",
                    "status": "Reviewed",
                    "overall_rating": 8.5
                }
            ]
        }
    """

    """Get all applicants from database"""
    applicants, error = get_all_applicant_status()

    if error:
        return jsonify({"success": False, "message": error})

    return jsonify({"success": True, "applicants": applicants})


@applicants_api.route("/applicant-info/<user_code>", methods=["GET"])
def get_applicant_info(user_code):
    """
    Get detailed applicant information by user code.

    Retrieves comprehensive information about a specific applicant including
    personal details, demographics, contact information, and basic academic data.

    @requires: Any authenticated user
    @method: GET
    @param user_code: Unique identifier for the applicant (URL parameter)
    @param_type user_code: str

    @return: JSON response with detailed applicant information
    @return_type: flask.Response
    @status_codes:
        - 200: Information retrieved successfully
        - 404: Applicant not found
        - 500: Database error

    @db_tables: applicant_info, sessions

    @example:
        GET /api/applicant-info/12345

        Response:
        {
            "success": true,
            "applicant": {
                "user_code": "12345",
                "family_name": "Smith",
                "given_name": "John",
                "email": "john.smith@email.com",
                "birth_date": "1995-05-15",
                "citizenship": "Canada"
            }
        }
    """

    """Get detailed applicant information by user code"""
    from models.applicants import get_applicant_info_by_code

    applicant_info, error = get_applicant_info_by_code(user_code)

    if error:
        return jsonify({"success": False, "message": error})

    return jsonify({"success": True, "applicant": applicant_info})


@applicants_api.route("/applicant-test-scores/<user_code>", methods=["GET"])
def get_applicant_test_scores(user_code):
    """
    Get all standardized test scores for an applicant.

    Retrieves all test scores including TOEFL, IELTS, GRE, GMAT, Duolingo,
    and other English proficiency and graduate admission tests.

    @requires: Any authenticated user
    @method: GET
    @param user_code: Unique identifier for the applicant
    @param_type user_code: str

    @return: JSON response with all test scores
    @return_type: flask.Response
    @status_codes:
        - 200: Test scores retrieved successfully
        - 404: Applicant not found
        - 500: Database error

    @db_tables: toefl, ielts, gre, gmat, melab, pte, cael, celpip, duolingo, alt_elpp

    @example:
        GET /api/applicant-test-scores/12345

        Response:
        {
            "success": true,
            "test_scores": {
                "toefl": {"total": 105, "reading": 28, "listening": 26, "speaking": 25, "writing": 26},
                "ielts": null,
                "gre": {"verbal": 160, "quantitative": 165, "writing": 4.5}
            }
        }
    """

    """Get all test scores for a applicant by user code"""
    from models.applicants import get_applicant_test_scores_by_code

    test_scores, error = get_applicant_test_scores_by_code(user_code)

    if error:
        return jsonify({"success": False, "message": error})

    return jsonify({"success": True, "test_scores": test_scores})


@applicants_api.route("/applicant-institutions/<user_code>", methods=["GET"])
def get_applicant_institutions(user_code):
    """
    Get all institutional/academic history for an applicant.

    Retrieves information about all educational institutions attended by
    the applicant, including degrees, GPAs, and academic credentials.

    @requires: Any authenticated user
    @method: GET
    @param user_code: Unique identifier for the applicant
    @param_type user_code: str

    @return: JSON response with institutional history
    @return_type: flask.Response
    @status_codes:
        - 200: Institution data retrieved successfully
        - 404: Applicant not found
        - 500: Database error

    @db_tables: institution_info

    @example:
        GET /api/applicant-institutions/12345

        Response:
        {
            "success": true,
            "institutions": [
                {
                    "institution_number": 1,
                    "full_name": "University of Toronto",
                    "country": "Canada",
                    "degree_confer": "Bachelor of Science",
                    "program_study": "Computer Science",
                    "gpa": "3.8"
                }
            ]
        }
    """

    """Get all institution information for a applicant by user code"""
    from models.applicants import get_applicant_institutions_by_code

    institutions, error = get_applicant_institutions_by_code(user_code)

    if error:
        return jsonify({"success": False, "message": error})

    return jsonify({"success": True, "institutions": institutions})


@applicants_api.route("/applicant-application-info/<user_code>", methods=["GET"])
def get_applicant_application_info(user_code):
    """
    Get application-specific information and metadata.

    Retrieves application status, English proficiency data, prerequisite
    course information, GPA details, and other application metadata.

    @requires: Any authenticated user
    @method: GET
    @param user_code: Unique identifier for the applicant
    @param_type user_code: str

    @return: JSON response with application information
    @return_type: flask.Response
    @status_codes:
        - 200: Application info retrieved successfully
        - 404: Application not found
        - 500: Database error

    @db_tables: application_info

    @example:
        GET /api/applicant-application-info/12345

        Response:
        {
            "success": true,
            "application_info": {
                "sent": "Reviewed",
                "english_status": "Passed",
                "english_comment": "Strong English proficiency",
                "cs": "CPSC 110, CPSC 210",
                "stat": "STAT 251",
                "math": "MATH 100, MATH 101",
                "gpa": "3.85"
            }
        }
    """

    """Get application_info for a applicant by user code"""
    from models.applicants import get_applicant_application_info_by_code

    application_info, error = get_applicant_application_info_by_code(user_code)

    if error:
        return jsonify({"success": False, "message": error})

    return jsonify({"success": True, "application_info": application_info})


@applicants_api.route("/applicant-application-info/<user_code>/status", methods=["PUT"])
def update_applicant_status(user_code):
    """
    Update the application status for an applicant.

    Changes the application status (e.g., from "Not Reviewed" to "Reviewed",
    "Offer", "Declined", etc.). Only Admin users can modify application status.
    Activity is logged for audit purposes.

    @requires: Admin authentication
    @method: PUT
    @param user_code: Unique identifier for the applicant (URL parameter)
    @param_type user_code: str
    @param status: New application status (JSON body)
    @param_type status: str
    @valid_statuses: ["Not Reviewed", "Reviewed", "Waitlist", "Declined", "Offer", "CoGS", "Offer Sent"]

    @return: JSON response with operation result
    @return_type: flask.Response
    @status_codes:
        - 200: Status updated successfully
        - 400: Invalid status value or missing data
        - 403: Access denied (non-Admin user)
        - 500: Database error

    @logs: Activity logging with old and new status values
    @db_tables: application_info

    @example:
        PUT /api/applicant-application-info/12345/status
        Content-Type: application/json

        Request:
        {
            "status": "Offer"
        }

        Response:
        {
            "success": true,
            "message": "Status updated successfully"
        }
    """

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
    """
    Update prerequisite course and GPA information for an applicant.

    Updates the computer science, statistics, and mathematics prerequisite
    courses, as well as GPA information. Admin and Faculty users can modify
    course data, but only Admin can modify GPA.

    @requires: Admin or Faculty authentication (Viewer access denied)
    @method: PUT
    @param user_code: Unique identifier for the applicant (URL parameter)
    @param_type user_code: str
    @param cs: Computer Science courses (JSON body, max 1000 chars)
    @param_type cs: str
    @param stat: Statistics courses (JSON body, max 1000 chars)
    @param_type stat: str
    @param math: Mathematics courses (JSON body, max 1000 chars)
    @param_type math: str
    @param gpa: Overall GPA (JSON body, max 50 chars)
    @param_type gpa: str

    @return: JSON response with operation result
    @return_type: flask.Response
    @status_codes:
        - 200: Prerequisites updated successfully
        - 400: Invalid user code or request data
        - 403: Access denied (Viewer user)
        - 500: Database error

    @db_tables: application_info
    @validation: Input sanitization and length limits applied

    @example:
        PUT /api/applicant-application-info/12345/prerequisites
        Content-Type: application/json

        Request:
        {
            "cs": "CPSC 110 (A+), CPSC 210 (A)",
            "stat": "STAT 251 (B+)",
            "math": "MATH 100 (A), MATH 101 (A-)",
            "gpa": "3.85"
        }

        Response:
        {
            "success": true,
            "message": "Prerequisites updated successfully"
        }
    """

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


@applicants_api.route(
    "/applicant-application-info/<user_code>/english-comment", methods=["PUT"]
)
def update_english_comment(user_code):
    """
    Update English proficiency comments for an applicant.

    Allows modification of English proficiency assessment comments.
    Based on updated permissions, only Admin users can edit these comments.

    @requires: Admin authentication (Faculty and Viewer access denied)
    @method: PUT
    @param user_code: Unique identifier for the applicant (URL parameter)
    @param_type user_code: str
    @param english_comment: English proficiency comment (JSON body, max 2000 chars)
    @param_type english_comment: str

    @return: JSON response with operation result
    @return_type: flask.Response
    @status_codes:
        - 200: Comment updated successfully
        - 400: Invalid user code or request data
        - 403: Access denied (non-Admin user)
        - 500: Database error

    @db_tables: application_info
    @validation: Input sanitization and 2000 character limit

    @example:
        PUT /api/applicant-application-info/12345/english-comment
        Content-Type: application/json

        Request:
        {
            "english_comment": "Excellent English proficiency demonstrated through TOEFL scores and academic writing samples."
        }

        Response:
        {
            "success": true,
            "message": "English comment updated successfully"
        }
    """

    """Update English comment for applicant (Admin only)"""
    if (
        not current_user.is_authenticated
        or current_user.is_viewer
        or current_user.is_faculty
    ):
        return jsonify({"success": False, "message": "Access denied"}), 403

    from models.applicants import update_english_comment

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Invalid request data"}), 400

    # Validate user_code format
    if not user_code or not user_code.strip():
        return jsonify({"success": False, "message": "Invalid user code"}), 400

    # Sanitize comment input and limit length
    english_comment = str(data.get("english_comment", "")).strip()[
        :2000
    ]  # Limit to 2000 chars

    success, message = update_english_comment(user_code, english_comment)

    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400


@applicants_api.route(
    "/applicant-application-info/<user_code>/english-status", methods=["PUT"]
)
def update_english_status(user_code):
    """
    Update English proficiency status for an applicant.

    Changes the English language requirement status. Based on updated
    permissions, only Admin users can modify English status.

    @requires: Admin authentication (Faculty and Viewer access denied)
    @method: PUT
    @param user_code: Unique identifier for the applicant (URL parameter)
    @param_type user_code: str
    @param english_status: New English status (JSON body)
    @param_type english_status: str
    @valid_statuses: ["Not Met", "Not Required", "Passed"]

    @return: JSON response with operation result
    @return_type: flask.Response
    @status_codes:
        - 200: Status updated successfully
        - 400: Invalid status value or missing data
        - 403: Access denied (non-Admin user)
        - 500: Database error

    @db_tables: application_info

    @example:
        PUT /api/applicant-application-info/12345/english-status
        Content-Type: application/json

        Request:
        {
            "english_status": "Passed"
        }

        Response:
        {
            "success": true,
            "message": "English status updated successfully"
        }
    """

    """Update English status for applicant (Admin only)"""
    if (
        not current_user.is_authenticated
        or current_user.is_viewer
        or current_user.is_faculty
    ):
        return jsonify({"success": False, "message": "Access denied"}), 403

    from models.applicants import update_english_status

    data = request.get_json()
    english_status = data.get("english_status")

    if not english_status:
        return jsonify({"success": False, "message": "English status is required"}), 400

    # Validate status values
    valid_statuses = ["Not Met", "Not Required", "Passed"]
    if english_status not in valid_statuses:
        return (
            jsonify({"success": False, "message": "Invalid English status value"}),
            400,
        )

    success, message = update_english_status(user_code, english_status)

    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400
