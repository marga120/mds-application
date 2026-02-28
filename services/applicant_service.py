"""
Applicant Service — business logic for applicant data management.
No Flask, no SQL. Calls models.applicants, logs activity.
"""

from models.applicants import (
    get_all_applicant_status,
    get_applicant_info_by_code,
    get_applicant_application_info_by_code,
    get_applicant_test_scores_by_code,
    get_applicant_institutions_by_code,
    update_applicant_application_status,
    update_applicant_prerequisites,
    update_english_comment as _update_english_comment,
    update_english_status as _update_english_status,
    update_applicant_scholarship,
    clear_all_applicant_data,
)
from models.statuses import get_all_statuses
from utils.activity_logger import log_activity

_VALID_ENGLISH_STATUSES = {"Not Met", "Not Required", "Passed"}


class ApplicantService:

    def get_all(self, session_id=None) -> list:
        """Return all applicants, optionally filtered by session."""
        applicants, error = get_all_applicant_status(session_id=session_id)
        if error:
            raise ValueError(error)
        return applicants or []

    def get_info(self, user_code: str) -> dict | None:
        """Return applicant personal info or None."""
        info, error = get_applicant_info_by_code(user_code)
        if error:
            raise ValueError(error)
        return info

    def get_application_info(self, user_code: str) -> dict | None:
        """Return application info or None."""
        info, error = get_applicant_application_info_by_code(user_code)
        if error:
            raise ValueError(error)
        return info

    def get_test_scores(self, user_code: str) -> dict:
        """Return test scores dict."""
        scores, error = get_applicant_test_scores_by_code(user_code)
        if error:
            raise ValueError(error)
        return scores or {}

    def get_institutions(self, user_code: str) -> list:
        """Return institution history list."""
        institutions, error = get_applicant_institutions_by_code(user_code)
        if error:
            raise ValueError(error)
        return institutions or []

    def update_status(self, user_code: str, status: str) -> str:
        """Validate status and update. Returns success message."""
        if not status:
            raise ValueError("Status is required")

        valid_statuses, error = get_all_statuses()
        if error or not valid_statuses:
            raise ValueError("Failed to validate status")

        valid_names = [s["status_name"] for s in valid_statuses]
        if status not in valid_names:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_names)}")

        old_info, _ = get_applicant_application_info_by_code(user_code)
        old_status = old_info.get("sent", "Not Reviewed") if old_info else "Not Reviewed"

        success, message = update_applicant_application_status(user_code, status)
        if not success:
            raise ValueError(message)

        if old_status != status:
            log_activity(
                action_type="status_change",
                target_entity="applicant",
                target_id=user_code,
                old_value=old_status,
                new_value=status,
                additional_metadata={"user_code": user_code},
            )

        return message

    def update_prerequisites(
        self,
        user_code: str,
        cs: str,
        stat: str,
        math: str,
        gpa,
        additional_comments: str,
        mds_v=None,
        mds_cl=None,
        mds_o=None,
    ) -> str:
        """Update prerequisite courses and GPA. Returns success message."""
        success, message = update_applicant_prerequisites(
            user_code, cs, stat, math, gpa, additional_comments, mds_v, mds_cl, mds_o
        )
        if not success:
            raise ValueError(message)
        return message

    def update_english_comment(self, user_code: str, comment: str) -> str:
        """Update English proficiency comment. Returns success message."""
        success, message = _update_english_comment(user_code, comment)
        if not success:
            raise ValueError(message)
        return message

    def update_english_status(self, user_code: str, status: str) -> str:
        """Validate and update English status. Returns success message."""
        if not status:
            raise ValueError("English status is required")
        if status not in _VALID_ENGLISH_STATUSES:
            raise ValueError("Invalid English status value")

        success, message = _update_english_status(user_code, status)
        if not success:
            raise ValueError(message)
        return message

    def update_scholarship(self, user_code: str, scholarship: str) -> str:
        """Validate and update scholarship decision. Returns success message."""
        if scholarship not in {"Yes", "No", "Undecided"}:
            raise ValueError("Invalid scholarship value")

        success, message = update_applicant_scholarship(user_code, scholarship)
        if not success:
            raise ValueError(message)
        return message

    def clear_all_data(self, admin_email: str) -> dict:
        """Clear all applicant data. Returns {message, tables_cleared}."""
        success, message, tables_cleared, records_cleared = clear_all_applicant_data()
        if not success:
            raise ValueError(message)

        log_activity(
            action_type="clear_all_data",
            target_entity="database",
            target_id="all_applicant_tables",
            old_value=str(records_cleared),
            new_value="0",
            additional_metadata={
                "tables_cleared": tables_cleared,
                "records_cleared": records_cleared,
                "admin_user": admin_email,
            },
        )

        return {"message": message, "tables_cleared": tables_cleared}
