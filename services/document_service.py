"""
Document Service — business logic for applicant document management.
No Flask, no SQL. Calls models.documents, logs activity.
File I/O (save/delete on disk) handled here; HTTP serving remains in api layer.
"""

import os
import uuid
from werkzeug.utils import secure_filename
from models.documents import (
    get_documents_by_user_code as _get_docs,
    get_document_by_id as _get_doc,
    save_document as _save_doc,
    delete_document as _delete_doc,
    get_document_count_by_user_code as _get_count,
)
from utils.activity_logger import log_activity

MAX_FILE_SIZE = 30 * 1024 * 1024  # 30 MB
ALLOWED_EXTENSIONS = {"pdf"}
DOCUMENT_TYPES = {"transcript", "recommendation_letter", "cv_resume", "statement_of_purpose", "other"}


class DocumentService:

    def get_documents(self, user_code: str) -> list:
        """Return all documents for an applicant."""
        docs, error = _get_docs(user_code)
        if error:
            raise ValueError(error)
        result = []
        for doc in (docs or []):
            d = dict(doc)
            if d.get("created_at"):
                d["created_at"] = d["created_at"].isoformat()
            if d.get("updated_at"):
                d["updated_at"] = d["updated_at"].isoformat()
            result.append(d)
        return result

    def get_document(self, doc_id: int) -> dict | None:
        """Return a single document dict or None."""
        doc, error = _get_doc(doc_id)
        if error:
            raise ValueError(error)
        return doc

    def get_count(self, user_code: str) -> int:
        """Return the document count for an applicant."""
        count, error = _get_count(user_code)
        if error:
            raise ValueError(error)
        return count or 0

    def upload_document(self, user_code: str, file, document_type: str, description: str, uploader_id: int, upload_folder: str) -> dict:
        """Validate, save file to disk, persist to DB. Returns document info."""
        if not file or file.filename == "":
            raise ValueError("No file provided")

        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError("Invalid file type. Only PDF files are allowed.")

        # Read into memory to check size before saving
        file_bytes = file.read()
        if len(file_bytes) > MAX_FILE_SIZE:
            raise ValueError("File size exceeds 30 MB limit")
        file.seek(0)  # Reset for saving

        if document_type not in DOCUMENT_TYPES:
            document_type = "other"

        original_filename = file.filename
        secure_name = secure_filename(original_filename)
        name_part = secure_name.rsplit(".", 1)[0] if "." in secure_name else secure_name
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{name_part}_{unique_id}.pdf"

        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        file_size = os.path.getsize(file_path)

        doc_id, error = _save_doc(
            user_code=user_code,
            document_type=document_type,
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type="application/pdf",
            uploaded_by=uploader_id,
            description=description,
        )

        if error:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise ValueError(error)

        log_activity(
            action_type="document_upload",
            target_entity="applicant_documents",
            target_id=user_code,
            new_value=f"{document_type}: {original_filename}",
        )

        return {"document_id": doc_id, "filename": filename}

    def delete_document(self, doc_id: int, user) -> str:
        """Delete document from DB and disk. Returns success message."""
        document, error = _get_doc(doc_id)
        if error:
            raise ValueError(error)
        if not document:
            raise ValueError("Document not found")

        deleted_doc, error = _delete_doc(doc_id)
        if error:
            raise ValueError(error)

        file_path = document["file_path"]
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass  # DB record deleted; log but don't fail

        log_activity(
            action_type="document_delete",
            target_entity="applicant_documents",
            target_id=document["user_code"],
            old_value=f"{document['document_type']}: {document['original_filename']}",
        )
        return "Document deleted successfully"

    def get_download_info(self, doc_id: int) -> tuple:
        """Return (file_path, original_filename, mime_type) for send_file."""
        document, error = _get_doc(doc_id)
        if error:
            raise ValueError(error)
        if not document:
            raise ValueError("Document not found")
        if not os.path.exists(document["file_path"]):
            raise ValueError("File not found on server")
        return document["file_path"], document["original_filename"], document.get("mime_type") or "application/pdf"
