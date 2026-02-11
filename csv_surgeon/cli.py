"""Command-line interface for CSV Surgeon."""

import click
import sys
import os
from csv_surgeon import __version__
from csv_surgeon.repair import repair_file
from csv_surgeon.detection import detect_encoding, detect_delimiter
from csv_surgeon.core import find_structure_issues, calculate_column_counts, find_mode_columns
from csv_surgeon.exceptions import UnrepairableFileError, EncodingDetectionError

@click.group()
@click.version_option(version=__version__, prog_name='csv-surgeon')
def cli():
    """CSV Surgeon - Intelligent CSV repair and sanitization for broken data files."""

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('-o', '--output', 'output_file', type=click.Path(), help='Output file path (default: stdout)')
@click.option('--encoding', type=str, help='Force output encoding (default: utf-8)')
@click.option('--delimiter', type=str, help='Force specific delimiter')
@click.option('--sanitize-pii', is_flag=True, help='Sanitize PII (emails, phones, SSNs)')
def repair(input_file, output_file, encoding, delimiter, sanitize_pii):
    """Repair a broken CSV file."""
    try:
        output_encoding = encoding or 'utf-8'
        result = repair_file(
            file_path=input_file,
            output_path=output_file,
            force_delimiter=delimiter,
            sanitize_pii_data=sanitize_pii,
            output_encoding=output_encoding
        )
        if delimiter:
            click.echo(f"Using forced delimiter: {delimiter}")
        else:
            click.echo(f"Detected delimiter: {result.delimiter_detected} (confidence: {result.delimiter_confidence:.2f})")
        click.echo(f"Detected encoding: {result.encoding_detected} (confidence: {result.encoding_confidence:.2f})")
        if encoding and encoding.lower() != result.encoding_detected.lower():
            click.echo(f"Converting from {result.encoding_detected} to {encoding}")
        if result.malformed_quotes > 0:
            click.echo(f"Repaired {result.malformed_quotes} malformed quote pairs")
        if result.reconstructed_records > 0:
            click.echo(f"Reconstructed {result.reconstructed_records} records with embedded linebreaks")
        click.echo(f"Repaired {result.repaired_rows} rows successfully")
        if sanitize_pii and result.pii_sanitized and sum(result.pii_sanitized.values()) > 0:
            pii_details = [f"{v} {k}" for k, v in result.pii_sanitized.items() if v > 0]
            click.echo(f"Sanitized PII: {', '.join(pii_details)}")
        if output_file:
            click.echo(f"\nOutput written to: {output_file}")
        else:
            click.echo()
            click.echo(result.output_data)
    except (UnrepairableFileError, EncodingDetectionError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except PermissionError as e:
        click.echo(f"Permission denied: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--html', is_flag=True, help='Generate HTML report and open in browser')
def analyze(input_file, html):
    """Analyze a CSV file and show diagnostics without repairing."""
    try:
        file_size = os.path.getsize(input_file)
        try:
            encoding_result = detect_encoding(input_file)
        except EncodingDetectionError as e:
            click.echo(f"Error detecting encoding: {e}", err=True)
            sys.exit(1)
        with open(input_file, 'r', encoding=encoding_result.value, errors='replace') as f:
            lines = [line.rstrip('\n\r') for line in f.readlines()]
        total_lines = len(lines)
        click.echo(f"File: {input_file} ({file_size // 1024} KB, {total_lines:,} lines)")
        click.echo()
        click.echo("Encoding Analysis:")
        click.echo(f"  Detected: {encoding_result.value} (confidence: {encoding_result.confidence:.2f})")
        if encoding_result.confidence < 0.8:
            click.echo(f"  Warning: Low confidence encoding detection")
        click.echo()
        click.echo("Delimiter Analysis:")
        delimiter_result = detect_delimiter(input_file, encoding_result.value)
        delim_names = {',': 'Comma', ';': 'Semicolon', '\t': 'Tab', '|': 'Pipe'}
        for delim in [',', ';', '\t', '|']:
            if delim == delimiter_result.value:
                cv = 1.0 - delimiter_result.confidence
                click.echo(f"  {delim_names[delim]}: CV={cv:.2f} (likely correct)")
            else:
                click.echo(f"  {delim_names.get(delim, delim)}: (not selected)")
        issues = find_structure_issues(lines, delimiter_result.value)
        click.echo()
        click.echo("Structure Issues:")
        column_counts = calculate_column_counts(lines, delimiter_result.value)
        expected_columns = find_mode_columns(column_counts)
        click.echo(f"  Expected columns: {expected_columns}")
        column_mismatches = [i for i in issues if i.issue_type == "column_mismatch"]
        quote_issues = [i for i in issues if i.issue_type == "unclosed_quote"]
        if column_mismatches:
            nums = ', '.join(str(i.line_number) for i in column_mismatches[:5])
            click.echo(f"  Inconsistent rows: {len(column_mismatches)} (lines: {nums}...)")
            click.echo(f"  Embedded linebreaks: ~{len(column_mismatches) // 2} records")
        else:
            click.echo(f"  Inconsistent rows: 0")
        click.echo(f"  Unclosed quotes: {len(quote_issues)} pairs" if quote_issues else "  Unclosed quotes: 0")
        if html:
            import webbrowser
            from csv_surgeon.report import export_html
            preview = lines[:5] if lines else []
            report_path = export_html(
                file_path=input_file, file_size=file_size, total_lines=total_lines,
                encoding_name=encoding_result.value, encoding_conf=encoding_result.confidence,
                delimiter=delimiter_result.value, delimiter_conf=delimiter_result.confidence,
                expected_cols=expected_columns,
                column_mismatches=column_mismatches, quote_issues=quote_issues,
                preview_lines=preview,
            )
            click.echo(f"Report saved: {report_path}")
            webbrowser.open(f"file://{report_path}")
            return

        click.echo()
        click.echo("Recommendation: Run with default repair")
    except Exception as e:
        click.echo(f"Error analyzing file: {e}", err=True)
        sys.exit(1)

def main():
    """Entry point for console script."""
    cli()

if __name__ == '__main__':
    main()
