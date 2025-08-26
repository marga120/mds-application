from utils.database import get_db_connection
import pandas as pd
from datetime import datetime

def process_toefl_scores(user_code, row, cursor, current_time):
    """
    Process and insert TOEFL test scores from CSV data.
    
    Extracts TOEFL test information from CSV row and inserts into
    the toefl table with score validation and date parsing.
    
    @param cursor: Database cursor for executing queries
    @param_type cursor: psycopg2.cursor
    @param user_code: Unique identifier for the applicant
    @param_type user_code: str
    @param df_row: Pandas DataFrame row containing CSV data
    @param_type df_row: pandas.Series
    
    @return: None (inserts directly into database)
    @return_type: None
    
    @db_tables: toefl
    @validation: Validates score ranges and date formats
    @csv_columns: reading, listening, speaking, writing, total scores
    
    @example:
        process_toefl_scores(cursor, "12345", df_row)
        # Processes TOEFL data from CSV and inserts into database
    """

    """Process TOEFL scores for a student"""
    data_changed = False
    try:
        # Check existing TOEFL data before processing
        cursor.execute("SELECT toefl_number, updated_at FROM toefl WHERE user_code = %s ORDER BY toefl_number", (user_code,))
        old_toefl_records = cursor.fetchall()
        old_toefl_dict = {record[0]: record[1] for record in old_toefl_records} if old_toefl_records else {}

        # Process up to 3 TOEFL scores (TOEFL, TOEFL2, TOEFL3)
        for i in range(1, 4):
            prefix = "TOEFL" if i == 1 else f"TOEFL{i}"

            # Check if this TOEFL entry has data
            reg_num = row.get(f"{prefix} Registration #")
            if pd.isna(reg_num):
                continue

            # Parse date of writing
            date_written = None
            if pd.notna(row.get(f"{prefix} Date of Writing")):
                try:
                    date_written = pd.to_datetime(
                        row.get(f"{prefix} Date of Writing")
                    ).date()
                except:
                    date_written = None

            # Parse MyBest dates
            mybest_date = None
            if pd.notna(row.get(f"{prefix} MyBest as of Date")):
                try:
                    mybest_date = pd.to_datetime(
                        row.get(f"{prefix} MyBest as of Date")
                    ).date()
                except:
                    mybest_date = None

            mybest_listening_date = None
            if pd.notna(row.get(f"{prefix} MyBest Listening Date")):
                try:
                    mybest_listening_date = pd.to_datetime(
                        row.get(f"{prefix} MyBest Listening Date")
                    ).date()
                except:
                    mybest_listening_date = None

            mybest_writing_date = None
            if pd.notna(row.get(f"{prefix} MyBest Writing Date")):
                try:
                    mybest_writing_date = pd.to_datetime(
                        row.get(f"{prefix} MyBest Writing Date")
                    ).date()
                except:
                    mybest_writing_date = None

            mybest_reading_date = None
            if pd.notna(row.get(f"{prefix} MyBest Reading Date")):
                try:
                    mybest_reading_date = pd.to_datetime(
                        row.get(f"{prefix} MyBest Reading Date")
                    ).date()
                except:
                    mybest_reading_date = None

            mybest_speaking_date = None
            if pd.notna(row.get(f"{prefix} MyBest Speaking Date")):
                try:
                    mybest_speaking_date = pd.to_datetime(
                        row.get(f"{prefix} MyBest Speaking Date")
                    ).date()
                except:
                    mybest_speaking_date = None

            # Convert scores to strings if they exist, otherwise None
            def convert_score(value):
                return str(int(value)) if pd.notna(value) else None

            toefl_query = """
            INSERT INTO toefl (
                user_code, toefl_number, registration_num, date_written, total_score,
                listening, structure_written, reading, speaking, mybest_total,
                mybest_date, mybest_listening, mybest_listening_date, mybest_writing,
                mybest_writing_date, mybest_reading, mybest_reading_date,
                mybest_speaking, mybest_speaking_date, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_code, toefl_number) DO UPDATE SET
                registration_num = EXCLUDED.registration_num,
                date_written = EXCLUDED.date_written,
                total_score = EXCLUDED.total_score,
                listening = EXCLUDED.listening,
                structure_written = EXCLUDED.structure_written,
                reading = EXCLUDED.reading,
                speaking = EXCLUDED.speaking,
                mybest_total = EXCLUDED.mybest_total,
                mybest_date = EXCLUDED.mybest_date,
                mybest_listening = EXCLUDED.mybest_listening,
                mybest_listening_date = EXCLUDED.mybest_listening_date,
                mybest_writing = EXCLUDED.mybest_writing,
                mybest_writing_date = EXCLUDED.mybest_writing_date,
                mybest_reading = EXCLUDED.mybest_reading,
                mybest_reading_date = EXCLUDED.mybest_reading_date,
                mybest_speaking = EXCLUDED.mybest_speaking,
                mybest_speaking_date = EXCLUDED.mybest_speaking_date,
                updated_at = CASE 
                    WHEN toefl.registration_num IS DISTINCT FROM EXCLUDED.registration_num
                      OR toefl.date_written IS DISTINCT FROM EXCLUDED.date_written
                      OR toefl.total_score IS DISTINCT FROM EXCLUDED.total_score
                      OR toefl.listening IS DISTINCT FROM EXCLUDED.listening
                      OR toefl.structure_written IS DISTINCT FROM EXCLUDED.structure_written
                      OR toefl.reading IS DISTINCT FROM EXCLUDED.reading
                      OR toefl.speaking IS DISTINCT FROM EXCLUDED.speaking
                      OR toefl.mybest_total IS DISTINCT FROM EXCLUDED.mybest_total
                      OR toefl.mybest_date IS DISTINCT FROM EXCLUDED.mybest_date
                      OR toefl.mybest_listening IS DISTINCT FROM EXCLUDED.mybest_listening
                      OR toefl.mybest_listening_date IS DISTINCT FROM EXCLUDED.mybest_listening_date
                      OR toefl.mybest_writing IS DISTINCT FROM EXCLUDED.mybest_writing
                      OR toefl.mybest_writing_date IS DISTINCT FROM EXCLUDED.mybest_writing_date
                      OR toefl.mybest_reading IS DISTINCT FROM EXCLUDED.mybest_reading
                      OR toefl.mybest_reading_date IS DISTINCT FROM EXCLUDED.mybest_reading_date
                      OR toefl.mybest_speaking IS DISTINCT FROM EXCLUDED.mybest_speaking
                      OR toefl.mybest_speaking_date IS DISTINCT FROM EXCLUDED.mybest_speaking_date
                    THEN EXCLUDED.updated_at 
                    ELSE toefl.updated_at 
                END
            """

            cursor.execute(
                toefl_query,
                (
                    user_code,
                    i,  # toefl_number
                    str(int(reg_num)) if pd.notna(reg_num) else None,
                    date_written,
                    convert_score(row.get(f"{prefix} Total Score")),
                    convert_score(row.get(f"{prefix} Listening")),
                    convert_score(row.get(f"{prefix} Structure/Written")),
                    convert_score(row.get(f"{prefix} Reading")),
                    convert_score(row.get(f"{prefix} Speaking")),
                    convert_score(row.get(f"{prefix} MyBest Total Score")),
                    mybest_date,
                    convert_score(row.get(f"{prefix} MyBest Listening Score")),
                    mybest_listening_date,
                    convert_score(row.get(f"{prefix} MyBest Writing Score")),
                    mybest_writing_date,
                    convert_score(row.get(f"{prefix} MyBest Reading Score")),
                    mybest_reading_date,
                    convert_score(row.get(f"{prefix} MyBest Speaking Score")),
                    mybest_speaking_date,
                    current_time,  # created_at
                    current_time,  # updated_at
                ),
            )

        # Check if data changed after processing
        cursor.execute("SELECT toefl_number, updated_at FROM toefl WHERE user_code = %s ORDER BY toefl_number", (user_code,))
        new_toefl_records = cursor.fetchall()
        new_toefl_dict = {record[0]: record[1] for record in new_toefl_records} if new_toefl_records else {}
        
        # Detect changes
        if len(old_toefl_dict) != len(new_toefl_dict):
            data_changed = True
        else:
            for toefl_num, new_timestamp in new_toefl_dict.items():
                old_timestamp = old_toefl_dict.get(toefl_num)
                if old_timestamp != new_timestamp:
                    data_changed = True
                    break

    except Exception as e:
        print(f"Error processing TOEFL scores for {user_code}: {e}")
    
    return data_changed


def process_ielts_scores(user_code, row, cursor, current_time):
    """
    Process and insert IELTS test scores from CSV data.
    
    Extracts IELTS test information from CSV row and inserts into
    the ielts table with band score validation.
    
    @param cursor: Database cursor for executing queries
    @param_type cursor: psycopg2.cursor
    @param user_code: Unique identifier for the applicant
    @param_type user_code: str
    @param df_row: Pandas DataFrame row containing CSV data
    @param_type df_row: pandas.Series
    
    @return: None (inserts directly into database)
    @return_type: None
    
    @db_tables: ielts
    @validation: Validates IELTS band scores (0.0-9.0)
    @csv_columns: listening, reading, writing, speaking, overall bands
    
    @example:
        process_ielts_scores(cursor, "12345", df_row)
        # Processes IELTS data from CSV and inserts into database
    """

    """Process IELTS scores for a student"""
    data_changed = False

    try:
        # Check existing IELTS data before processing
        cursor.execute("SELECT ielts_number, updated_at FROM ielts WHERE user_code = %s ORDER BY ielts_number", (user_code,))
        old_ielts_records = cursor.fetchall()
        old_ielts_dict = {record[0]: record[1] for record in old_ielts_records} if old_ielts_records else {}


        # Process up to 3 IELTS scores (IELTS, IELTS2, IELTS3)
        for i in range(1, 4):
            prefix = "IELTS" if i == 1 else f"IELTS{i}"

            # Check if this IELTS entry has data
            candidate_num = row.get(f"{prefix} Candidate #")
            if pd.isna(candidate_num):
                continue

            # Parse date of writing
            date_written = None
            if pd.notna(row.get(f"{prefix} Date of Writing")):
                try:
                    date_written = pd.to_datetime(
                        row.get(f"{prefix} Date of Writing")
                    ).date()
                except:
                    date_written = None

            # Convert scores to strings if they exist, otherwise None
            def convert_score(value):
                return str(value) if pd.notna(value) else None

            ielts_query = """
            INSERT INTO ielts (
                user_code, ielts_number, candidate_num, date_written, total_band_score,
                listening, reading, writing, speaking, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_code, ielts_number) DO UPDATE SET
                candidate_num = EXCLUDED.candidate_num,
                date_written = EXCLUDED.date_written,
                total_band_score = EXCLUDED.total_band_score,
                listening = EXCLUDED.listening,
                reading = EXCLUDED.reading,
                writing = EXCLUDED.writing,
                speaking = EXCLUDED.speaking,
                updated_at = CASE 
                    WHEN ielts.candidate_num IS DISTINCT FROM EXCLUDED.candidate_num
                      OR ielts.date_written IS DISTINCT FROM EXCLUDED.date_written
                      OR ielts.total_band_score IS DISTINCT FROM EXCLUDED.total_band_score
                      OR ielts.listening IS DISTINCT FROM EXCLUDED.listening
                      OR ielts.reading IS DISTINCT FROM EXCLUDED.reading
                      OR ielts.writing IS DISTINCT FROM EXCLUDED.writing
                      OR ielts.speaking IS DISTINCT FROM EXCLUDED.speaking
                    THEN EXCLUDED.updated_at 
                    ELSE ielts.updated_at 
                END
            """

            cursor.execute(
                ielts_query,
                (
                    user_code,
                    i,  # ielts_number
                    str(int(candidate_num)) if pd.notna(candidate_num) else None,
                    date_written,
                    convert_score(row.get(f"{prefix} Total Band Score")),
                    convert_score(row.get(f"{prefix} Listening")),
                    convert_score(row.get(f"{prefix} Reading")),
                    convert_score(row.get(f"{prefix} Writing")),
                    convert_score(row.get(f"{prefix} Speaking")),
                    current_time,  # created_at
                    current_time,  # updated_at
                ),
            )

        # Check if data changed after processing
        cursor.execute("SELECT ielts_number, updated_at FROM ielts WHERE user_code = %s ORDER BY ielts_number", (user_code,))
        new_ielts_records = cursor.fetchall()
        new_ielts_dict = {record[0]: record[1] for record in new_ielts_records} if new_ielts_records else {}
        
        # Detect changes
        if len(old_ielts_dict) != len(new_ielts_dict):
            data_changed = True
        else:
            for ielts_num, new_timestamp in new_ielts_dict.items():
                old_timestamp = old_ielts_dict.get(ielts_num)
                if old_timestamp != new_timestamp:
                    data_changed = True
                    break

    except Exception as e:
        print(f"Error processing IELTS scores for {user_code}: {e}")
    
    return data_changed


def process_other_test_scores(user_code, row, cursor, current_time):
    """
    Process and insert other standardized test scores from CSV data.
    
    Handles various other test types including GRE, GMAT, MELAB, PTE,
    CAEL, CELPIP, and Alternative ELPP scores from CSV data.
    
    @param cursor: Database cursor for executing queries
    @param_type cursor: psycopg2.cursor
    @param user_code: Unique identifier for the applicant
    @param_type user_code: str
    @param df_row: Pandas DataFrame row containing CSV data
    @param_type df_row: pandas.Series
    
    @return: None (inserts directly into database)
    @return_type: None
    
    @db_tables: gre, gmat, melab, pte, cael, celpip, alt_elpp
    @validation: Test-specific score range and format validation
    @csv_columns: Various test-specific score columns
    
    @example:
        process_other_test_scores(cursor, "12345", df_row)
        # Processes GRE, GMAT, and other test scores from CSV
    """

    """Process other test scores (MELAB, PTE, CAEL, CELPIP, ALT ELPP, GRE, GMAT)"""
    data_changed = False

    try:
        # Check existing data for all test types
        tables_to_check = ['melab', 'pte', 'cael', 'celpip', 'alt_elpp', 'gre', 'gmat']
        old_timestamps = {}
        
        for table in tables_to_check:
            cursor.execute(f"SELECT updated_at FROM {table} WHERE user_code = %s", (user_code,))
            result = cursor.fetchone()
            old_timestamps[table] = result[0] if result else None
        
        # Convert scores to strings if they exist, otherwise None
        def convert_score(value):
            return str(value) if pd.notna(value) else None

        # MELAB
        melab_ref = row.get("MELAB Reference #")
        if pd.notna(melab_ref):
            melab_date = None
            if pd.notna(row.get("MELAB Date of Writing")):
                try:
                    melab_date = pd.to_datetime(row.get("MELAB Date of Writing")).date()
                except:
                    melab_date = None

            melab_query = """
            INSERT INTO melab (user_code, ref_num, date_written, total, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_code) DO UPDATE SET
                ref_num = EXCLUDED.ref_num,
                date_written = EXCLUDED.date_written,
                total = EXCLUDED.total,
                updated_at = CASE 
                    WHEN melab.ref_num IS DISTINCT FROM EXCLUDED.ref_num
                      OR melab.date_written IS DISTINCT FROM EXCLUDED.date_written
                      OR melab.total IS DISTINCT FROM EXCLUDED.total
                    THEN EXCLUDED.updated_at 
                    ELSE melab.updated_at 
                END
            """
            cursor.execute(
                melab_query,
                (
                    user_code,
                    str(int(melab_ref)),
                    melab_date,
                    convert_score(row.get("MELAB Total Score")),
                    current_time,  # created_at
                    current_time,  # updated_at
                ),
            )


        # PTE
        pte_ref = row.get("PTE Reference #")
        if pd.notna(pte_ref):
            pte_date = None
            if pd.notna(row.get("PTE Date of Writing")):
                try:
                    pte_date = pd.to_datetime(row.get("PTE Date of Writing")).date()
                except:
                    pte_date = None

            pte_query = """
            INSERT INTO pte (user_code, ref_num, date_written, total, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_code) DO UPDATE SET
                ref_num = EXCLUDED.ref_num,
                date_written = EXCLUDED.date_written,
                total = EXCLUDED.total,
                updated_at = CASE 
                    WHEN pte.ref_num IS DISTINCT FROM EXCLUDED.ref_num
                      OR pte.date_written IS DISTINCT FROM EXCLUDED.date_written
                      OR pte.total IS DISTINCT FROM EXCLUDED.total
                    THEN EXCLUDED.updated_at 
                    ELSE pte.updated_at 
                END
            """
            cursor.execute(
                pte_query,
                (
                    user_code,
                    str(int(pte_ref)),
                    pte_date,
                    convert_score(row.get("PTE Total Score")),
                    current_time,  # created_at
                    current_time,  # updated_at
                ),
            )

        # CAEL
        cael_ref = row.get("CAEL Reference #")
        if pd.notna(cael_ref):
            cael_date = None
            if pd.notna(row.get("CAEL Date of Writing")):
                try:
                    cael_date = pd.to_datetime(row.get("CAEL Date of Writing")).date()
                except:
                    cael_date = None

            cael_query = """
            INSERT INTO cael (user_code, ref_num, date_written, reading, listening, writing, speaking, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_code) DO UPDATE SET
                ref_num = EXCLUDED.ref_num,
                date_written = EXCLUDED.date_written,
                reading = EXCLUDED.reading,
                listening = EXCLUDED.listening,
                writing = EXCLUDED.writing,
                speaking = EXCLUDED.speaking,
                updated_at = CASE 
                    WHEN cael.ref_num IS DISTINCT FROM EXCLUDED.ref_num
                      OR cael.date_written IS DISTINCT FROM EXCLUDED.date_written
                      OR cael.reading IS DISTINCT FROM EXCLUDED.reading
                      OR cael.listening IS DISTINCT FROM EXCLUDED.listening
                      OR cael.writing IS DISTINCT FROM EXCLUDED.writing
                      OR cael.speaking IS DISTINCT FROM EXCLUDED.speaking
                    THEN EXCLUDED.updated_at 
                    ELSE cael.updated_at 
                END
            """
            cursor.execute(
                cael_query,
                (
                    user_code,
                    str(int(cael_ref)),
                    cael_date,
                    convert_score(row.get("CAEL Reading Performance Score")),
                    convert_score(row.get("CAEL Listening Performance Score")),
                    convert_score(row.get("CAEL Writing Performance Score")),
                    convert_score(row.get("CAEL Speaking Performance Score")),
                    current_time,
                    current_time,
                ),
            )

        # CELPIP
        celpip_ref = row.get("CELPIP Reference #")
        if pd.notna(celpip_ref):
            celpip_date = None
            if pd.notna(row.get("CELPIP Date of Writing")):
                try:
                    celpip_date = pd.to_datetime(
                        row.get("CELPIP Date of Writing")
                    ).date()
                except:
                    celpip_date = None

            celpip_query = """
            INSERT INTO celpip (user_code, ref_num, date_written, listening, speaking, reading_writing, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_code) DO UPDATE SET
                ref_num = EXCLUDED.ref_num,
                date_written = EXCLUDED.date_written,
                listening = EXCLUDED.listening,
                speaking = EXCLUDED.speaking,
                reading_writing = EXCLUDED.reading_writing,
                updated_at = CASE 
                    WHEN celpip.ref_num IS DISTINCT FROM EXCLUDED.ref_num
                      OR celpip.date_written IS DISTINCT FROM EXCLUDED.date_written
                      OR celpip.listening IS DISTINCT FROM EXCLUDED.listening
                      OR celpip.speaking IS DISTINCT FROM EXCLUDED.speaking
                      OR celpip.reading_writing IS DISTINCT FROM EXCLUDED.reading_writing
                    THEN EXCLUDED.updated_at 
                    ELSE celpip.updated_at 
                END
            """
            cursor.execute(
                celpip_query,
                (
                    user_code,
                    str(int(celpip_ref)),
                    celpip_date,
                    convert_score(row.get("CELPIP Listening Score")),
                    convert_score(row.get("CELPIP Speaking Score")),
                    convert_score(row.get("CELPIP Academic Reading & Writing Score")),
                    current_time,
                    current_time,
                ),
            )

        # ALT ELPP
        alt_elpp_ref = row.get("ALT ELPP Reference #")
        if pd.notna(alt_elpp_ref):
            alt_elpp_date = None
            if pd.notna(row.get("ALT ELPP Date of Writing")):
                try:
                    alt_elpp_date = pd.to_datetime(
                        row.get("ALT ELPP Date of Writing")
                    ).date()
                except:
                    alt_elpp_date = None

            alt_elpp_query = """
            INSERT INTO alt_elpp (user_code, ref_num, date_written, total, test_type, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_code) DO UPDATE SET
                ref_num = EXCLUDED.ref_num,
                date_written = EXCLUDED.date_written,
                total = EXCLUDED.total,
                test_type = EXCLUDED.test_type,
                updated_at = CASE 
                    WHEN alt_elpp.ref_num IS DISTINCT FROM EXCLUDED.ref_num
                      OR alt_elpp.date_written IS DISTINCT FROM EXCLUDED.date_written
                      OR alt_elpp.total IS DISTINCT FROM EXCLUDED.total
                      OR alt_elpp.test_type IS DISTINCT FROM EXCLUDED.test_type
                    THEN EXCLUDED.updated_at 
                    ELSE alt_elpp.updated_at 
                END
            """
            cursor.execute(
                alt_elpp_query,
                (
                    user_code,
                    str(int(alt_elpp_ref)),
                    alt_elpp_date,
                    convert_score(row.get("ALT ELPP Total Score")),
                    convert_score(row.get("ALT ELPP Test Type")),
                    current_time,
                    current_time,
                ),
            )

        # GRE
        gre_reg = row.get("GRE Registration #")
        if pd.notna(gre_reg):
            gre_date = None
            if pd.notna(row.get("GRE Date of Writing")):
                try:
                    gre_date = pd.to_datetime(row.get("GRE Date of Writing")).date()
                except:
                    gre_date = None

            gre_subject_date = None
            if pd.notna(row.get("GRE (Subject Tests) - Date of Test")):
                try:
                    gre_subject_date = pd.to_datetime(
                        row.get("GRE (Subject Tests) - Date of Test")
                    ).date()
                except:
                    gre_subject_date = None

            gre_query = """
            INSERT INTO gre (
                user_code, reg_num, date_written, verbal, verbal_below, quantitative,
                quantitative_below, writing, writing_below, subject_tests, subject_reg_num,
                subject_date, subject_scaled_score, subject_below, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_code) DO UPDATE SET
                reg_num = EXCLUDED.reg_num,
                date_written = EXCLUDED.date_written,
                verbal = EXCLUDED.verbal,
                verbal_below = EXCLUDED.verbal_below,
                quantitative = EXCLUDED.quantitative,
                quantitative_below = EXCLUDED.quantitative_below,
                writing = EXCLUDED.writing,
                writing_below = EXCLUDED.writing_below,
                subject_tests = EXCLUDED.subject_tests,
                subject_reg_num = EXCLUDED.subject_reg_num,
                subject_date = EXCLUDED.subject_date,
                subject_scaled_score = EXCLUDED.subject_scaled_score,
                subject_below = EXCLUDED.subject_below,
                updated_at = CASE 
                    WHEN gre.reg_num IS DISTINCT FROM EXCLUDED.reg_num
                      OR gre.date_written IS DISTINCT FROM EXCLUDED.date_written
                      OR gre.verbal IS DISTINCT FROM EXCLUDED.verbal
                      OR gre.verbal_below IS DISTINCT FROM EXCLUDED.verbal_below
                      OR gre.quantitative IS DISTINCT FROM EXCLUDED.quantitative
                      OR gre.quantitative_below IS DISTINCT FROM EXCLUDED.quantitative_below
                      OR gre.writing IS DISTINCT FROM EXCLUDED.writing
                      OR gre.writing_below IS DISTINCT FROM EXCLUDED.writing_below
                      OR gre.subject_tests IS DISTINCT FROM EXCLUDED.subject_tests
                      OR gre.subject_reg_num IS DISTINCT FROM EXCLUDED.subject_reg_num
                      OR gre.subject_date IS DISTINCT FROM EXCLUDED.subject_date
                      OR gre.subject_scaled_score IS DISTINCT FROM EXCLUDED.subject_scaled_score
                      OR gre.subject_below IS DISTINCT FROM EXCLUDED.subject_below
                    THEN EXCLUDED.updated_at 
                    ELSE gre.updated_at 
                END
            """
            cursor.execute(
                gre_query,
                (
                    user_code,
                    str(int(gre_reg)),
                    gre_date,
                    convert_score(row.get("GRE Verbal Reasoning")),
                    convert_score(row.get("GRE Verbal Reasoning % Below")),
                    convert_score(row.get("GRE Quantitative Reasoning")),
                    convert_score(row.get("GRE Quantitative Reasoning % Below")),
                    convert_score(row.get("GRE Analytical Writing")),
                    convert_score(row.get("GRE Analytical Writing % Below")),
                    convert_score(row.get("GRE Subject Tests")),
                    (
                        str(int(row.get("GRE (Subject Tests) - Registration #")))
                        if pd.notna(row.get("GRE (Subject Tests) - Registration #"))
                        else None
                    ),
                    gre_subject_date,
                    convert_score(
                        row.get("GRE (Subject Tests) - Overall Scaled Score")
                    ),
                    convert_score(row.get("GRE (Subject Tests) - Overall % Below")),
                    current_time,
                    current_time,
                ),
            )

        # GMAT
        gmat_ref = row.get("GMAT Reference #")
        if pd.notna(gmat_ref):
            gmat_date = None
            if pd.notna(row.get("GMAT Date of Writing")):
                try:
                    gmat_date = pd.to_datetime(row.get("GMAT Date of Writing")).date()
                except:
                    gmat_date = None

            gmat_query = """
            INSERT INTO gmat (user_code, ref_num, date_written, total, integrated_reasoning, quantitative, verbal, writing, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_code) DO UPDATE SET
                ref_num = EXCLUDED.ref_num,
                date_written = EXCLUDED.date_written,
                total = EXCLUDED.total,
                integrated_reasoning = EXCLUDED.integrated_reasoning,
                quantitative = EXCLUDED.quantitative,
                verbal = EXCLUDED.verbal,
                writing = EXCLUDED.writing,
                updated_at = CASE 
                    WHEN gmat.ref_num IS DISTINCT FROM EXCLUDED.ref_num
                      OR gmat.date_written IS DISTINCT FROM EXCLUDED.date_written
                      OR gmat.total IS DISTINCT FROM EXCLUDED.total
                      OR gmat.integrated_reasoning IS DISTINCT FROM EXCLUDED.integrated_reasoning
                      OR gmat.quantitative IS DISTINCT FROM EXCLUDED.quantitative
                      OR gmat.verbal IS DISTINCT FROM EXCLUDED.verbal
                      OR gmat.writing IS DISTINCT FROM EXCLUDED.writing
                    THEN EXCLUDED.updated_at 
                    ELSE gmat.updated_at 
                END
            """
            cursor.execute(
                gmat_query,
                (
                    user_code,
                    str(int(gmat_ref)),
                    gmat_date,
                    convert_score(row.get("GMAT Total Score")),
                    convert_score(row.get("Integrated Reasoning")),
                    convert_score(row.get("Quantitative")),
                    convert_score(row.get("Verbal")),
                    convert_score(row.get("Analytical Writing Assessment")),
                    current_time,
                    current_time,
                ),
            )

    # Check if data changed after processing
        for table in tables_to_check:
            cursor.execute(f"SELECT updated_at FROM {table} WHERE user_code = %s", (user_code,))
            result = cursor.fetchone()
            new_timestamp = result[0] if result else None
            
            if old_timestamps[table] != new_timestamp:
                data_changed = True
                break

    except Exception as e:
        print(f"Error processing other test scores for {user_code}: {e}")
    
    return data_changed
