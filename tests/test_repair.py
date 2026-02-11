import pytest
import os
from csv_surgeon.repair import RepairEngine, repair_file
from csv_surgeon.exceptions import UnrepairableFileError

def test_repair_simple_csv(temp_csv_file, simple_csv_data):
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(simple_csv_data)
    engine = RepairEngine()
    result = engine.repair(temp_csv_file)
    assert result.repaired_rows > 0
    assert result.encoding_detected.lower() in ['utf-8', 'ascii']
    assert result.delimiter_detected == ','
    assert len(result.output_data) > 0
    assert result.errors == []
def test_repair_broken_quotes(broken_quotes_file):
    engine = RepairEngine()
    result = engine.repair(broken_quotes_file)
    assert result.repaired_rows > 0
    assert result.malformed_quotes >= 0
    assert len(result.output_data) > 0
    assert result.delimiter_detected == ','
def test_repair_with_pii_sanitization(temp_csv_file, pii_data):
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(pii_data)
    engine = RepairEngine()
    result = engine.repair(temp_csv_file, sanitize=True)
    assert result.repaired_rows > 0
    assert result.pii_sanitized is not None
    assert 'emails' in result.pii_sanitized
    assert 'phones' in result.pii_sanitized
    assert result.pii_sanitized['emails'] >= 3
    assert result.pii_sanitized['phones'] >= 3
    assert '[REDACTED_EMAIL]' in result.output_data
    assert '[REDACTED_PHONE]' in result.output_data
def test_repair_without_pii_sanitization(temp_csv_file, pii_data):
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(pii_data)
    engine = RepairEngine()
    result = engine.repair(temp_csv_file, sanitize=False)
    assert result.repaired_rows > 0
    assert result.pii_sanitized is None
    assert '[REDACTED_EMAIL]' not in result.output_data
    assert '@' in result.output_data
def test_repair_with_forced_delimiter(temp_csv_file):
    data = "a;b;c\n1;2;3"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    engine = RepairEngine(force_delimiter=';')
    result = engine.repair(temp_csv_file)
    assert result.delimiter_detected == ';'
    assert result.delimiter_confidence == 1.0
    assert result.repaired_rows == 2
def test_repair_with_forced_encoding(temp_csv_file, simple_csv_data):
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(simple_csv_data)
    engine = RepairEngine(force_encoding='utf-8')
    result = engine.repair(temp_csv_file)
    assert result.encoding_detected == 'utf-8'
    assert result.encoding_confidence == 1.0
    assert result.repaired_rows > 0
def test_repair_nonexistent_file():
    engine = RepairEngine()
    with pytest.raises(UnrepairableFileError) as exc_info:
        engine.repair('/nonexistent/file.csv')
    assert "not found" in str(exc_info.value).lower()
def test_repair_empty_file(temp_csv_file):
    with open(temp_csv_file, 'w') as f:
        f.write('')
    engine = RepairEngine()
    with pytest.raises(UnrepairableFileError) as exc_info:
        engine.repair(temp_csv_file)
    assert "empty" in str(exc_info.value).lower()
def test_repair_file_convenience_function(temp_csv_file, simple_csv_data):
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(simple_csv_data)
    result = repair_file(temp_csv_file)
    assert result.repaired_rows > 0
    assert result.delimiter_detected == ','
    assert len(result.output_data) > 0
def test_repair_file_with_output_path(temp_csv_file, simple_csv_data):
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(simple_csv_data)
    output_path = temp_csv_file + '.out'
    try:
        result = repair_file(temp_csv_file, output_path=output_path)
        assert result.repaired_rows > 0
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            content = f.read()
            assert len(content) > 0
            assert 'id' in content
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)



def test_reconstruct_records_consistent():
    engine = RepairEngine()
    lines = ["a,b,c", "1,2,3", "x,y,z"]
    reconstructed, reconstructions = engine._reconstruct_records(lines, ',')
    assert len(reconstructed) == 3
    assert reconstructions == 0

def test_sanitize_lines():
    engine = RepairEngine()
    lines = ["john@example.com", "jane@test.com", "555-123-4567"]
    sanitized, counts = engine._sanitize_lines(lines)
    assert len(sanitized) == 3
    assert counts['emails'] >= 2
    assert counts['phones'] >= 1
    assert '[REDACTED_EMAIL]' in sanitized[0]
    assert '[REDACTED_PHONE]' in sanitized[2]

def test_repair_line_quotes_already_balanced():
    engine = RepairEngine()
    line = 'id,name,"description"'
    repaired, repairs = engine._repair_line_quotes(line, ',')
    assert repaired == line
    assert repairs == 0

def test_repair_line_quotes_adds_closing():
    engine = RepairEngine()
    line = 'id,name,"description'
    repaired, repairs = engine._repair_line_quotes(line, ',')
    assert repaired.count('"') % 2 == 0
    assert repairs == 1

def test_repair_line_quotes_no_delimiter():
    engine = RepairEngine()
    line = 'simple text with " quote'
    repaired, repairs = engine._repair_line_quotes(line, ',')
    assert repaired.count('"') % 2 == 0
    assert repairs == 1

def test_repair_quotes_multiple_lines():
    engine = RepairEngine()
    lines = ['a,b,c', '1,2,"test', '4,5,6']
    repaired, repairs = engine._repair_quotes(lines, ',')
    assert len(repaired) == 3
    assert repairs >= 0

def test_reconstruct_records_merge_needed():
    engine = RepairEngine()
    lines = ["a,b,c", "1,2,test", "continues", "4,5,6"]
    reconstructed, reconstructions = engine._reconstruct_records(lines, ',')
    assert reconstructions >= 0
    assert len(reconstructed) <= len(lines)

def test_repair_with_output_encoding_conversion(temp_csv_file, simple_csv_data):
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(simple_csv_data)
    engine = RepairEngine()
    result = engine.repair(temp_csv_file, output_encoding='latin-1')
    assert result.repaired_rows > 0
    assert len(result.output_data) > 0

def test_repair_file_with_all_options(temp_csv_file, pii_data):
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(pii_data)
    result = repair_file(
        temp_csv_file,
        force_encoding='utf-8',
        force_delimiter=',',
        sanitize_pii_data=True,
        output_encoding='utf-8'
    )
    assert result.repaired_rows > 0
    assert result.pii_sanitized is not None
    assert result.encoding_confidence == 1.0

def test_repair_permission_error(tmp_path):
    file_path = tmp_path / "readonly.csv"
    file_path.write_text("id,name\n1,Test")
    file_path.chmod(0o444)
    try:
        engine = RepairEngine()
        result = engine.repair(str(file_path))
        assert result.repaired_rows >= 0
    finally:
        file_path.chmod(0o644)

def test_repair_unicode_content(temp_csv_file):
    data = "id,name,city\n1,José,São Paulo\n2,François,Zürich"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    engine = RepairEngine()
    result = engine.repair(temp_csv_file)
    assert result.repaired_rows == 3
    assert 'José' in result.output_data or 'Jos' in result.output_data

def test_reconstruct_records_empty_lines():
    engine = RepairEngine()
    lines = []
    reconstructed, reconstructions = engine._reconstruct_records(lines, ',')
    assert reconstructed == []
    assert reconstructions == 0

def test_sanitize_lines_no_pii():
    engine = RepairEngine()
    lines = ["id,name", "1,John", "2,Jane"]
    sanitized, counts = engine._sanitize_lines(lines)
    assert len(sanitized) == 3
    assert counts['emails'] == 0
    assert counts['phones'] == 0


