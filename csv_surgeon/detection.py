"""Encoding, delimiter, and header detection functions."""

import chardet
import statistics
from typing import List
from csv_surgeon.core import DetectionResult
from csv_surgeon.exceptions import EncodingDetectionError

def detect_encoding(file_path: str, sample_size: int = 100000) -> DetectionResult:
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(sample_size)
    except IOError as e:
        raise EncodingDetectionError(f"Cannot read file: {e}")
    if not raw_data:
        raise EncodingDetectionError("File is empty")
    result = chardet.detect(raw_data)
    encoding = result.get('encoding')
    confidence = result.get('confidence', 0.0)
    if encoding is None or confidence < 0.5:
        fallback_chain = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
        for fallback_encoding in fallback_chain:
            try:
                raw_data.decode(fallback_encoding)
                return DetectionResult(
                    value=fallback_encoding,
                    confidence=0.6,
                    method="fallback"
                )
            except (UnicodeDecodeError, LookupError):
                continue
        raise EncodingDetectionError("Cannot determine encoding with confidence")
    return DetectionResult(
        value=encoding,
        confidence=confidence,
        method="chardet"
    )

def detect_delimiter(file_path: str, encoding: str = 'utf-8', sample_lines: int = 100) -> DetectionResult:
    candidate_delimiters = [',', ';', '\t', '|']
    delimiter_scores = {}
    try:
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            all_lines = []
            for _ in range(sample_lines):
                line = f.readline()
                if not line:
                    break
                stripped = line.strip()
                if stripped:
                    all_lines.append(stripped)
            lines = all_lines
    except IOError:
        return DetectionResult(value=',', confidence=0.5, method="default")
    if not lines:
        return DetectionResult(value=',', confidence=0.5, method="default")
    for delimiter in candidate_delimiters:
        counts = [line.count(delimiter) for line in lines]
        if all(c == 0 for c in counts):
            delimiter_scores[delimiter] = float('inf')
            continue
        if len(set(counts)) == 1:
            delimiter_scores[delimiter] = 0.0
        else:
            mean_count = statistics.mean(counts)
            if mean_count == 0:
                delimiter_scores[delimiter] = float('inf')
            else:
                stdev = statistics.stdev(counts) if len(counts) > 1 else 0
                cv = stdev / mean_count
                delimiter_scores[delimiter] = cv
    best_delimiter = min(delimiter_scores.items(), key=lambda x: x[1])
    delimiter_char = best_delimiter[0]
    cv_score = best_delimiter[1]
    if cv_score == float('inf'):
        confidence = 0.5
    elif cv_score == 0.0:
        confidence = 0.99
    else:
        confidence = max(0.5, min(0.99, 1.0 - cv_score))
    return DetectionResult(
        value=delimiter_char,
        confidence=confidence,
        method="statistical_cv"
    )

def detect_header(lines: List[str], delimiter: str) -> bool:
    if len(lines) < 2:
        return False
    first_row = lines[0].split(delimiter)
    if len(lines) < 3:
        return True
    data_rows = [line.split(delimiter) for line in lines[1:min(10, len(lines))]]
    if not data_rows:
        return False
    first_row_all_strings = all(_looks_like_string(cell) for cell in first_row)
    data_has_numbers = False
    for row in data_rows:
        if any(_looks_like_number(cell) for cell in row[:len(first_row)]):
            data_has_numbers = True
            break
    return first_row_all_strings and data_has_numbers

def _looks_like_number(value: str) -> bool:
    value = value.strip().strip('"').strip("'")
    if not value:
        return False
    try:
        float(value)
        return True
    except ValueError:
        return False

def _looks_like_string(value: str) -> bool:
    value = value.strip().strip('"').strip("'")
    if not value:
        return True
    try:
        float(value)
        return False
    except ValueError:
        return True
