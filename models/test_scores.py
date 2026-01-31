"""
Test Scores Model

This module handles processing test scores from CSV data.
Uses the generic processor from utils/test_score_helpers for all test types.
"""

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


# Re-export for convenience
__all__ = [
    'process_toefl_scores',
    'process_ielts_scores',
    'process_other_test_scores',
    'process_a l_test_scores',
    'convert_id_to_string',
]
