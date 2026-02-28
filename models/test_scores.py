"""
Test Scores Model

This module handles processing test scores from CSV data.
Uses the generic processor from utils/test_score_helpers for all test types.
"""

from utils.db_helpers import db_transaction
from utils.test_score_helpers import (
    process_test_score,
    process_all_test_scores,
    TOEFL_CONFIG,
    IELTS_CONFIG,
    MELAB_CONFIG,
    PTE_CONFIG,
    CAEL_CONFIG,
    CELPIP_CONFIG,
    ALT_ELPP_CONFIG,
    GRE_CONFIG,
    GMAT_CONFIG,
    convert_id_to_string,
)


def process_toefl_scores(user_code, row, cursor, current_time):
    """
    Process TOEFL test scores from CSV data.

    @param user_code: Unique identifier for the applicant
    @param row: Pandas DataFrame row containing CSV data
    @param cursor: Database cursor for executing queries
    @param current_time: Timestamp for created_at/updated_at
    @return: True if data changed, False otherwise
    """
    return process_test_score(user_code, row, cursor, current_time, TOEFL_CONFIG)


def process_ielts_scores(user_code, row, cursor, current_time):
    """
    Process IELTS test scores from CSV data.

    @param user_code: Unique identifier for the applicant
    @param row: Pandas DataFrame row containing CSV data
    @param cursor: Database cursor for executing queries
    @param current_time: Timestamp for created_at/updated_at
    @return: True if data changed, False otherwise
    """
    return process_test_score(user_code, row, cursor, current_time, IELTS_CONFIG)


def process_other_test_scores(user_code, row, cursor, current_time):
    """
    Process other test scores (MELAB, PTE, CAEL, CELPIP, ALT ELPP, GRE, GMAT).

    @param user_code: Unique identifier for the applicant
    @param row: Pandas DataFrame row containing CSV data
    @param cursor: Database cursor for executing queries
    @param current_time: Timestamp for created_at/updated_at
    @return: True if any data changed, False otherwise
    """
    changed = False

    # Process each test type
    other_configs = [
        MELAB_CONFIG,
        PTE_CONFIG,
        CAEL_CONFIG,
        CELPIP_CONFIG,
        ALT_ELPP_CONFIG,
        GRE_CONFIG,
        GMAT_CONFIG,
    ]

    for config in other_configs:
        if process_test_score(user_code, row, cursor, current_time, config):
            changed = True

    return changed


def save_duolingo_score(user_code, score, description, date_written, current_time):
    """
    Upsert a Duolingo score record.

    @param user_code: Unique identifier for the applicant
    @param score: Duolingo test score (int, 0-160, or None)
    @param description: Test description or notes
    @param date_written: Test date (date object or None)
    @param current_time: Timestamp for updated_at
    """
    with db_transaction() as (conn, cursor):
        cursor.execute(
            """
            INSERT INTO duolingo (user_code, score, description, date_written, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_code) DO UPDATE SET
                score = EXCLUDED.score,
                description = EXCLUDED.description,
                date_written = EXCLUDED.date_written,
                updated_at = EXCLUDED.updated_at
            """,
            (user_code, score, description, date_written, current_time, current_time),
        )


# Re-export for convenience
__all__ = [
    'process_toefl_scores',
    'process_ielts_scores',
    'process_other_test_scores',
    'process_all_test_scores',
    'convert_id_to_string',
]
