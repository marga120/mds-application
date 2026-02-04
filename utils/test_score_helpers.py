"""
Test Score Processing Utilities

This module provides a generic, config-driven approach to processing test scores
from CSV data, replacing the repetitive individual functions for each test type.

Usage:
    from utils.test_score_helpers import process_test_score, TestScoreConfig

    # Define configuration for a test type
    TOEFL_CONFIG = TestScoreConfig(
        table_name='toefl',
        number_field='toefl_number',
        max_entries=3,
        prefix_pattern='TOEFL',  # TOEFL, TOEFL2, TOEFL3
        fields=[
            ScoreField('registration_num', 'Registration #', 'id'),
            ScoreField('total_score', 'Total Score', 'score'),
            ...
        ]
    )

    # Process scores
    changed = process_test_score(user_code, row, cursor, current_time, TOEFL_CONFIG)
"""

import pandas as pd
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Any


def convert_id_to_string(value):
    """Convert ID numbers to clean strings, removing .0 from floats."""
    if pd.isna(value):
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def convert_score(value):
    """Convert score values to strings if they exist, otherwise None."""
    return str(value) if pd.notna(value) else None


def parse_date(value):
    """Parse a date value from CSV, returning None if invalid."""
    if pd.isna(value):
        return None
    try:
        return pd.to_datetime(value).date()
    except:
        return None


@dataclass
class ScoreField:
    """
    Configuration for a single field in a test score table.

    @param db_column: Column name in the database table
    @param csv_suffix: Suffix to append to prefix for CSV column name
    @param field_type: Type of field - 'id', 'score', 'date'
    @param csv_column_override: Full CSV column name (overrides prefix + suffix)
    """
    db_column: str
    csv_suffix: str
    field_type: str = 'score'  # 'id', 'score', 'date'
    csv_column_override: Optional[str] = None

    def get_csv_column(self, prefix: str) -> str:
        """Get the full CSV column name for this field."""
        if self.csv_column_override:
            return self.csv_column_override
        return f"{prefix} {self.csv_suffix}"

    def extract_value(self, row, prefix: str):
        """Extract and convert value from CSV row."""
        csv_col = self.get_csv_column(prefix)
        value = row.get(csv_col)

        if self.field_type == 'id':
            return convert_id_to_string(value)
        elif self.field_type == 'date':
            return parse_date(value)
        else:  # score
            return convert_score(value)


@dataclass
class TestScoreConfig:
    """
    Configuration for processing a specific test type.

    @param table_name: Database table name
    @param number_field: Column name for test number (e.g., 'toefl_number')
    @param max_entries: Maximum number of test entries (1-3)
    @param prefix_pattern: Base prefix for CSV columns
    @param fields: List of ScoreField configurations
    @param check_fields: Fields to check for determining if entry has data
    @param has_single_entry: True if test only has one entry (no number field)
    """
    table_name: str
    fields: List[ScoreField]
    number_field: Optional[str] = None
    max_entries: int = 1
    prefix_pattern: str = ''
    check_fields: List[str] = field(default_factory=list)
    has_single_entry: bool = True

    def get_prefix(self, entry_num: int) -> str:
        """Get the CSV column prefix for a given entry number."""
        if entry_num == 1:
            return self.prefix_pattern
        return f"{self.prefix_pattern}{entry_num}"


def build_insert_query(config: TestScoreConfig) -> str:
    """
    Build the INSERT ... ON CONFLICT query for a test score table.

    @param config: TestScoreConfig for the test type
    @return: SQL query string
    """
    columns = ['user_code']
    if not config.has_single_entry:
        columns.append(config.number_field)

    columns.extend([f.db_column for f in config.fields])
    columns.extend(['created_at', 'updated_at'])

    placeholders = ', '.join(['%s'] * len(columns))

    # Build the ON CONFLICT clause
    if config.has_single_entry:
        conflict_key = 'user_code'
    else:
        conflict_key = f"user_code, {config.number_field}"

    # Build UPDATE SET clause with change detection
    update_fields = [f.db_column for f in config.fields]
    update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_fields])

    # Build change detection for updated_at
    change_conditions = ' OR '.join([
        f"{config.table_name}.{col} IS DISTINCT FROM EXCLUDED.{col}"
        for col in update_fields
    ])

    query = f"""
    INSERT INTO {config.table_name} ({', '.join(columns)})
    VALUES ({placeholders})
    ON CONFLICT ({conflict_key}) DO UPDATE SET
        {update_set},
        updated_at = CASE
            WHEN {change_conditions}
            THEN EXCLUDED.updated_at
            ELSE {config.table_name}.updated_at
        END
    """

    return query


def has_score_data(row, config: TestScoreConfig, prefix: str) -> bool:
    """
    Check if a CSV row has any score data for the given test entry.

    @param row: CSV row (pandas Series or dict)
    @param config: TestScoreConfig for the test type
    @param prefix: CSV column prefix for this entry
    @return: True if any score data exists
    """
    if not config.check_fields:
        # Default: check all score fields
        check_fields = [f for f in config.fields if f.field_type == 'score']
    else:
        check_fields = [f for f in config.fields if f.db_column in config.check_fields]

    return any(pd.notna(row.get(f.get_csv_column(prefix))) for f in check_fields)


def get_old_records(cursor, config: TestScoreConfig, user_code: str) -> dict:
    """
    Get existing records for change detection.

    @return: Dictionary mapping entry number (or 0 for single) to updated_at timestamp
    """
    if config.has_single_entry:
        cursor.execute(
            f"SELECT updated_at FROM {config.table_name} WHERE user_code = %s",
            (user_code,)
        )
        result = cursor.fetchone()
        return {0: result[0] if result else None}
    else:
        cursor.execute(
            f"SELECT {config.number_field}, updated_at FROM {config.table_name} WHERE user_code = %s ORDER BY {config.number_field}",
            (user_code,)
        )
        return {r[0]: r[1] for r in cursor.fetchall()}


def get_new_records(cursor, config: TestScoreConfig, user_code: str) -> dict:
    """Get records after processing for change detection."""
    return get_old_records(cursor, config, user_code)


def process_test_score(user_code: str, row, cursor, current_time, config: TestScoreConfig) -> bool:
    """
    Generic function to process test scores from CSV data.

    @param user_code: Applicant's user code
    @param row: CSV row (pandas Series or dict)
    @param cursor: Database cursor
    @param current_time: Timestamp for created_at/updated_at
    @param config: TestScoreConfig for the test type
    @return: True if data changed, False otherwise
    """
    old_records = get_old_records(cursor, config, user_code)
    query = build_insert_query(config)

    entries_to_process = range(1, config.max_entries + 1) if not config.has_single_entry else [1]

    for entry_num in entries_to_process:
        prefix = config.get_prefix(entry_num)

        # Check if this entry has any score data
        if not has_score_data(row, config, prefix):
            continue

        # Build parameter values
        params = [user_code]
        if not config.has_single_entry:
            params.append(entry_num)

        for field_config in config.fields:
            params.append(field_config.extract_value(row, prefix))

        params.extend([current_time, current_time])

        cursor.execute(query, tuple(params))

    # Check for changes
    new_records = get_new_records(cursor, config, user_code)

    if len(old_records) != len(new_records):
        return True

    for key, new_ts in new_records.items():
        if old_records.get(key) != new_ts:
            return True

    return False


# =============================================================================
# Pre-configured Test Score Configurations
# =============================================================================

TOEFL_CONFIG = TestScoreConfig(
    table_name='toefl',
    number_field='toefl_number',
    max_entries=3,
    prefix_pattern='TOEFL',
    has_single_entry=False,
    check_fields=['total_score', 'listening', 'structure_written', 'reading', 'speaking'],
    fields=[
        ScoreField('registration_num', 'Registration #', 'id'),
        ScoreField('date_written', 'Date of Writing', 'date'),
        ScoreField('total_score', 'Total Score', 'score'),
        ScoreField('listening', 'Listening', 'score'),
        ScoreField('structure_written', 'Structure/Written', 'score'),
        ScoreField('reading', 'Reading', 'score'),
        ScoreField('speaking', 'Speaking', 'score'),
        ScoreField('mybest_total', 'MyBest Total Score', 'score'),
        ScoreField('mybest_date', 'MyBest as of Date', 'date'),
        ScoreField('mybest_listening', 'MyBest Listening Score', 'score'),
        ScoreField('mybest_listening_date', 'MyBest Listening Date', 'date'),
        ScoreField('mybest_writing', 'MyBest Writing Score', 'score'),
        ScoreField('mybest_writing_date', 'MyBest Writing Date', 'date'),
        ScoreField('mybest_reading', 'MyBest Reading Score', 'score'),
        ScoreField('mybest_reading_date', 'MyBest Reading Date', 'date'),
        ScoreField('mybest_speaking', 'MyBest Speaking Score', 'score'),
        ScoreField('mybest_speaking_date', 'MyBest Speaking Date', 'date'),
    ]
)

IELTS_CONFIG = TestScoreConfig(
    table_name='ielts',
    number_field='ielts_number',
    max_entries=3,
    prefix_pattern='IELTS',
    has_single_entry=False,
    check_fields=['total_band_score', 'listening', 'reading', 'writing', 'speaking'],
    fields=[
        ScoreField('candidate_num', 'Candidate #', 'id'),
        ScoreField('date_written', 'Date of Writing', 'date'),
        ScoreField('total_band_score', 'Total Band Score', 'score'),
        ScoreField('listening', 'Listening', 'score'),
        ScoreField('reading', 'Reading', 'score'),
        ScoreField('writing', 'Writing', 'score'),
        ScoreField('speaking', 'Speaking', 'score'),
    ]
)

MELAB_CONFIG = TestScoreConfig(
    table_name='melab',
    prefix_pattern='MELAB',
    has_single_entry=True,
    check_fields=['total'],
    fields=[
        ScoreField('ref_num', 'Reference #', 'id'),
        ScoreField('date_written', 'Date of Writing', 'date'),
        ScoreField('total', 'Total Score', 'score'),
    ]
)

PTE_CONFIG = TestScoreConfig(
    table_name='pte',
    prefix_pattern='PTE',
    has_single_entry=True,
    check_fields=['total'],
    fields=[
        ScoreField('ref_num', 'Reference #', 'id'),
        ScoreField('date_written', 'Date of Writing', 'date'),
        ScoreField('total', 'Total Score', 'score'),
    ]
)

CAEL_CONFIG = TestScoreConfig(
    table_name='cael',
    prefix_pattern='CAEL',
    has_single_entry=True,
    check_fields=['reading', 'listening', 'writing', 'speaking'],
    fields=[
        ScoreField('ref_num', 'Reference #', 'id'),
        ScoreField('date_written', 'Date of Writing', 'date'),
        ScoreField('reading', 'Reading Performance Score', 'score'),
        ScoreField('listening', 'Listening Performance Score', 'score'),
        ScoreField('writing', 'Writing Performance Score', 'score'),
        ScoreField('speaking', 'Speaking Performance Score', 'score'),
    ]
)

CELPIP_CONFIG = TestScoreConfig(
    table_name='celpip',
    prefix_pattern='CELPIP',
    has_single_entry=True,
    check_fields=['listening', 'speaking', 'reading_writing'],
    fields=[
        ScoreField('ref_num', 'Reference #', 'id'),
        ScoreField('date_written', 'Date of Writing', 'date'),
        ScoreField('listening', 'Listening Score', 'score'),
        ScoreField('speaking', 'Speaking Score', 'score'),
        ScoreField('reading_writing', 'Academic Reading & Writing Score', 'score'),
    ]
)

ALT_ELPP_CONFIG = TestScoreConfig(
    table_name='alt_elpp',
    prefix_pattern='ALT ELPP',
    has_single_entry=True,
    check_fields=['total', 'test_type'],
    fields=[
        ScoreField('ref_num', 'Reference #', 'id'),
        ScoreField('date_written', 'Date of Writing', 'date'),
        ScoreField('total', 'Total Score', 'score'),
        ScoreField('test_type', 'Test Type', 'score'),
    ]
)

GRE_CONFIG = TestScoreConfig(
    table_name='gre',
    prefix_pattern='GRE',
    has_single_entry=True,
    check_fields=['verbal', 'quantitative', 'writing', 'subject_scaled_score'],
    fields=[
        ScoreField('reg_num', 'Registration #', 'id'),
        ScoreField('date_written', 'Date of Writing', 'date'),
        ScoreField('verbal', 'Verbal Reasoning', 'score'),
        ScoreField('verbal_below', 'Verbal Reasoning % Below', 'score'),
        ScoreField('quantitative', 'Quantitative Reasoning', 'score'),
        ScoreField('quantitative_below', 'Quantitative Reasoning % Below', 'score'),
        ScoreField('writing', 'Analytical Writing', 'score'),
        ScoreField('writing_below', 'Analytical Writing % Below', 'score'),
        ScoreField('subject_tests', 'Subject Tests', 'score'),
        ScoreField('subject_reg_num', '(Subject Tests) - Registration #', 'id'),
        ScoreField('subject_date', '(Subject Tests) - Date of Test', 'date'),
        ScoreField('subject_scaled_score', '(Subject Tests) - Overall Scaled Score', 'score'),
        ScoreField('subject_below', '(Subject Tests) - Overall % Below', 'score'),
    ]
)

GMAT_CONFIG = TestScoreConfig(
    table_name='gmat',
    prefix_pattern='GMAT',
    has_single_entry=True,
    check_fields=['total', 'integrated_reasoning', 'quantitative', 'verbal', 'writing'],
    fields=[
        ScoreField('ref_num', 'Reference #', 'id'),
        ScoreField('date_written', 'Date of Writing', 'date'),
        ScoreField('total', 'Total Score', 'score'),
        # Note: These use different column naming in CSV
        ScoreField('integrated_reasoning', 'Integrated Reasoning', 'score', csv_column_override='Integrated Reasoning'),
        ScoreField('quantitative', 'Quantitative', 'score', csv_column_override='Quantitative'),
        ScoreField('verbal', 'Verbal', 'score', csv_column_override='Verbal'),
        ScoreField('writing', 'Analytical Writing Assessment', 'score', csv_column_override='Analytical Writing Assessment'),
    ]
)


# Dictionary for easy lookup
TEST_SCORE_CONFIGS = {
    'toefl': TOEFL_CONFIG,
    'ielts': IELTS_CONFIG,
    'melab': MELAB_CONFIG,
    'pte': PTE_CONFIG,
    'cael': CAEL_CONFIG,
    'celpip': CELPIP_CONFIG,
    'alt_elpp': ALT_ELPP_CONFIG,
    'gre': GRE_CONFIG,
    'gmat': GMAT_CONFIG,
}


def process_all_test_scores(user_code: str, row, cursor, current_time) -> bool:
    """
    Process all test scores for an applicant.

    @param user_code: Applicant's user code
    @param row: CSV row
    @param cursor: Database cursor
    @param current_time: Timestamp
    @return: True if any data changed
    """
    changed = False
    for config in TEST_SCORE_CONFIGS.values():
        if process_test_score(user_code, row, cursor, current_time, config):
            changed = True
    return changed
