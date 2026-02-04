"""
Applicants Model Module

This module provides the public API for applicant-related operations.
All functions are re-exported here for backward compatibility.

Usage:
    from models.applicants import get_all_applicant_status, process_csv_data
"""

# Core CRUD operations
from .core import (
    convert_id_to_string,
    get_all_applicant_status,
    get_all_sessions,
    get_applicant_info_by_code,
    get_applicant_test_scores_by_code,
    get_applicant_institutions_by_code,
    get_applicant_application_info_by_code,
    update_applicant_application_status,
    update_applicant_prerequisites,
    update_applicant_scholarship,
    update_english_comment,
    update_english_status,
    clear_all_applicant_data,
)

# CSV processing
from .csv_processing import (
    process_csv_data,
    calculate_age,
    create_or_get_sessions,
    calculate_application_info_fields,
    process_application_info,
)

# English status computation
from .english_status import (
    compute_english_status,
    compute_english_status_for_all,
)

# Export functions
from .export import (
    get_selected_applicants_for_export,
    get_all_applicants_complete_export,
)

__all__ = [
    # Core
    'convert_id_to_string',
    'get_all_applicant_status',
    'get_all_sessions',
    'get_applicant_info_by_code',
    'get_applicant_test_scores_by_code',
    'get_applicant_institutions_by_code',
    'get_applicant_application_info_by_code',
    'update_applicant_application_status',
    'update_applicant_prerequisites',
    'update_applicant_scholarship',
    'update_english_comment',
    'update_english_status',
    'clear_all_applicant_data',
    # CSV processing
    'process_csv_data',
    'calculate_age',
    'create_or_get_sessions',
    'calculate_application_info_fields',
    'process_application_info',
    # English status
    'compute_english_status',
    'compute_english_status_for_all',
    # Export
    'get_selected_applicants_for_export',
    'get_all_applicants_complete_export',
]
