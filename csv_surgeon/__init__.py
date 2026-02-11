"""CSV Surgeon - Intelligent CSV repair and sanitization for broken data files."""

__version__ = "1.1.0"

from csv_surgeon.exceptions import (
    UnrepairableFileError,
    EncodingDetectionError,
    StructureError,
)
from csv_surgeon.core import RepairResult, DetectionResult
from csv_surgeon.repair import RepairEngine, repair_file
from csv_surgeon.detection import detect_encoding, detect_delimiter, detect_header

__all__ = [
    "__version__",
    "UnrepairableFileError",
    "EncodingDetectionError",
    "StructureError",
    "RepairResult",
    "DetectionResult",
    "RepairEngine",
    "repair_file",
    "detect_encoding",
    "detect_delimiter",
    "detect_header",
]
