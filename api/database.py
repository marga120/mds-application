"""
DATABASE BACKUP AND IMPORT API

This module handles database backup and import operations for the MDS Application
Management System. It provides endpoints for exporting the database to SQL files
and importing SQL files back into the database. Admin-only access is enforced
for all operations to maintain data integrity and security.
"""

from flask import Blueprint, jsonify, request, send_file
from flask_login import login_required, current_user
import psycopg2
import os
import subprocess
from datetime import datetime
from utils.database import DB_CONFIG
from utils.activity_logger import log_activity

database_api = Blueprint("database_api", __name__)


def admin_required(f):
    """Decorator to require admin role"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({"success": False, "message": "Admin access required"}), 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@database_api.route("/backup-database", methods=["POST"])
@login_required
@admin_required
def backup_database():
    """
    Backup the entire database to a SQL file
    Admin only - Creates a timestamped backup file and returns it for download
    """
    try:
        # Create backups directory if it doesn't exist
        backup_dir = os.path.join(os.getcwd(), "backups")
        os.makedirs(backup_dir, exist_ok=True)

        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"mds_backup_{timestamp}.sql"
        backup_path = os.path.join(backup_dir, backup_filename)

        # Set up environment variable for password
        env = os.environ.copy()
        env['PGPASSWORD'] = DB_CONFIG['password']

        # Build pg_dump command
        pg_dump_cmd = [
            'pg_dump',
            '-h', DB_CONFIG['host'],
            '-p', str(DB_CONFIG['port']),
            '-U', DB_CONFIG['user'],
            '-d', DB_CONFIG['database'],
            '-F', 'p',  # Plain text SQL format
            '-f', backup_path,
            '--no-owner',  # Don't include ownership commands
            '--no-privileges',  # Don't include privilege commands
            '--clean',  # Include DROP statements before CREATE
            '--if-exists'  # Use IF EXISTS with DROP statements
        ]

        # Execute pg_dump
        result = subprocess.run(
            pg_dump_cmd,
            env=env,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            error_msg = result.stderr or "Unknown error during backup"
            log_activity(
                current_user.user_id,
                "database_backup_failed",
                f"Database backup failed: {error_msg}"
            )
            return jsonify({
                "success": False,
                "message": f"Backup failed: {error_msg}"
            }), 500

        # Log successful backup
        log_activity(
            current_user.id,
            "database_backup",
            f"Database backed up to {backup_filename}"
        )

        # Return the file for download
        return send_file(
            backup_path,
            as_attachment=True,
            download_name=backup_filename,
            mimetype='application/sql'
        )

    except FileNotFoundError:
        return jsonify({
            "success": False,
            "message": "pg_dump not found. Please ensure PostgreSQL client tools are installed."
        }), 500
    except Exception as e:
        log_activity(
            current_user.id,
            "database_backup_error",
            f"Database backup error: {str(e)}"
        )
        return jsonify({
            "success": False,
            "message": f"Backup error: {str(e)}"
        }), 500


@database_api.route("/import-database", methods=["POST"])
@login_required
@admin_required
def import_database():
    """
    Import a database from a SQL file
    Admin only - Restores database from uploaded SQL file
    WARNING: This will replace existing data
    """
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "message": "No file uploaded"
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                "success": False,
                "message": "No file selected"
            }), 400

        # Validate file extension
        if not file.filename.endswith('.sql'):
            return jsonify({
                "success": False,
                "message": "Invalid file type. Please upload a .sql file"
            }), 400

        # Save uploaded file temporarily
        temp_dir = os.path.join(os.getcwd(), "temp")
        os.makedirs(temp_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_filename = f"import_{timestamp}.sql"
        temp_path = os.path.join(temp_dir, temp_filename)

        file.save(temp_path)

        # Set up environment variable for password
        env = os.environ.copy()
        env['PGPASSWORD'] = DB_CONFIG['password']

        # Build psql command to import the database
        psql_cmd = [
            'psql',
            '-h', DB_CONFIG['host'],
            '-p', str(DB_CONFIG['port']),
            '-U', DB_CONFIG['user'],
            '-d', DB_CONFIG['database'],
            '-v', 'ON_ERROR_STOP=0',  # Don't stop on errors (allows duplicate constraint warnings)
            '-f', temp_path,
            '--single-transaction'  # Wrap entire import in a single transaction
        ]

        # Execute psql import
        result = subprocess.run(
            psql_cmd,
            env=env,
            capture_output=True,
            text=True
        )

        # Clean up temporary file
        try:
            os.remove(temp_path)
        except:
            pass

        # Check for critical errors (not just warnings about duplicate constraints)
        if result.returncode != 0:
            error_msg = result.stderr or "Unknown error during import"
            # Filter out duplicate constraint warnings
            if "already exists" not in error_msg.lower() and "duplicate" not in error_msg.lower():
                log_activity(
                    current_user.id,
                    "database_import_failed",
                    f"Database import failed: {error_msg}"
                )
                return jsonify({
                    "success": False,
                    "message": f"Import failed: {error_msg}"
                }), 500

        if result.stderr and result.stderr.strip():
            print(f"Import warnings: {result.stderr.strip()}")

        # Ensure transaction is committed by creating a new connection and verifying data
        try:
            import time
            time.sleep(0.5)  # Brief pause to ensure transaction is fully committed

            # Verify import by checking if applicant_info has data
            verify_conn = psycopg2.connect(**DB_CONFIG)
            verify_cursor = verify_conn.cursor()
            verify_cursor.execute("SELECT COUNT(*) FROM applicant_info")
            count = verify_cursor.fetchone()[0]
            verify_cursor.close()
            verify_conn.close()

            if count == 0:
                raise Exception("No applicant data found after import")
        except Exception as verify_error:
            log_activity(
                current_user.id,
                "database_import_verification_failed",
                f"Import verification failed: {str(verify_error)}"
            )
            return jsonify({
                "success": False,
                "message": f"Import verification failed: {str(verify_error)}"
            }), 500

        # Log successful import
        log_activity(
            current_user.id,
            "database_import",
            f"Database imported from {file.filename}"
        )

        return jsonify({
            "success": True,
            "message": "Database imported successfully"
        })

    except FileNotFoundError:
        return jsonify({
            "success": False,
            "message": "psql not found. Please ensure PostgreSQL client tools are installed."
        }), 500
    except Exception as e:
        log_activity(
            current_user.id,
            "database_import_error",
            f"Database import error: {str(e)}"
        )
        return jsonify({
            "success": False,
            "message": f"Import error: {str(e)}"
        }), 500
