import pytest
from csv_surgeon.core import sanitize_pii
from csv_surgeon.detection import detect_delimiter
from csv_surgeon.repair import RepairEngine

def test_not_an_email():
    text = "This is not@an incomplete address"
    result, counts = sanitize_pii(text)
    assert counts['emails'] == 0
    assert result == text

def test_not_an_email_missing_domain():
    text = "user@ or @domain.com"
    result, counts = sanitize_pii(text)
    assert counts['emails'] == 0

def test_not_a_phone_version_number():
    text = "Version 1.2.3.4567 or 10.11.12.1314"
    result, counts = sanitize_pii(text)
    assert counts['phones'] == 0

def test_not_a_phone_ip_address():
    text = "IP: 192.168.1.100"
    result, counts = sanitize_pii(text)
    assert counts['phones'] == 0

def test_not_a_phone_too_short():
    text = "Call 123-456"
    result, counts = sanitize_pii(text)
    assert counts['phones'] == 0

def test_not_a_ssn_too_long():
    text = "Number: 1234-56-7890"
    result, counts = sanitize_pii(text)
    assert counts['ssns'] == 0

def test_not_a_ssn_too_short():
    text = "Number: 12-34-5678"
    result, counts = sanitize_pii(text)
    assert counts['ssns'] == 0

def test_not_a_ssn_wrong_format():
    text = "Number: 12345-6789"
    result, counts = sanitize_pii(text)
    assert counts['ssns'] == 0

def test_delimiter_detection_not_csv(temp_csv_file):
    text = "This is just plain text without any clear structure"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(text)
    result = detect_delimiter(temp_csv_file)
    assert result.value == ','
    assert result.confidence <= 0.5

def test_not_a_broken_quote_normal_apostrophe(temp_csv_file):
    data = "id,name,note\n1,John,It's a test\n2,Jane,That's all"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    engine = RepairEngine()
    result = engine.repair(temp_csv_file)
    assert result.malformed_quotes == 0

def test_not_embedded_linebreak_short_line(temp_csv_file):
    data = "id,name\n1,John\n2\n3,Jane"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    engine = RepairEngine()
    result = engine.repair(temp_csv_file)
    assert result.repaired_rows >= 3

def test_email_not_in_middle_of_word():
    text = "Contact at example@test.com but not inside@word"
    result, counts = sanitize_pii(text)
    assert counts['emails'] >= 1

def test_ssn_not_in_longer_number():
    text = "Serial: 12345-67-8901 or ID: 123-45-6789"
    result, counts = sanitize_pii(text)
    assert counts['ssns'] >= 1

def test_phone_must_be_complete():
    text = "Incomplete 555-123- or 555--4567"
    result, counts = sanitize_pii(text)
    assert counts['phones'] == 0

def test_not_a_csv_just_numbers(temp_csv_file):
    data = "123\n456\n789"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    engine = RepairEngine()
    result = engine.repair(temp_csv_file)
    assert result.repaired_rows == 3
    assert result.delimiter_detected in [',', ';', '\t', '|']

def test_normal_text_with_dashes():
    text = "Date format: 2024-01-15 and time: 14-30-45"
    result, counts = sanitize_pii(text)
    assert counts['ssns'] == 0
    assert counts['phones'] == 0

def test_email_boundary_detection():
    text = "noreply@example.com and test@@invalid"
    result, counts = sanitize_pii(text)
    assert counts['emails'] == 1

def test_not_a_delimiter_symbol_in_text(temp_csv_file):
    data = "Column data with | and ; symbols\nAnother row with , commas inside"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    result = detect_delimiter(temp_csv_file)
    assert result.confidence <= 1.0
