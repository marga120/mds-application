from utils.database import get_db_connection
import pandas as pd
from datetime import datetime


def process_institution_info(user_code, row, cursor, current_time):
    """Process institution information for a student (up to 6 institutions)"""
    try:
        # Process up to 6 institutions (I1 through I6)
        for i in range(1, 7):
            prefix = f"I{i}"

            # Check if this institution entry has data
            institution_code = row.get(f"{prefix} Institution CODE")
            if pd.isna(institution_code):
                continue

            # Parse start date
            start_date = None
            if pd.notna(row.get(f"{prefix} Start Date")):
                try:
                    start_date = pd.to_datetime(row.get(f"{prefix} Start Date")).date()
                except:
                    start_date = None

            # Parse end date
            end_date = None
            if pd.notna(row.get(f"{prefix} End Date or Expected End Date")):
                try:
                    end_date = pd.to_datetime(
                        row.get(f"{prefix} End Date or Expected End Date")
                    ).date()
                except:
                    end_date = None

            # Parse date conferred
            date_confer = None
            if pd.notna(row.get(f"{prefix} If Yes, Date Conferred")):
                try:
                    date_confer = pd.to_datetime(
                        row.get(f"{prefix} If Yes, Date Conferred")
                    ).date()
                except:
                    date_confer = None

            # Parse expected conferred date
            expected_confer_date = None
            if pd.notna(row.get(f"{prefix} Expected Conferred Date")):
                try:
                    expected_confer_date = pd.to_datetime(
                        row.get(f"{prefix} Expected Conferred Date")
                    ).date()
                except:
                    expected_confer_date = None

            # Convert withdrawal/failure to string (VARCHAR(3))
            fail_withdraw = None
            withdraw_field = row.get(
                f"{prefix} Were you required to withdraw or did you have a failed year from this institution?"
            )
            if pd.isna(withdraw_field):
                # For I4-I6, check the "Withdrawal?" field instead
                withdraw_field = row.get(f"{prefix} Withdrawal?")

            if pd.notna(withdraw_field):
                # Convert to string limited to 3 characters for VARCHAR(3)
                withdraw_str = str(withdraw_field).strip()[:3]
                fail_withdraw = withdraw_str if withdraw_str else None

            # Helper function to safely convert values to strings
            def safe_str(value):
                if pd.isna(value):
                    return None
                return str(value).strip() if str(value).strip() else None

            institution_query = """
            INSERT INTO institution_info (
                user_code, institution_number, institution_code, full_name, country,
                start_date, end_date, program_study, degree_confer_code, degree_confer,
                date_confer, credential_receive_code, credential_receive, expected_confer_date,
                expected_credential_code, expected_credential, honours, fail_withdraw, reason, gpa
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (user_code, institution_number) DO UPDATE SET
                institution_code = EXCLUDED.institution_code,
                full_name = EXCLUDED.full_name,
                country = EXCLUDED.country,
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                program_study = EXCLUDED.program_study,
                degree_confer_code = EXCLUDED.degree_confer_code,
                degree_confer = EXCLUDED.degree_confer,
                date_confer = EXCLUDED.date_confer,
                credential_receive_code = EXCLUDED.credential_receive_code,
                credential_receive = EXCLUDED.credential_receive,
                expected_confer_date = EXCLUDED.expected_confer_date,
                expected_credential_code = EXCLUDED.expected_credential_code,
                expected_credential = EXCLUDED.expected_credential,
                honours = EXCLUDED.honours,
                fail_withdraw = EXCLUDED.fail_withdraw,
                reason = EXCLUDED.reason,
                gpa = EXCLUDED.gpa
            """

            cursor.execute(
                institution_query,
                (
                    user_code,
                    i,  # institution_number (1-6)
                    safe_str(institution_code),
                    safe_str(row.get(f"{prefix} Full Institution Name")),
                    safe_str(row.get(f"{prefix} Institution Country")),
                    start_date,
                    end_date,
                    safe_str(row.get(f"{prefix} Program of Study")),
                    safe_str(row.get(f"{prefix} Degree Conferred? CODE")),
                    safe_str(row.get(f"{prefix} Degree Conferred?")),
                    date_confer,
                    safe_str(row.get(f"{prefix} Credential Received CODE")),
                    safe_str(row.get(f"{prefix} Credential Received")),
                    expected_confer_date,
                    safe_str(row.get(f"{prefix} Expected Credential CODE")),
                    safe_str(row.get(f"{prefix} Expected Credential")),
                    safe_str(row.get(f"{prefix} Honours")),
                    fail_withdraw,
                    safe_str(row.get(f"{prefix} Provide Details/Reason")),
                    safe_str(row.get(f"{prefix} Self Reported GPA")),
                ),
            )

    except Exception as e:
        print(f"Error processing institution info for {user_code}: {e}")
