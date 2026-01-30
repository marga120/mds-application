"""
Documents API Blueprint

This module provides REST API endpoints for managing applicant documents (PDFs).
"""

import os
import uuid
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models.documents import (
    get_documents_by_user_code,
    get_document_by_id,
    save_document,
    delete_document,
    get_document_count_by_user_code,
)
from utils.activity_logger import log_activity
from utils.permissions import require_admin, require_faculty_or_admin

documents_bp = Blueprint('documents', __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

# Document type options
DOCUMENT_TYPES = [
    'transcript',
    'recommendation_letter',
    'cv_resume',
    'statement_of_purpose',
    'other'
]


def allowed_file(filename):
    """Check if file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_upload_folder():
    """Get the upload folder path from app config."""
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads/documents')
    # Ensure the directory exists
    os.makedirs(upload_folder, exist_ok=True)
    return upload_folder


def generate_unique_filename(original_filename):
    """Generate a unique filename to prevent collisions."""
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'pdf'
    unique_id = str(uuid.uuid4())[:8]
    secure_name = secure_filename(original_filename)
    name_part = secure_name.rsplit('.', 1)[0] if '.' in secure_name else secure_name
    return f"{name_part}_{unique_id}.{ext}"


@documents_bp.route('/api/documents/<user_code>', methods=['GET'])
@login_required
def list_documents(user_code):
    """
    List all documents for an applicant.

    @param user_code: Applicant's user code
    @return: JSON response with documents list
    """
    documents, error = get_documents_by_user_code(user_code)

    if error:
        return jsonify({'success': False, 'message': error}), 500

    # Convert datetime objects to strings for JSON serialization
    docs_list = []
    for doc in documents:
        doc_dict = dict(doc)
        if doc_dict.get('created_at'):
            doc_dict['created_at'] = doc_dict['created_at'].isoformat()
        if doc_dict.get('updated_at'):
            doc_dict['updated_at'] = doc_dict['updated_at'].isoformat()
        docs_list.append(doc_dict)

    return jsonify({
        'success': True,
        'documents': docs_list,
        'count': len(docs_list)
    })


@documents_bp.route('/api/documents/<user_code>', methods=['POST'])
@require_faculty_or_admin
def upload_document(user_code):
    """
    Upload a new document for an applicant.

    @param user_code: Applicant's user code
    @return: JSON response with upload status
    """
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'message': 'Invalid file type. Only PDF files are allowed.'
        }), 400

    # Get document metadata from form
    document_type = request.form.get('document_type', 'other')
    if document_type not in DOCUMENT_TYPES:
        document_type = 'other'

    description = request.form.get('description', '')

    try:
        # Generate unique filename and save file
        original_filename = file.filename
        filename = generate_unique_filename(original_filename)
        upload_folder = get_upload_folder()
        file_path = os.path.join(upload_folder, filename)

        file.save(file_path)

        # Get file size
        file_size = os.path.getsize(file_path)

        # Save document record to database
        document_id, error = save_document(
            user_code=user_code,
            document_type=document_type,
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type='application/pdf',
            uploaded_by=current_user.id,
            description=description
        )

        if error:
            # Clean up the file if database insert failed
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'success': False, 'message': error}), 500

        # Log the activity
        log_activity(
            user_id=current_user.id,
            action_type='document_upload',
            target_entity='applicant_documents',
            target_id=user_code,
            new_value=f"{document_type}: {original_filename}"
        )

        return jsonify({
            'success': True,
            'message': 'Document uploaded successfully',
            'document_id': document_id,
            'filename': filename
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Upload failed: {str(e)}'
        }), 500


@documents_bp.route('/api/documents/view/<int:document_id>', methods=['GET'])
@login_required
def view_document(document_id):
    """
    View/download a document.

    @param document_id: Document ID
    @return: File response or JSON error
    """
    document, error = get_document_by_id(document_id)

    if error:
        return jsonify({'success': False, 'message': error}), 500

    if not document:
        return jsonify({'success': False, 'message': 'Document not found'}), 404

    file_path = document['file_path']

    if not os.path.exists(file_path):
        return jsonify({
            'success': False,
            'message': 'File not found on server'
        }), 404

    # Send file for viewing (inline) or downloading
    download = request.args.get('download', 'false').lower() == 'true'

    return send_file(
        file_path,
        mimetype=document['mime_type'] or 'application/pdf',
        as_attachment=download,
        download_name=document['original_filename']
    )


@documents_bp.route('/api/documents/<int:document_id>', methods=['DELETE'])
@require_admin
def delete_document_endpoint(document_id):
    """
    Delete a document.

    @param document_id: Document ID
    @return: JSON response with deletion status
    """
    # Get document info first
    document, error = get_document_by_id(document_id)

    if error:
        return jsonify({'success': False, 'message': error}), 500

    if not document:
        return jsonify({'success': False, 'message': 'Document not found'}), 404

    # Delete from database
    deleted_doc, error = delete_document(document_id)

    if error:
        return jsonify({'success': False, 'message': error}), 500

    # Delete the file from disk
    file_path = document['file_path']
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            # Log but don't fail - DB record is already deleted
            print(f"Warning: Could not delete file {file_path}: {e}")

    # Log the activity
    log_activity(
        user_id=current_user.id,
        action_type='document_delete',
        target_entity='applicant_documents',
        target_id=document['user_code'],
        old_value=f"{document['document_type']}: {document['original_filename']}"
    )

    return jsonify({
        'success': True,
        'message': 'Document deleted successfully'
    })


@documents_bp.route('/api/documents/count/<user_code>', methods=['GET'])
@login_required
def get_document_count(user_code):
    """
    Get document count for an applicant.

    @param user_code: Applicant's user code
    @return: JSON response with count
    """
    count, error = get_document_count_by_user_code(user_code)

    if error:
        return jsonify({'success': False, 'message': error}), 500

    return jsonify({
        'success': True,
        'count': count
    })


@documents_bp.route('/api/documents/types', methods=['GET'])
@login_required
def get_document_types():
    """
    Get available document types.

    @return: JSON response with document types list
    """
    types_with_labels = [
        {'value': 'transcript', 'label': 'Transcript'},
        {'value': 'recommendation_letter', 'label': 'Recommendation Letter'},
        {'value': 'cv_resume', 'label': 'CV/Resume'},
        {'value': 'statement_of_purpose', 'label': 'Statement of Purpose'},
        {'value': 'other', 'label': 'Other'},
    ]

    return jsonify({
        'success': True,
        'types': types_with_labels
    })
