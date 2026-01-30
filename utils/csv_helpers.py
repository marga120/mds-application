"""
CSV Export Utilities

This module provides shared utilities for CSV export operations,
eliminating duplicate clean_row() functions and standardizing CSV generation.

Usage:
    from utils.csv_helpers import clean_row, create_csv_response

    # Clean a row for CSV export
    cleaned = clean_row({"name": "John", "age": None, "score": float('nan')})
    # Result: {"name": "John", "age": "", "score": ""}

    # Create a Flask response with CSV data
    response = create_csv_response(rows, filename="export.csv")
"""

import csv
import io
import math
from datetime import datetime
from flask import make_response


def clean_value(value):
    """
    Clean a single value for CSV export.

    Converts None, NaN, and null-like values to empty strings.
    Handles datetime objects by converting to ISO format.

    @param value: Any value to clean
    @return: Cleaned value (empty string for null-like values)

    @example:
        clean_value(None)        # Returns ''
        clean_value(float('nan'))  # Returns ''
        clean_value('NaN')       # Returns ''
        clean_value(42)          # Returns 42
    """
    # Handle None
    if value is None:
        return ''

    # Handle string representations of null
    if isinstance(value, str):
        if value.lower() in ['nan', 'none', 'null', '']:
            return ''
        return value

    # Handle float NaN
    if isinstance(value, float):
        if math.isnan(value):
            return ''
        return value

    # Handle datetime objects
    if isinstance(value, datetime):
        return value.isoformat()

    return value


def clean_row(row):
    """
    Clean a dictionary row for CSV export.

    Converts None, NaN, and null values to empty strings for all keys.

    @param row: Dictionary with values to clean
    @return: New dictionary with cleaned values

    @example:
        row = {"name": "John", "age": None, "score": float('nan')}
        cleaned = clean_row(row)
        # Result: {"name": "John", "age": "", "score": ""}
    """
    return {k: clean_value(v) for k, v in row.items()}


def clean_rows(rows):
    """
    Clean multiple rows for CSV export.

    @param rows: List of dictionaries
    @return: List of cleaned dictionaries

    @example:
        rows = [{"a": None}, {"a": "value"}]
        cleaned = clean_rows(rows)
        # Result: [{"a": ""}, {"a": "value"}]
    """
    return [clean_row(row) for row in rows]


def rows_to_csv_string(rows, fieldnames=None):
    """
    Convert a list of dictionaries to a CSV string.

    @param rows: List of dictionaries to convert
    @param fieldnames: Optional list of column names (uses first row keys if not provided)
    @return: CSV string

    @example:
        rows = [{"name": "Alice", "score": 95}, {"name": "Bob", "score": 87}]
        csv_string = rows_to_csv_string(rows)
    """
    if not rows:
        return ""

    output = io.StringIO()

    # Determine headers
    if fieldnames is None:
        fieldnames = list(rows[0].keys())

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in rows:
        writer.writerow(clean_row(row))

    return output.getvalue()


def create_csv_response(rows, filename, fieldnames=None):
    """
    Create a Flask response with CSV content for download.

    @param rows: List of dictionaries to export
    @param filename: Name for the downloaded file
    @param fieldnames: Optional list of column names
    @return: Flask Response object with CSV content

    @example:
        @app.route('/export')
        def export():
            data = get_export_data()
            return create_csv_response(data, "applicants_export.csv")
    """
    csv_content = rows_to_csv_string(rows, fieldnames)

    response = make_response(csv_content)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'

    return response


def generate_export_filename(prefix, record_count=None, include_date=True):
    """
    Generate a standardized export filename.

    @param prefix: Filename prefix (e.g., 'applicants', 'ratings')
    @param record_count: Optional number of records for filename
    @param include_date: Whether to include date in filename
    @return: Generated filename string

    @example:
        generate_export_filename('applicants', 150)
        # Returns: 'applicants_150_records_2026-01-29.csv'

        generate_export_filename('export', include_date=False)
        # Returns: 'export.csv'
    """
    parts = [prefix]

    if record_count is not None:
        parts.append(f"{record_count}_records")

    if include_date:
        parts.append(datetime.now().strftime("%Y-%m-%d"))

    return '_'.join(parts) + '.csv'


class CSVWriter:
    """
    Context manager for building CSV content incrementally.

    Useful for complex exports with multiple sections or large datasets.

    @example:
        with CSVWriter() as writer:
            writer.writerow(['Header 1', 'Header 2'])
            writer.writerow(['Value 1', 'Value 2'])
            csv_content = writer.getvalue()
    """

    def __init__(self):
        self.output = io.StringIO()
        self.writer = csv.writer(self.output)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def writerow(self, row):
        """Write a single row to the CSV."""
        self.writer.writerow(row)

    def writerows(self, rows):
        """Write multiple rows to the CSV."""
        self.writer.writerows(rows)

    def write_dict_row(self, row, fieldnames):
        """Write a dictionary row with specified field order."""
        self.writer.writerow([clean_value(row.get(f, '')) for f in fieldnames])

    def write_header(self, headers):
        """Write a header row."""
        self.writer.writerow(headers)

    def write_spacer(self):
        """Write an empty row as a spacer."""
        self.writer.writerow([])

    def write_section_header(self, title):
        """Write a section header row."""
        self.writer.writerow([title])

    def getvalue(self):
        """Get the complete CSV content as a string."""
        return self.output.getvalue()

    def make_response(self, filename):
        """Create a Flask response with the CSV content."""
        response = make_response(self.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        return response
