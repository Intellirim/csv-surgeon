"""CSV repair functions."""

import os
from typing import Optional
from csv_surgeon.core import RepairResult, calculate_column_counts, find_mode_columns, sanitize_pii, DetectionResult
from csv_surgeon.detection import detect_encoding, detect_delimiter, detect_header
from csv_surgeon.exceptions import UnrepairableFileError

class RepairEngine:
    def __init__(self, force_encoding: Optional[str] = None, force_delimiter: Optional[str] = None):
        self.force_encoding = force_encoding
        self.force_delimiter = force_delimiter

    def repair(self, file_path: str, sanitize: bool = False, output_encoding: Optional[str] = None) -> RepairResult:
        if not os.path.exists(file_path):
            raise UnrepairableFileError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size > 100 * 1024 * 1024:
            pass

        try:
            encoding_result = self._detect_or_use_encoding(file_path)
        except Exception as e:
            raise UnrepairableFileError(f"Cannot detect encoding: {e}")
        delimiter_result = self._detect_or_use_delimiter(file_path, encoding_result.value)
        try:
            with open(file_path, 'r', encoding=encoding_result.value, errors='replace') as f:
                lines = []
                for line in f:
                    lines.append(line.rstrip('\n\r'))
        except IOError as e:
            raise UnrepairableFileError(f"Cannot read file: {e}")
        if not lines:
            raise UnrepairableFileError("File is empty")
        repaired_lines, quote_repairs = self._repair_quotes(lines, delimiter_result.value)
        reconstructed_lines, record_reconstructions = self._reconstruct_records(
            repaired_lines, delimiter_result.value
        )
        has_header = detect_header(reconstructed_lines, delimiter_result.value)
        if sanitize:
            reconstructed_lines, pii_counts = self._sanitize_lines(reconstructed_lines)
            pii_sanitized = {
                'emails': pii_counts['emails'],
                'phones': pii_counts['phones'],
                'ssns': pii_counts['ssns'],
                'credit_cards': pii_counts['credit_cards']
            }
        else:
            pii_sanitized = None
        output_data = '\n'.join(reconstructed_lines)
        if output_encoding and output_encoding.lower() != encoding_result.value.lower():
            output_data = output_data.encode(encoding_result.value, errors='replace').decode(
                output_encoding, errors='replace'
            )
        return RepairResult(
            repaired_rows=len(reconstructed_lines),
            malformed_quotes=quote_repairs,
            reconstructed_records=record_reconstructions,
            encoding_detected=encoding_result.value,
            encoding_confidence=encoding_result.confidence,
            delimiter_detected=delimiter_result.value,
            delimiter_confidence=delimiter_result.confidence,
            has_header=has_header,
            output_data=output_data,
            pii_sanitized=pii_sanitized
        )

    def _detect_or_use_encoding(self, file_path: str):
        if self.force_encoding:
            return DetectionResult(value=self.force_encoding, confidence=1.0, method="forced")
        return detect_encoding(file_path)

    def _detect_or_use_delimiter(self, file_path: str, encoding: str):
        if self.force_delimiter:
            return DetectionResult(value=self.force_delimiter, confidence=1.0, method="forced")
        return detect_delimiter(file_path, encoding)

    def _repair_quotes(self, lines: list[str], delimiter: str) -> tuple[list[str], int]:
        repaired = []
        repairs = 0
        for line in lines:
            repaired_line, line_repairs = self._repair_line_quotes(line, delimiter)
            repaired.append(repaired_line)
            repairs += line_repairs
        return repaired, repairs

    def _repair_line_quotes(self, line: str, delimiter: str) -> tuple[str, int]:
        quote_count = line.count('"')
        if quote_count % 2 == 0:
            return line, 0
        last_delimiter_pos = line.rfind(delimiter)
        if last_delimiter_pos == -1:
            return line + '"', 1
        if line.count('"', last_delimiter_pos) % 2 == 1:
            return line + '"', 1
        first_quote_pos = line.find('"')
        if first_quote_pos > 0 and line[first_quote_pos - 1] != delimiter and first_quote_pos != 0:
            return '"' + line, 1
        return line + '"', 1

    def _reconstruct_records(self, lines: list[str], delimiter: str) -> tuple[list[str], int]:
        column_counts = calculate_column_counts(lines, delimiter)
        expected_columns = find_mode_columns(column_counts)
        reconstructed = []
        reconstructions = 0
        i = 0
        while i < len(lines):
            current_line = lines[i]
            current_columns = column_counts[i]
            if current_columns == expected_columns:
                reconstructed.append(current_line)
                i += 1
            else:
                merged_line = current_line
                j = i + 1
                while j < len(lines) and merged_line.count(delimiter) + 1 != expected_columns:
                    merged_line += ' ' + lines[j]
                    j += 1
                reconstructed.append(merged_line)
                if j > i + 1:
                    reconstructions += 1
                i = j
        return reconstructed, reconstructions

    def _sanitize_lines(self, lines: list[str]) -> tuple[list[str], dict]:
        sanitized = []
        total_counts = {'emails': 0, 'phones': 0, 'ssns': 0, 'credit_cards': 0}
        for line in lines:
            sanitized_line, counts = sanitize_pii(line)
            sanitized.append(sanitized_line)
            for key in total_counts:
                total_counts[key] += counts[key]
        return sanitized, total_counts

def repair_file(file_path: str, output_path: Optional[str] = None,
                force_encoding: Optional[str] = None,
                force_delimiter: Optional[str] = None,
                sanitize_pii_data: bool = False,
                output_encoding: str = 'utf-8') -> RepairResult:
    engine = RepairEngine(force_encoding=force_encoding, force_delimiter=force_delimiter)
    result = engine.repair(file_path, sanitize=sanitize_pii_data, output_encoding=output_encoding)
    if output_path:
        with open(output_path, 'w', encoding=output_encoding) as f:
            f.write(result.output_data)
    return result
