"""
CSV Import Service — validates and processes applicant CSV uploads.
No Flask, no SQL. Delegates to models.applicants.process_csv_data.
"""

import io
import pandas as pd
from models.applicants import process_csv_data
from models.sessions import find_session_by_abbrev
from utils.activity_logger import log_activity


class SessionValidationError(Exception):
    """Raised when one or more sessions referenced in the CSV do not exist."""

    def __init__(self, unmatched_sessions: list[dict]):
        self.unmatched_sessions = unmatched_sessions
        super().__init__("Session validation failed")


class CSVImportService:

    def import_file(self, file_bytes: bytes, admin_email: str, user=None) -> dict:
        """
        Parse CSV bytes, validate sessions, and import applicant data.
        Returns {success, message, records_processed}.
        Raises ValueError on invalid format.
        Raises SessionValidationError if any sessions in the CSV don't exist.
        """
        try:
            csv_text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("File encoding error — please upload a UTF-8 encoded CSV")

        df = pd.read_csv(io.StringIO(csv_text))
        df.columns = df.columns.str.rstrip()

        if "User Code" not in df.columns:
            raise ValueError("Missing required column: User Code")

        df = df.dropna(subset=["User Code"])
        if df.empty:
            raise ValueError("No valid data found in CSV")

        if "Session" not in df.columns:
            raise ValueError(
                "CSV is missing the required session column. "
                "Cannot determine which session to import into."
            )

        # Determine campus scope: None = Super Admin (unrestricted)
        campus = None
        if user is not None and not getattr(user, "is_super_admin", False):
            campus = getattr(user, "campus", None)

        session_id_map = self._validate_and_resolve_sessions(df, campus)

        success, message, records_processed = process_csv_data(df, session_id_map)
        if not success:
            raise ValueError(message)

        log_activity(
            action_type="csv_upload",
            target_entity="applicants",
            target_id="bulk_import",
            new_value=f"{records_processed} records",
            additional_metadata={
                "records_processed": records_processed,
                "uploaded_by": admin_email,
            },
        )

        return {"message": message, "records_processed": records_processed}

    def _validate_and_resolve_sessions(self, df: pd.DataFrame, campus: str | None) -> dict:
        """
        Extract distinct (program_code, session_abbrev) combos from df, look up each
        in the sessions table, and return a map of (program_code_upper, session_abbrev_upper)
        → session_id.

        Raises SessionValidationError listing any unmatched combos.
        """
        # Collect distinct combos (keep program name for error reporting)
        combos: dict[tuple, str] = {}  # (pc_upper, sa_upper) → program display name
        for _, row in df.iterrows():
            program_code = str(row.get("Program CODE", "")).strip()
            program = str(row.get("Program", "")).strip()
            session_abbrev = str(row.get("Session", "")).strip()

            if not program_code or program_code == "nan":
                continue
            if not session_abbrev or session_abbrev == "nan":
                continue

            key = (program_code.upper(), session_abbrev.upper())
            if key not in combos:
                combos[key] = program if program and program != "nan" else ""

        unmatched = []
        session_id_map = {}

        for (pc_upper, sa_upper), program in combos.items():
            session, _ = find_session_by_abbrev(pc_upper, sa_upper, campus)
            if session is None:
                unmatched.append({
                    "program_code": pc_upper,
                    "session_abbrev": sa_upper,
                    "program": program,
                })
            else:
                session_id_map[(pc_upper, sa_upper)] = session["id"]

        if unmatched:
            raise SessionValidationError(unmatched)

        return session_id_map
