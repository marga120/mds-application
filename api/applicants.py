from flask import Blueprint, make_response, request, jsonify
import pandas as pd
import io
from datetime import datetime, timezone
from flask_login import current_user, login_required
from utils.activity_logger import log_activity
from utils.permissions import require_admin, require_faculty_or_admin
import csv

# Import our model functions
from models.applicants import process_csv_data, get_all_applicant_status, clear_all_applicant_data

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
    @query_params:
        - session_id: Optional session ID to filter applicants by session

    @return: JSON response containing list of all applicants
    @return_type: flask.Response
    @status_codes:
        - 200: Applicants retrieved successfully
        - 500: Database error

    @db_tables: applicant_status, applicant_info, ratings

    @example:
        GET /api/applicants?session_id=5

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

    """Get all applicants from database, optionally filtered by session"""
    session_id = request.args.get('session_id', type=int)
    applicants, error = get_all_applicant_status(session_id=session_id)

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

    Changes the application status (e.g., from "Not Reviewed" to "Reviewed by PPA",
    "Send Offer to CoGS", "Declined", etc.). Only Admin users can modify application status.
    Activity is logged for audit purposes.

    @requires: Admin authentication
    @method: PUT
    @param user_code: Unique identifier for the applicant (URL parameter)
    @param_type user_code: str
    @param status: New application status (JSON body)
    @param_type status: str
    @valid_statuses: ["Not Reviewed", "Reviewed", "Waitlist", "Declined", "Send Offer to CoGS", "Offer Sent to CoGS", "Offer Sent to Student", "Offer Accepted", "Offer Declined", "Deferred"]

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
            "status": "Send Offer to CoGS"
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

    from models.statuses import get_all_statuses
    valid_statuses, error = get_all_statuses()
    
    if error or not valid_statuses:
        return jsonify({"success": False, "message": "Failed to validate status"}), 500
    
    valid_status_names = [s['status_name'] for s in valid_statuses]
    
    if status not in valid_status_names:
        return jsonify({"success": False, "message": f"Invalid status value. Must be one of: {', '.join(valid_status_names)}"}), 400

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
    additional_comments = str(data.get("additional_comments", "")).strip()[:2000]

    # Handle GPA - accept as string input
    gpa = data.get("gpa", "")
    if gpa and gpa != "":
        # Accept any string input, just limit length for database storage
        gpa = str(gpa).strip()[:50]  # Limit to 50 characters
    else:
        gpa = None

    # Handle MDS fields
    mds_v = data.get("mds_v")
    mds_cl = data.get("mds_cl")
    mds_o = data.get("mds_o")

    success, message = update_applicant_prerequisites(user_code, cs, stat, math, gpa, additional_comments, mds_v, mds_cl, mds_o)

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
    ###Changed
def _write_single_applicant_csv_sections(writer, applicant_data, sections=None):
    """
    Helper function to write the multi-section CSV report for one applicant (Vertical Format).
    This logic is shared by the single applicant export endpoint.
    """
    
    basic_info = applicant_data.get('basic', {})
    name = f"{basic_info.get('given_name', '')} {basic_info.get('family_name', '')}"
    user_code = basic_info.get('user_code', 'UNKNOWN')
    
    # Add a main header for the applicant
    writer.writerow([f"Applicant Report for: {name}", f"User Code: {user_code}"])
    writer.writerow([]) # Spacer

    # Ratings & Comments section
    if not sections or 'ratings' in sections:
        writer.writerow(['Ratings & Comments'])
        writer.writerow(['Applicant', 'Reviewer', 'Rating', 'Comment', 'Date'])
        for rating in (applicant_data.get('ratings') or []):
            writer.writerow([
                name,
                f"{rating.get('first_name', '')} {rating.get('last_name', '')}",
                rating.get('rating'),
                rating.get('user_comment') or '',
                rating['created_at'].strftime('%Y-%m-%d %H:%M') if rating.get('created_at') else ''
            ])
        writer.writerow([]) # Spacer

    # Personal Information section
    if not sections or 'personal' in sections:
        writer.writerow(['Personal Information'])
        personal = applicant_data.get('personal', {})
        if personal:
            for key, value in personal.items():
                if value and key not in ['user_code']: # Skip user_code
                    writer.writerow([key.replace('_', ' ').title(), value])
        writer.writerow([]) # Spacer

    # Prerequisites section
    if not sections or 'prerequisites' in sections:
        writer.writerow(['Prerequisites & GPA'])
        prereq = applicant_data.get('prerequisites', {})
        if prereq:
            writer.writerow(['Computer Science', prereq.get('cs', '')])
            writer.writerow(['Statistics', prereq.get('stat', '')])
            writer.writerow(['Mathematics', prereq.get('math', '')])
            writer.writerow(['GPA', prereq.get('gpa', '')])
        writer.writerow([]) # Spacer

    # Test Scores section
    if not sections or 'test_scores' in sections:
        writer.writerow(['Test Scores'])
        test_scores = applicant_data.get('test_scores', {})
        for idx, toefl in enumerate(test_scores.get('toefl', []) or [], 1):
            writer.writerow([
                f'TOEFL {idx}', 
                f"Total: {toefl.get('total_score', '')}, " +
                f"Reading: {toefl.get('reading', '')}, " +
                f"Listening: {toefl.get('listening', '')}, " +
                f"Speaking: {toefl.get('speaking', '')}, " +
                f"Writing: {toefl.get('structure_written', '')}"
            ])
        # Note: Add logic for other test types (IELTS, etc.) here if present
        writer.writerow([]) # Spacer

    # Institutions section
    if not sections or 'institutions' in sections:
        writer.writerow(['Educational Background'])
        writer.writerow(['Institution', 'Degree', 'Program', 'GPA', 'Start Date', 'End Date'])
        for inst in (applicant_data.get('institutions') or []):
            writer.writerow([
                inst.get('full_name', ''),
                inst.get('credential_receive', ''),
                inst.get('program_study', ''),
                inst.get('gpa', ''),
                inst.get('start_date', ''),
                inst.get('end_date', '')
            ])
        writer.writerow([]) # Spacer
    
    # Add a separator for the next applicant
    writer.writerow(['='*20, '='*20, '='*20])
    writer.writerow([])

@applicants_api.route("/export/all", methods=["GET"])
def export_all_applicants():
    """
    Export all applicants with complete data from all tables.

    This endpoint retrieves absolutely every piece of information for every applicant
    in the database, including demographics, test scores, institutions, ratings, etc.
    It generates a comprehensive CSV file with 100+ columns.

    @requires: Admin or Faculty authentication (Viewer access denied)
    @method: GET

    @return: CSV file download with all applicant data
    @return_type: flask.Response (text/csv)
    @status_codes:
        - 200: CSV file generated successfully
        - 403: Access denied (Viewer user)
        - 404: No applicants found in database
        - 500: Database or export error

    @db_tables: All applicant-related tables (18+ tables)
    @performance: This is an expensive operation - use sparingly
    @logs: Activity logging with record count

    @example:
        GET /api/export/all

        Response: CSV file download
        Filename: complete_export_150_applicants_2026-01-09.csv
    """
    if not current_user.is_authenticated or current_user.is_viewer:
        return jsonify({"success": False, "message": "Access denied"}), 403

    try:
        from models.applicants import get_all_applicants_complete_export

        # Call the model function to get all data
        applicants, error = get_all_applicants_complete_export()

        if error:
            return jsonify({"success": False, "message": error}), 500

        if not applicants or len(applicants) == 0:
            return jsonify({"success": False, "message": "No applicants found in database"}), 404

        # Create CSV output
        output = io.StringIO()

        # Get headers from the first applicant's keys
        headers = list(applicants[0].keys())
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()

        # Helper function to clean None/NaN values
        def clean_row(row):
            """Convert None, NaN, and null values to empty strings for CSV export."""
            cleaned = {}
            for k, v in row.items():
                # Handle None
                if v is None:
                    cleaned[k] = ''
                # Handle string 'nan', 'NaN', 'none', 'null'
                elif isinstance(v, str) and v.lower() in ['nan', 'none', 'null', '']:
                    cleaned[k] = ''
                # Handle float NaN
                elif isinstance(v, float):
                    import math
                    if math.isnan(v):
                        cleaned[k] = ''
                    else:
                        cleaned[k] = v
                else:
                    cleaned[k] = v
            return cleaned

        # Write all applicants to CSV
        for applicant in applicants:
            writer.writerow(clean_row(applicant))

        # Log the activity
        log_activity(
            action_type="export",
            target_entity="all_applicants",
            target_id="complete_database",
            additional_metadata={
                "record_count": len(applicants),
                "export_type": "complete_database_export",
                "exported_by": current_user.email
            }
        )

        # Prepare response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'

        # Generate filename with timestamp and count
        filename = f'complete_export_{len(applicants)}_applicants_{datetime.now().strftime("%Y-%m-%d")}.csv'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'

        return response

    except Exception as e:
        print(f"Export all error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Export failed: {str(e)}"}), 500

@applicants_api.route("/export/selected", methods=["POST"])
def export_selected_applicants():
    """Export multiple selected applicants (horizontal, one row per applicant)."""
    
    if not current_user.is_authenticated or current_user.is_viewer:
        return jsonify({"success": False, "message": "Access denied"}), 403

    try:
        from models.applicants import get_selected_applicants_for_export
        
        data = request.get_json()
        user_codes = data.get('user_codes', [])
        sections = data.get('sections', None)
        
        if not user_codes:
            return jsonify({"success": False, "message": "No applicants selected"}), 400
        
        applicants, error = get_selected_applicants_for_export(user_codes, sections)
        
        if error:
            return jsonify({"success": False, "message": error}), 500

        if not applicants:
            return jsonify({"success": False, "message": "No applicant data found for selected users"}), 404

        # Create CSV with dynamic headers based on sections
        output = io.StringIO()
        
        # Use DictWriter. The keys of the dictionary (from SQL aliases) become the headers.
        headers = list(applicants[0].keys())
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        
        # Helper to clean None/NaN values -> Empty String for CSV
        def clean_row(row):
            cleaned = {}
            for k, v in row.items():
                # Handle None
                if v is None:
                    cleaned[k] = ''
                # Handle string 'nan', 'NaN', 'none', 'null', 'None', 'NULL'
                elif isinstance(v, str) and v.lower() in ['nan', 'none', 'null', '']:
                    cleaned[k] = ''
                # Handle float NaN (from pandas or numpy)
                elif isinstance(v, float):
                    import math
                    if math.isnan(v):
                        cleaned[k] = ''
                    else:
                        cleaned[k] = v
                else:
                    cleaned[k] = v
            return cleaned

        for applicant in applicants:
            writer.writerow(clean_row(applicant))
        
        log_activity(
            action_type="export",
            target_entity="selected_applicants",
            target_id=None,
            additional_metadata={
                "record_count": len(applicants),
                "user_codes": user_codes,
                "sections": sections or "all",
                "export_style": "horizontal_dynamic_pivoted"
            }
        )
        
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        
        sections_str = '_'.join(sections) if sections else 'all'
        filename = f'selected_{len(user_codes)}_{sections_str}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
        
    except Exception as e:
        print(f"Export error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Export failed: {str(e)}"}), 500

@applicants_api.route("/clear-all-data", methods=["DELETE"])
@login_required
def clear_all_data():
    """
    Clear all applicant data from the database (Admin only).
    
    Deletes all records from applicant-related tables while preserving
    the table structure. This is a destructive operation that cannot be undone.
    
    @requires: Admin authentication
    @method: DELETE
    
    @return: JSON response with operation result
    @return_type: flask.Response
    @status_codes:
        - 200: Data cleared successfully
        - 403: Access denied (non-Admin user)
        - 500: Database error
    
    @logs: Activity logging for data deletion action
    """
    # Only Admin can clear all data
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({"success": False, "message": "Access denied. Admin privileges required."}), 403
    
    # Call the model function to do the actual work
    success, message, tables_cleared, records_cleared = clear_all_applicant_data()
    
    if success:
        # Log the action
        log_activity(
            action_type="clear_all_data",
            target_entity="database",
            target_id="all_applicant_tables",
            old_value=f"{records_cleared} records",
            new_value="0 records",
            additional_metadata={
                "tables_cleared": tables_cleared,
                "records_cleared": records_cleared,
                "admin_user": current_user.email
            }
        )
        
        return jsonify({
            "success": True,
            "message": message,
            "tables_cleared": tables_cleared
        }), 200
    else:
        return jsonify({
            "success": False,
            "message": message
        }), 500

@applicants_api.route("/applicant-application-info/<user_code>/scholarship", methods=["PUT"])
@require_admin
def update_applicant_scholarship_endpoint(user_code):
    """
    Update applicant scholarship decision.

    Updates the scholarship offer decision for a specific applicant.
    Only Admin users can update scholarship decisions.

    @requires: Admin authentication (Faculty and Viewer access denied)
    @method: PUT
    @param user_code: Unique identifier for the applicant (URL parameter)
    @param_type user_code: str
    @param scholarship: Scholarship decision (JSON body: "Yes", "No", or "Undecided")
    @param_type scholarship: str

    @return: JSON response with operation result
    @return_type: flask.Response
    @status_codes:
        - 200: Scholarship decision updated successfully
        - 400: Invalid scholarship value or request data
        - 401: Authentication required
        - 403: Access denied (non-Admin user)
        - 404: Applicant not found
        - 500: Database error

    @validation: Scholarship must be "Yes", "No", or "Undecided"
    @db_tables: application_info
    @upsert: Updates existing record or creates new one

    @example:
        PUT /api/applicant-application-info/12345/scholarship
        Content-Type: application/json

        Request:
        {
            "scholarship": "Yes"
        }

        Response:
        {
            "success": true,
            "message": "Scholarship decision updated successfully"
        }
    """
    from models.applicants import update_applicant_scholarship

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Invalid request data"}), 400

    scholarship = data.get("scholarship", "Undecided")
    
    # Validate scholarship value
    if scholarship not in ["Yes", "No", "Undecided"]:
        return jsonify({"success": False, "message": "Invalid scholarship value"}), 400

    success, message = update_applicant_scholarship(user_code, scholarship)

    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400