"""
Session Service — business logic for academic session management.
No Flask, no SQL. Calls models.sessions, logs activity.
"""

from models.sessions import (
    get_all_sessions as _get_all_sessions,
    get_session_by_id as _get_session_by_id,
    get_most_recent_session as _get_most_recent_session,
    get_session_name as _get_session_name,
    create_session as _create_session,
    archive_session as _archive_session,
    restore_session as _restore_session,
)
from utils.activity_logger import log_activity


class SessionService:

    def get_all_sessions(self, include_archived: bool = False) -> dict:
        """Return sessions grouped by campus."""
        sessions, error = _get_all_sessions(include_archived)
        if error:
            raise ValueError(error)
        return sessions or {}

    def get_session_by_id(self, session_id: int) -> dict:
        """Return a single session dict or raise ValueError."""
        session, error = _get_session_by_id(session_id)
        if error:
            raise ValueError(error)
        return session

    def get_most_recent_session(self, campus=None) -> dict | None:
        """Return the most recent non-archived session, or None."""
        session, _ = _get_most_recent_session(campus)
        return session

    def get_session_name(self) -> str | None:
        """Return session name for legacy endpoint."""
        name, _ = _get_session_name()
        return name

    def create_session(
        self,
        program_code: str,
        program: str,
        session_abbrev: str,
        year: int,
        campus: str,
        description: str,
        user,
    ) -> dict:
        """Validate and create a new session. Returns session info dict."""
        program_code = program_code.strip().upper()
        program = program.strip()
        session_abbrev = session_abbrev.strip()
        description = description.strip() if description else ""

        if not program_code:
            raise ValueError("Program code is required")
        if len(program_code) < 2 or len(program_code) > 10:
            raise ValueError("Program code must be 2-10 characters")
        if not program_code.isalpha():
            raise ValueError("Program code must contain only letters")
        if not program:
            raise ValueError("Program name is required")
        if len(program) > 100:
            raise ValueError("Program name must be 100 characters or less")
        if not session_abbrev:
            raise ValueError("Session abbreviation is required")
        if not year:
            raise ValueError("Year is required")
        year = int(year)
        if year < 2024 or year > 2035:
            raise ValueError("Year must be between 2024 and 2035")
        campus = campus.strip()
        if not campus:
            raise ValueError("Campus is required")
        if len(campus) > 20:
            raise ValueError("Campus must be 20 characters or less")

        session_id, error = _create_session(
            program_code=program_code,
            program=program,
            session_abbrev=session_abbrev,
            year=year,
            campus=campus,
            description=description,
        )
        if error:
            raise ValueError(error)

        session_name = f"{program_code}-{campus} {session_abbrev}"

        log_activity(
            action_type="create_session",
            target_entity="session",
            target_id=str(session_id),
            new_value=session_name,
            additional_metadata={"campus": campus, "program_code": program_code},
        )

        return {
            "id": session_id,
            "name": session_name,
            "campus": campus,
            "year": year,
            "program_code": program_code,
        }


    def archive_session(self, session_id: int, user) -> str:
        """Archive a session. Returns success message."""
        success, message = _archive_session(session_id)
        if not success:
            raise ValueError(message)

        log_activity(
            action_type="archive_session",
            target_entity="session",
            target_id=str(session_id),
            new_value="archived",
        )
        return message

    def restore_session(self, session_id: int, user) -> str:
        """Restore an archived session. Returns success message."""
        success, message = _restore_session(session_id)
        if not success:
            raise ValueError(message)

        log_activity(
            action_type="restore_session",
            target_entity="session",
            target_id=str(session_id),
            new_value="restored",
        )
        return message
