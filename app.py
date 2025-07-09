from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import io
from datetime import datetime, timezone

# Import our database functions
from utils.database import init_database
from models.students import (
    upsert_students,
    get_all_students,
    update_student,
    delete_student,
    get_upload_history,
)

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    """Serve the main HTML page"""
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
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
        # Get upload timestamp from request or use current time
        upload_timestamp_str = request.form.get("upload_timestamp")
        if upload_timestamp_str:
            try:
                upload_timestamp = datetime.fromisoformat(
                    upload_timestamp_str.replace("Z", "+00:00")
                )
            except:
                upload_timestamp = datetime.now()
        else:
            upload_timestamp = datetime.now()

        # Ensure timestamp is timezone-aware
        if upload_timestamp.tzinfo is None:
            upload_timestamp = upload_timestamp.replace(tzinfo=timezone.utc)

        # Read CSV file
        csv_data = file.read().decode("utf-8")
        df = pd.read_csv(io.StringIO(csv_data))

        # Validate required columns
        required_columns = [
            "student_id",
            "student_name",
            "university",
            "year",
            "degree",
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            return jsonify(
                {
                    "success": False,
                    "message": f'Missing required columns: {", ".join(missing_columns)}',
                }
            )

        # Clean and validate data
        df = df.dropna()  # Remove rows with missing values
        df["student_id"] = df["student_id"].astype(str)
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
        df = df.dropna()  # Remove rows where year conversion failed

        if df.empty:
            return jsonify({"success": False, "message": "No valid data found in CSV"})

        # Use the model function to upsert data
        success, message, records_processed = upsert_students(df, upload_timestamp)

        if success:
            return jsonify(
                {
                    "success": True,
                    "message": message,
                    "records_processed": records_processed,
                    "upload_timestamp": upload_timestamp.isoformat(),
                    "processed_at": datetime.now().isoformat(),
                }
            )
        else:
            return jsonify({"success": False, "message": message})

    except Exception as e:
        return jsonify(
            {"success": False, "message": f"Error processing file: {str(e)}"}
        )


@app.route("/api/students", methods=["GET"])
def get_students():
    """Get all students from database"""
    students, error = get_all_students()

    if error:
        return jsonify({"success": False, "message": error})

    return jsonify({"success": True, "students": students})


@app.route("/api/students/<student_id>", methods=["PUT"])
def update_student_route(student_id):
    """Update a specific student record"""
    data = request.get_json()
    success, message = update_student(student_id, data)
    return jsonify({"success": success, "message": message})


@app.route("/api/students/<student_id>", methods=["DELETE"])
def delete_student_route(student_id):
    """Delete a specific student"""
    success, message = delete_student(student_id)
    return jsonify({"success": success, "message": message})


@app.route("/api/upload-history", methods=["GET"])
def get_upload_history_route():
    """Get upload history with timestamps"""
    history, error = get_upload_history()

    if error:
        return jsonify({"success": False, "message": error})

    return jsonify({"success": True, "history": history})


if __name__ == "__main__":
    init_database()
    app.run(debug=True)
