"""
Documents API — HTTP only.
All business logic delegated to DocumentService.
File serving (send_file) stays here as an HTTP concern.
"""

from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from utils.permissions import require_admin, require_faculty_or_admin
from services.document_service import DocumentService

documents_bp = Blueprint("documents", __name__)
_service = DocumentService()

DOCUMENT_TYPES_WITH_LABELS = [
    {"value": "transcript", "label": "Transcript"},
    {"value": "recommendation_letter", "label": "Recommendation Letter"},
    {"value": "cv_resume", "label": "CV/Resume"},
    {"value": "statement_of_purpose", "label": "Statement of Purpose"},
    {"value": "other", "label": "Other"},
]


def _upload_folder():
    folder = current_app.config.get("UPLOAD_FOLDER", "uploads/documents")
    return folder


@documents_bp.route("/api/documents/<user_code>", methods=["GET"])
@login_required
def list_documents(user_code):
    """List all documents for an applicant."""
    try:
        docs = _service.get_documents(user_code)
        return jsonify({"success": True, "documents": docs, "count": len(docs)})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@documents_bp.route("/api/documents/<user_code>", methods=["POST"])
@require_faculty_or_admin
def upload_document(user_code):
    """Upload a new document for an applicant."""
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file provided"}), 400
    try:
        result = _service.upload_document(
            user_code=user_code,
            file=request.files["file"],
            document_type=request.form.get("document_type", "other"),
            description=request.form.get("description", ""),
            uploader_id=current_user.id,
            upload_folder=_upload_folder(),
        )
        return jsonify({"success": True, "message": "Document uploaded successfully", **result})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Upload failed: {str(e)}"}), 500


@documents_bp.route("/api/documents/view/<int:document_id>", methods=["GET"])
@login_required
def view_document(document_id):
    """View/download a document."""
    try:
        file_path, original_filename, mime_type = _service.get_download_info(document_id)
        download = request.args.get("download", "false").lower() == "true"
        return send_file(file_path, mimetype=mime_type, as_attachment=download, download_name=original_filename)
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@documents_bp.route("/api/documents/<int:document_id>", methods=["DELETE"])
@require_admin
def delete_document_endpoint(document_id):
    """Delete a document (Admin only)."""
    try:
        message = _service.delete_document(document_id, current_user)
        return jsonify({"success": True, "message": message})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@documents_bp.route("/api/documents/count/<user_code>", methods=["GET"])
@login_required
def get_document_count(user_code):
    """Get document count for an applicant."""
    try:
        return jsonify({"success": True, "count": _service.get_count(user_code)})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@documents_bp.route("/api/documents/types", methods=["GET"])
@login_required
def get_document_types():
    """Get available document types."""
    return jsonify({"success": True, "types": DOCUMENT_TYPES_WITH_LABELS})
