import pytest
import os
from click.testing import CliRunner
from csv_surgeon.cli import cli, main
@pytest.fixture
def runner():
    return CliRunner()
def test_cli_version(runner):
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert 'csv-surgeon' in result.output.lower() or 'version' in result.output.lower()

def test_cli_help(runner):
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'repair' in result.output and 'analyze' in result.output


def test_repair_simple_csv(runner, temp_csv_file, simple_csv_data):
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(simple_csv_data)
    result = runner.invoke(cli, ['repair', temp_csv_file])
    assert result.exit_code == 0
    assert all(x in result.output for x in ['Detected delimiter', 'Detected encoding', 'Repaired', 'john@example.com'])
def test_repair_with_output_file(runner, temp_csv_file, simple_csv_data):
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(simple_csv_data)
    output_file = temp_csv_file + '.out'
    try:
        result = runner.invoke(cli, ['repair', temp_csv_file, '-o', output_file])
        assert result.exit_code == 0
        assert 'Output written to' in result.output
        assert os.path.exists(output_file)
        with open(output_file, 'r') as f:
            content = f.read()
            assert len(content) > 0
    finally:
        if os.path.exists(output_file):
            os.unlink(output_file)
def test_repair_with_forced_delimiter(runner, temp_csv_file):
    data = "a;b;c\n1;2;3"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    result = runner.invoke(cli, ['repair', temp_csv_file, '--delimiter', ';'])
    assert result.exit_code == 0
    assert 'Using forced delimiter: ;' in result.output
    assert 'Repaired' in result.output

def test_repair_with_pii_sanitization(runner, temp_csv_file, pii_data):
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(pii_data)
    result = runner.invoke(cli, ['repair', temp_csv_file, '--sanitize-pii'])
    assert result.exit_code == 0
    assert all(x in result.output for x in ['Sanitized PII', 'emails', '[REDACTED_EMAIL]'])
def test_repair_nonexistent_file(runner):
    result = runner.invoke(cli, ['repair', '/nonexistent/file.csv'])
    assert result.exit_code != 0
    assert result.exit_code == 2
def test_analyze_simple_csv(runner, temp_csv_file, simple_csv_data):
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(simple_csv_data)
    result = runner.invoke(cli, ['analyze', temp_csv_file])
    assert result.exit_code == 0
    assert all(x in result.output for x in ['File:', 'Encoding Analysis', 'Delimiter Analysis', 'Structure Issues', 'Recommendation'])

def test_analyze_nonexistent_file(runner):
    result = runner.invoke(cli, ['analyze', '/nonexistent/file.csv'])
    assert result.exit_code != 0
    assert result.exit_code == 2
def test_main_entry_point():
    result = CliRunner().invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'repair' in result.output
def test_repair_broken_quotes_file(runner, broken_quotes_file):
    result = runner.invoke(cli, ['repair', broken_quotes_file])
    assert result.exit_code == 0
    assert 'Repaired' in result.output and 'rows successfully' in result.output
def test_repair_mixed_delimiters_file(runner, mixed_delimiters_file):
    result = runner.invoke(cli, ['repair', mixed_delimiters_file])
    assert result.exit_code == 0
    assert 'Detected delimiter' in result.output and 'Repaired' in result.output

def test_repair_with_encoding_conversion(runner, temp_csv_file, simple_csv_data):
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(simple_csv_data)
    result = runner.invoke(cli, ['repair', temp_csv_file, '--encoding', 'latin-1'])
    assert result.exit_code == 0
    assert 'Converting from' in result.output or 'Repaired' in result.output

def test_analyze_with_encoding_issues(runner, temp_csv_file):
    with open(temp_csv_file, 'wb') as f:
        f.write("id,name\n".encode('utf-8'))
        f.write("1,Tëst\n".encode('utf-8'))
    result = runner.invoke(cli, ['analyze', temp_csv_file])
    assert result.exit_code == 0
    assert 'Encoding Analysis' in result.output

def test_cli_repair_stdout_output(runner, temp_csv_file, simple_csv_data):
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(simple_csv_data)
    result = runner.invoke(cli, ['repair', temp_csv_file])
    assert result.exit_code == 0
    assert 'john@example.com' in result.output
    assert 'jane@example.com' in result.output

def test_analyze_structure_issues(runner, temp_csv_file):
    data = "a,b,c\n1,2\n3,4,5"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    result = runner.invoke(cli, ['analyze', temp_csv_file])
    assert result.exit_code == 0
    assert 'Inconsistent rows' in result.output

def test_repair_empty_file_error(runner, temp_csv_file):
    with open(temp_csv_file, 'w') as f:
        f.write('')
    result = runner.invoke(cli, ['repair', temp_csv_file])
    assert result.exit_code == 1
    assert 'Error' in result.output

def test_cli_help_for_repair_command(runner):
    result = runner.invoke(cli, ['repair', '--help'])
    assert result.exit_code == 0
    assert '--output' in result.output
    assert '--delimiter' in result.output
    assert '--sanitize-pii' in result.output

def test_cli_help_for_analyze_command(runner):
    result = runner.invoke(cli, ['analyze', '--help'])
    assert result.exit_code == 0
    assert 'analyze' in result.output.lower()

def test_repair_with_quotes_and_pii(runner, temp_csv_file):
    data = 'id,name,email\n1,"John Doe",john@test.com\n2,"Jane",jane@example.org'
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    result = runner.invoke(cli, ['repair', temp_csv_file, '--sanitize-pii'])
    assert result.exit_code == 0
    assert 'Sanitized PII' in result.output
    assert '[REDACTED_EMAIL]' in result.output


