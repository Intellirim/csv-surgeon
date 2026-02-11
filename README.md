# CSV Surgeon

Intelligent CSV repair and sanitization for broken data files

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

CSV Surgeon is a CLI tool that automatically detects and repairs broken CSV files with encoding issues, delimiter mismatches, malformed quotes, embedded linebreaks, and structural inconsistencies. Unlike web-based tools or manual approaches, it uses statistical analysis and heuristic algorithms to infer correct file structure, normalize encodings, and reconstruct malformed records while preserving data integrity.

## Installation

```bash
pip install csv-surgeon
```

## Usage

```bash
# Repair broken CSV
csv-surgeon repair broken.csv

# Save to file with encoding
csv-surgeon repair data.csv -o cleaned.csv --encoding utf-8

# Analyze without repair
csv-surgeon analyze messy.csv

# Redact PII
csv-surgeon repair input.csv --delimiter , --sanitize-pii
```

## Features

- **Multi-pass encoding detection**: Uses chardet with fallback chain (UTF-8, UTF-16, Latin-1, CP1252) and confidence scoring
- **Statistical delimiter inference**: Tests 4 delimiter types (comma, semicolon, tab, pipe) using coefficient of variation
- **Context-aware quote repair**: Detects and repairs unclosed quotes using delimiter-aware heuristics
- **Embedded linebreak reconstruction**: Merges records split across multiple lines using column count consistency
- **Header auto-detection**: Distinguishes headers from data using type consistency analysis
- **PII sanitization**: Detects and redacts emails, phone numbers (3 formats), and SSNs using regex patterns
- **Detailed reporting**: Provides confidence scores (0.0-1.0) for encoding and delimiter detection
- **Error handling**: Gracefully handles permission errors, empty files, and binary files

## How It Works

Uses chardet for encoding detection, statistical analysis for delimiter inference (coefficient of variation), state machine for quote repair, and column count mode for record reconstruction.

## Why CSV Surgeon?

Unlike RepairMyCSV (web-only), csvkit (complex), OpenRefine (GUI), or Excel (manual), CSV Surgeon combines automatic detection, CLI automation, and intelligent algorithms in one simple tool.

## License

MIT License - Copyright (c) 2026 Intellirim
