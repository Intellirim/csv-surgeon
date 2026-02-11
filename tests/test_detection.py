import pytest
import os
from csv_surgeon.detection import (
    detect_encoding,
    detect_delimiter,
    detect_header,
    _looks_like_number,
    _looks_like_string
)
from csv_surgeon.exceptions import EncodingDetectionError
def test_detect_encoding_utf8(temp_csv_file, simple_csv_data):
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(simple_csv_data)
    result = detect_encoding(temp_csv_file)
    assert result.value.lower() in ['utf-8', 'ascii']
    assert result.confidence > 0.5
    assert isinstance(result.method, str)
def test_detect_encoding_latin1(wrong_encoding_file):
    result = detect_encoding(wrong_encoding_file)
    assert result.value is not None
    assert result.confidence > 0.0
    assert len(result.value) > 0
def test_detect_encoding_empty_file(temp_csv_file):
    with open(temp_csv_file, 'w') as f:
        f.write('')
    with pytest.raises(EncodingDetectionError) as exc_info:
        detect_encoding(temp_csv_file)
    assert "empty" in str(exc_info.value).lower()
def test_detect_encoding_nonexistent_file():
    with pytest.raises(EncodingDetectionError) as exc_info:
        detect_encoding('/nonexistent/file.csv')
    assert "Cannot read file" in str(exc_info.value)
def test_detect_delimiter_comma(temp_csv_file, simple_csv_data):
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(simple_csv_data)
    result = detect_delimiter(temp_csv_file)
    assert result.value == ','
    assert result.confidence > 0.5
    assert result.method == 'statistical_cv'
def test_detect_delimiter_semicolon(mixed_delimiters_file):
    result = detect_delimiter(mixed_delimiters_file)
    assert result.value == ';'
    assert result.confidence > 0.5

def test_detect_delimiter_consistent_columns(temp_csv_file):
    data = "a,b,c\n1,2,3\n4,5,6\n7,8,9"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    result = detect_delimiter(temp_csv_file)
    assert result.value == ','
    assert result.confidence > 0.9
def test_detect_header_with_header(temp_csv_file):
    lines = ["name,age,city", "John,25,NYC", "Jane,30,LA"]
    result = detect_header(lines, ',')
    assert result is True
    assert isinstance(result, bool)
def test_detect_header_without_header(temp_csv_file):
    lines = ["John,25,NYC", "Jane,30,LA", "Bob,35,SF"]
    result = detect_header(lines, ',')
    assert result is False
    assert isinstance(result, bool)
def test_detect_header_insufficient_lines():
    lines = ["name,age"]
    result = detect_header(lines, ',')
    assert result is False
    assert isinstance(result, bool)
def test_detect_header_single_line():
    lines = ["name,age,city", "John,25,NYC"]
    result = detect_header(lines, ',')
    assert result is True
    assert isinstance(result, bool)
def test_looks_like_number():
    assert _looks_like_number("123") is True
    assert _looks_like_number("45.67") is True
    assert _looks_like_number("-89") is True
    assert _looks_like_number("0.001") is True
    assert _looks_like_number("hello") is False
    assert _looks_like_number("") is False
    assert _looks_like_number('"123"') is True
def test_looks_like_string():
    assert _looks_like_string("hello") is True
    assert _looks_like_string("world") is True
    assert _looks_like_string("123") is False
    assert _looks_like_string("45.67") is False
    assert _looks_like_string("") is True
    assert _looks_like_string('"text"') is True

def test_detect_delimiter_empty_file(temp_csv_file):
    with open(temp_csv_file, 'w') as f:
        f.write('')
    result = detect_delimiter(temp_csv_file)
    assert result.value == ','
    assert result.confidence == 0.5
    assert result.method == 'default'

def test_detect_encoding_binary_file(temp_csv_file):
    with open(temp_csv_file, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00')
    result = detect_encoding(temp_csv_file)
    assert result.value is not None
    assert result.confidence >= 0.0

def test_detect_encoding_very_large_sample(temp_csv_file):
    large_data = ("a,b,c\n" + "1,2,3\n" * 50000)
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(large_data)
    result = detect_encoding(temp_csv_file, sample_size=200000)
    assert result.value.lower() in ['utf-8', 'ascii']
    assert result.confidence > 0.5

def test_detect_delimiter_tab(temp_csv_file):
    data = "a\tb\tc\n1\t2\t3\n4\t5\t6"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    result = detect_delimiter(temp_csv_file)
    assert result.value == '\t'
    assert result.confidence > 0.5

def test_detect_delimiter_pipe(temp_csv_file):
    data = "a|b|c\n1|2|3\n4|5|6"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    result = detect_delimiter(temp_csv_file)
    assert result.value == '|'
    assert result.confidence > 0.5

def test_detect_delimiter_all_zero_counts(temp_csv_file):
    data = "abc\ndef\nghi"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    result = detect_delimiter(temp_csv_file)
    assert result.value == ','
    assert result.confidence >= 0.5

def test_looks_like_number_edge_cases():
    assert _looks_like_number("  123  ") is True
    assert _looks_like_number("'456'") is True
    assert _looks_like_number("-0.001") is True
    assert _looks_like_number("1e10") is True

def test_looks_like_string_with_quotes():
    assert _looks_like_string('"hello world"') is True
    assert _looks_like_string("'data'") is True
    assert _looks_like_string('"45.67"') is False
    assert _looks_like_string("  ") is True

def test_detect_header_all_numbers():
    lines = ["1,2,3", "4,5,6", "7,8,9"]
    result = detect_header(lines, ',')
    assert result is False

def test_detect_header_mixed_first_row():
    lines = ["id,25,John", "1,30,Jane", "2,35,Bob"]
    result = detect_header(lines, ',')
    assert result is False

def test_detect_encoding_fallback_utf16(temp_csv_file):
    data = "id,name\n1,Test"
    with open(temp_csv_file, 'w', encoding='utf-16') as f:
        f.write(data)
    result = detect_encoding(temp_csv_file)
    assert result.value is not None
    assert result.confidence > 0.0

def test_detect_delimiter_single_line(temp_csv_file):
    data = "a,b,c"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    result = detect_delimiter(temp_csv_file)
    assert result.value == ','
    assert result.confidence > 0.9

def test_detect_delimiter_inconsistent_counts(temp_csv_file):
    data = "a,b,c\n1,2\n3,4,5,6"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    result = detect_delimiter(temp_csv_file)
    assert result.value == ','
    assert 0.5 <= result.confidence <= 1.0
