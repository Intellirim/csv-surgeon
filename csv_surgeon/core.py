"""Core data models and utility functions for CSV Surgeon."""

import re
import statistics
from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class DetectionResult:
    value: str
    confidence: float
    method: str = "auto"

@dataclass
class RepairResult:
    repaired_rows: int
    malformed_quotes: int = 0
    reconstructed_records: int = 0
    encoding_detected: str = "utf-8"
    encoding_confidence: float = 0.0
    delimiter_detected: str = ","
    delimiter_confidence: float = 0.0
    has_header: bool = False
    output_data: str = ""
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    pii_sanitized: Optional[Dict[str, int]] = None

@dataclass
class StructureIssue:
    line_number: int
    issue_type: str
    description: str

def calculate_column_counts(lines: List[str], delimiter: str) -> List[int]:
    return [line.count(delimiter) + 1 for line in lines]

def find_mode_columns(column_counts: List[int]) -> int:
    if not column_counts:
        return 0
    try:
        return statistics.mode(column_counts)
    except statistics.StatisticsError:
        return max(set(column_counts), key=column_counts.count)

def validate_column_consistency(lines: List[str], delimiter: str, expected_columns: int = None):
    column_counts = calculate_column_counts(lines, delimiter)
    if expected_columns is None:
        expected_columns = find_mode_columns(column_counts)
    inconsistent_lines = [i for i, count in enumerate(column_counts) if count != expected_columns]
    return expected_columns, inconsistent_lines

def detect_unclosed_quotes(line: str) -> int:
    return line.count('"') % 2

def find_structure_issues(lines: List[str], delimiter: str) -> List[StructureIssue]:
    issues = []
    expected_columns, inconsistent_indices = validate_column_consistency(lines, delimiter)
    for idx in inconsistent_indices:
        actual_count = lines[idx].count(delimiter) + 1
        issues.append(StructureIssue(
            line_number=idx + 1,
            issue_type="column_mismatch",
            description=f"Expected {expected_columns} columns, found {actual_count}"
        ))
    for idx, line in enumerate(lines):
        if detect_unclosed_quotes(line):
            issues.append(StructureIssue(
                line_number=idx + 1,
                issue_type="unclosed_quote",
                description="Line contains unclosed quote"
            ))
    return issues

def infer_data_type(value: str) -> str:
    value = value.strip().strip('"').strip("'")
    if not value:
        return 'empty'
    if value.lower() in ('true', 'false', 'yes', 'no'):
        return 'bool'
    try:
        int(value)
        return 'int'
    except ValueError:
        pass
    try:
        float(value)
        return 'float'
    except ValueError:
        pass
    return 'string'

def sanitize_pii(text: str):
    counts = {'emails': 0, 'phones': 0, 'ssns': 0, 'credit_cards': 0}

    email_pattern = r'(?<![A-Za-z0-9@.])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}(?![A-Za-z0-9@.])'
    emails = re.findall(email_pattern, text)
    text = re.sub(email_pattern, '[REDACTED_EMAIL]', text)
    counts['emails'] = len(emails)

    phone_patterns = [
        r'\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b',
        r'\(\d{3}\)\s?\d{3}[-.\s]\d{4}',
        r'\b\+\d{1,3}[-.\s]\d{1,4}[-.\s]\d{1,4}[-.\s]\d{4,9}\b'
    ]
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        counts['phones'] += len(matches)
        text = re.sub(pattern, '[REDACTED_PHONE]', text)

    ssn_pattern = r'(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)'
    ssns = re.findall(ssn_pattern, text)
    text = re.sub(ssn_pattern, '[REDACTED_SSN]', text)
    counts['ssns'] = len(ssns)

    return text, counts
