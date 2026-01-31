"""
Documents Model

This module handles database operations for applicant documents (PDFs).
"""

from datetime import datetime
from utils.db_helpers import db_connection, db_transaction


def get_documents_by_user_code(user_code):
    """
    Get all documents for an applicant.

    @param user_code: Unique identifier for the applicant
    @return: Tuple of (documents_list, error_message)
    """
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT
                    d.id,
                    d.user_code,
                    d.document_type,
                    d.filename,
                    d.original_filename,
                    d.file_path,
                    d.file_size,
                    d.mime_type,
                    d.uploaded_by,
                    d.description,
                    d.created_at,
                    d.updated_at,
                    u.first_name || ' ' || u.last_name as uploaded_by_name
                FROM applicant_documents d
                LEFT JOIN "user" u ON d.uploaded_by = u.id
                WHERE d.user_code = %s
                ORDER BY d.created_at DESC
            """, (user_code,))
            return cursor.fetchall(), None

    except Exception as e:
        return None, f"Database error: {str(e)}"


def get_document_by_id(document_id):
    """
    Get a single document by its ID.

    @param document_id: Document ID
    @return: Tuple of (document_dict, error_message)
    """
    try:
        with db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT
                    id, user_code, document_type, filename, original_filename,
                    file_path, file_size, mime_type, uploaded_by, description,
                    created_at, updated_at
                FROM applicant_documents
                WHERE id = %s
            """, (document_id,))
            return cursor.fetchone(), None

    except Exception as e:
        return None, f"Database error: {str(e)}"


def save_document(user_code, document_type, filename, original_filename,
                  file_path, file_size, mime_type, uploaded_by, description=None):
    """
    Save a new document record.

    @param user_code: Applicant user code
    @param document_type: Type of document (e.g., 'transcript', 'recommendation')
    @param filename: Stored filename
    @param original_filename: Original uploaded filename
    @param file_path: Full path to stored file
    @param file_size: Size in bytes
    @param mime_type: MIME type (e.g., 'application/pdf')
    @param uploaded_by: User ID of uploader
    @param description: Optional description
    @return: Tuple of (document_id, error_message)
    """
    try:
        with db_transaction() as (conn, cursor):
            current_time = datetime.now()

            cursor.execute("""
                INSERT INTO applicant_documents (
                    user_code, document_type, filename, original_filename,
                    file_path, file_size, mime_type, uploaded_by, description,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (user_code, document_type, filename, original_filename,
                  file_path, file_size, mime_type, uploaded_by, description,
                  current_time, current_time))

            document_id = cursor.fetchone()['id']
            #print(document_id)
            return document_id, None

    except Exception as e:
        return None, f"Database error: {str(e)}"


def delete_document(document_id):
    """
    Delete a document record.

    Note: This only deletes the database record. The file should be
    deleted separately after calling this function.

    @param document_id: Document ID to delete
    @return: Tuple of (document_info, error_message)
    """
    try:
        with db_transaction() as (conn, cursor):
            # First get the document info for file deletion
            cursor.execute(
                "SELECT id, file_path, filename FROM applicant_documents WHERE id = %s",
                (document_id,),
            )
            document = cursor.fetchone()

            if not document:
                return None, "Document not found"

            # Delete the record
            cursor.execute(
                "DELETE FROM applicant_documents WHERE id = %s",
                (document_id,),
            )

            return document, None

    except Exception as e:
        return None, f"Database error: {str(e)}"


def update_document(document_id, description=None, document_type=None):
    """
    Update a document's metadata.

    @param document_id: Document ID to update
    @param description: New description (optional)
    @param document_type: New document type (optional)
    @return: Tuple of (success, error_message)
    """
    try:
        with db_transaction() as (conn, cursor):
            updates = []
            params = []

            if description is not None:
                updates.append("description = %s")
                params.append(description)

            if document_type is not None:
                updates.append("document_type = %s")
                params.append(document_type)

            if not updates:
                return False, "No updates provided"

            updates.append("updated_at = %s")
            params.append(datetime.now())
            params.append(document_id)

            query = f"UPDATE applicant_documents SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(query, tuple(params))

            if cursor.rowcount == 0:
                return False, "Document not found"

            return True, None

    except Exception as e:
        return False, f"Database error: {str(e)}"


def get_document_count_by_user_code(user_code):
    """
    Get the count of documents for an applicant.

    @param user_code: Applicant user code
    @return: Tuple of (count, error_message)
    """
    try:
        with db_connection() as (conn, cursor):
            cursor.execute(
                "SELECT COUNT(*) FROM applicant_documents WHERE user_code = %s",
                (user_code,),
            )
            return cursor.fetchone()[0], None

    except Exception as e:
        return None, f"Database error: {str(e)}"
