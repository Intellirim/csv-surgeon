"""Custom exceptions for CSV Surgeon."""


class CSVSurgeonError(Exception):
    """Base exception for CSV Surgeon errors."""


class UnrepairableFileError(CSVSurgeonError):
    """Raised when a file cannot be repaired due to severe corruption."""


class EncodingDetectionError(CSVSurgeonError):
    """Raised when encoding detection fails."""


class StructureError(CSVSurgeonError):
    """Raised when CSV structure cannot be determined or is invalid."""
