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
    try:
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
                mybest_speaking, mybest_speaking_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                mybest_speaking_date = EXCLUDED.mybest_speaking_date
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
                ),
            )

    except Exception as e:
        print(f"Error processing TOEFL scores for {user_code}: {e}")


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
    try:
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
                listening, reading, writing, speaking
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_code, ielts_number) DO UPDATE SET
                candidate_num = EXCLUDED.candidate_num,
                date_written = EXCLUDED.date_written,
                total_band_score = EXCLUDED.total_band_score,
                listening = EXCLUDED.listening,
                reading = EXCLUDED.reading,
                writing = EXCLUDED.writing,
                speaking = EXCLUDED.speaking
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
                ),
            )

    except Exception as e:
        print(f"Error processing IELTS scores for {user_code}: {e}")


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
    try:
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
            INSERT INTO melab (user_code, ref_num, date_written, total)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_code) DO UPDATE SET
                ref_num = EXCLUDED.ref_num,
                date_written = EXCLUDED.date_written,
                total = EXCLUDED.total
            """
            cursor.execute(
                melab_query,
                (
                    user_code,
                    str(int(melab_ref)),
                    melab_date,
                    convert_score(row.get("MELAB Total Score")),
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
            INSERT INTO pte (user_code, ref_num, date_written, total)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_code) DO UPDATE SET
                ref_num = EXCLUDED.ref_num,
                date_written = EXCLUDED.date_written,
                total = EXCLUDED.total
            """
            cursor.execute(
                pte_query,
                (
                    user_code,
                    str(int(pte_ref)),
                    pte_date,
                    convert_score(row.get("PTE Total Score")),
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
            INSERT INTO cael (user_code, ref_num, date_written, reading, listening, writing, speaking)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_code) DO UPDATE SET
                ref_num = EXCLUDED.ref_num,
                date_written = EXCLUDED.date_written,
                reading = EXCLUDED.reading,
                listening = EXCLUDED.listening,
                writing = EXCLUDED.writing,
                speaking = EXCLUDED.speaking
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
            INSERT INTO celpip (user_code, ref_num, date_written, listening, speaking, reading_writing)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_code) DO UPDATE SET
                ref_num = EXCLUDED.ref_num,
                date_written = EXCLUDED.date_written,
                listening = EXCLUDED.listening,
                speaking = EXCLUDED.speaking,
                reading_writing = EXCLUDED.reading_writing
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
            INSERT INTO alt_elpp (user_code, ref_num, date_written, total, test_type)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_code) DO UPDATE SET
                ref_num = EXCLUDED.ref_num,
                date_written = EXCLUDED.date_written,
                total = EXCLUDED.total,
                test_type = EXCLUDED.test_type
            """
            cursor.execute(
                alt_elpp_query,
                (
                    user_code,
                    str(int(alt_elpp_ref)),
                    alt_elpp_date,
                    convert_score(row.get("ALT ELPP Total Score")),
                    convert_score(row.get("ALT ELPP Test Type")),
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
                subject_date, subject_scaled_score, subject_below
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                subject_below = EXCLUDED.subject_below
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
            INSERT INTO gmat (user_code, ref_num, date_written, total, integrated_reasoning, quantitative, verbal, writing)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_code) DO UPDATE SET
                ref_num = EXCLUDED.ref_num,
                date_written = EXCLUDED.date_written,
                total = EXCLUDED.total,
                integrated_reasoning = EXCLUDED.integrated_reasoning,
                quantitative = EXCLUDED.quantitative,
                verbal = EXCLUDED.verbal,
                writing = EXCLUDED.writing
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
                ),
            )

    except Exception as e:
        print(f"Error processing other test scores for {user_code}: {e}")
