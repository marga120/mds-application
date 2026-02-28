"""
CSV Import Service — validates and processes applicant CSV uploads.
No Flask, no SQL. Delegates to models.applicants.process_csv_data.
"""

import io
import pandas as pd
from models.applicants import process_csv_data
from utils.activity_logger import log_activity


class CSVImportService:

    def import_file(self, file_bytes: bytes, admin_email: str) -> dict:
        """
        Parse CSV bytes, validate format, and import applicant data.
        Returns {success, message, records_processed}.
        Raises ValueError on invalid format.
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

        success, message, records_processed = process_csv_data(df)
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
