from utils.database import get_db_connection
import pandas as pd
from datetime import datetime


def process_institution_info(user_code, row, cursor, current_time):
    """Process institution information for a student (up to 6 institutions)"""
    data_changed = False
    try:
         # Check existing institution data before processing
        cursor.execute("SELECT institution_number, updated_at FROM institution_info WHERE user_code = %s ORDER BY institution_number", (user_code,))
        old_institution_records = cursor.fetchall()
        old_institution_dict = {record[0]: record[1] for record in old_institution_records} if old_institution_records else {}

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
                expected_credential_code, expected_credential, honours, fail_withdraw, reason, gpa,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
                gpa = EXCLUDED.gpa,
                updated_at = CASE 
                    WHEN institution_info.institution_code IS DISTINCT FROM EXCLUDED.institution_code
                      OR institution_info.full_name IS DISTINCT FROM EXCLUDED.full_name
                      OR institution_info.country IS DISTINCT FROM EXCLUDED.country
                      OR institution_info.start_date IS DISTINCT FROM EXCLUDED.start_date
                      OR institution_info.end_date IS DISTINCT FROM EXCLUDED.end_date
                      OR institution_info.program_study IS DISTINCT FROM EXCLUDED.program_study
                      OR institution_info.degree_confer_code IS DISTINCT FROM EXCLUDED.degree_confer_code
                      OR institution_info.degree_confer IS DISTINCT FROM EXCLUDED.degree_confer
                      OR institution_info.date_confer IS DISTINCT FROM EXCLUDED.date_confer
                      OR institution_info.credential_receive_code IS DISTINCT FROM EXCLUDED.credential_receive_code
                      OR institution_info.credential_receive IS DISTINCT FROM EXCLUDED.credential_receive
                      OR institution_info.expected_confer_date IS DISTINCT FROM EXCLUDED.expected_confer_date
                      OR institution_info.expected_credential_code IS DISTINCT FROM EXCLUDED.expected_credential_code
                      OR institution_info.expected_credential IS DISTINCT FROM EXCLUDED.expected_credential
                      OR institution_info.honours IS DISTINCT FROM EXCLUDED.honours
                      OR institution_info.fail_withdraw IS DISTINCT FROM EXCLUDED.fail_withdraw
                      OR institution_info.reason IS DISTINCT FROM EXCLUDED.reason
                      OR institution_info.gpa IS DISTINCT FROM EXCLUDED.gpa
                    THEN EXCLUDED.updated_at 
                    ELSE institution_info.updated_at 
                END
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
                    current_time,  # created_at
                    current_time,  # updated_at
                ),
            )

        # Check if data changed after processing
        cursor.execute("SELECT institution_number, updated_at FROM institution_info WHERE user_code = %s ORDER BY institution_number", (user_code,))
        new_institution_records = cursor.fetchall()
        new_institution_dict = {record[0]: record[1] for record in new_institution_records} if new_institution_records else {}
        
        # Detect changes
        if len(old_institution_dict) != len(new_institution_dict):
            data_changed = True
        else:
            for inst_num, new_timestamp in new_institution_dict.items():
                old_timestamp = old_institution_dict.get(inst_num)
                if old_timestamp != new_timestamp:
                    data_changed = True
                    break

    except Exception as e:
        print(f"Error processing institution info for {user_code}: {e}")
    
    return data_changed