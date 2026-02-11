import pytest
import os
from csv_surgeon.repair import RepairEngine
from csv_surgeon.detection import detect_encoding, detect_delimiter
from csv_surgeon.exceptions import UnrepairableFileError, EncodingDetectionError

def test_repair_very_large_file(tmp_path):
    file_path = tmp_path / "large.csv"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("id,name,value\n")
        for i in range(10000):
            f.write(f"{i},name_{i},{i*100}\n")
    engine = RepairEngine()
    result = engine.repair(str(file_path))
    assert result.repaired_rows == 10001
    assert result.delimiter_detected == ','

def test_repair_single_column(temp_csv_file):
    data = "id\n1\n2\n3"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    engine = RepairEngine()
    result = engine.repair(temp_csv_file)
    assert result.repaired_rows == 4
    assert len(result.output_data) > 0

def test_repair_only_header(temp_csv_file):
    data = "id,name,email"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    engine = RepairEngine()
    result = engine.repair(temp_csv_file)
    assert result.repaired_rows == 1
    assert result.has_header is False

def test_repair_many_columns(temp_csv_file):
    columns = ','.join([f'col{i}' for i in range(100)])
    values = ','.join([str(i) for i in range(100)])
    data = f"{columns}\n{values}\n{values}"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    engine = RepairEngine()
    result = engine.repair(temp_csv_file)
    assert result.repaired_rows == 3
    assert result.delimiter_detected == ','

def test_repair_quotes_everywhere(temp_csv_file):
    data = '"id","name","description"\n"1","John","Test"\n"2","Jane","Data"'
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    engine = RepairEngine()
    result = engine.repair(temp_csv_file)
    assert result.repaired_rows == 3
    assert result.malformed_quotes == 0

def test_repair_mixed_line_endings(temp_csv_file):
    with open(temp_csv_file, 'wb') as f:
        f.write(b"id,name\r\n1,John\n2,Jane\r\n3,Bob\n")
    engine = RepairEngine()
    result = engine.repair(temp_csv_file)
    assert result.repaired_rows >= 3

def test_repair_trailing_delimiters(temp_csv_file):
    data = "id,name,\n1,John,\n2,Jane,"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    engine = RepairEngine()
    result = engine.repair(temp_csv_file)
    assert result.repaired_rows == 3

def test_repair_leading_delimiters(temp_csv_file):
    data = ",id,name\n,1,John\n,2,Jane"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    engine = RepairEngine()
    result = engine.repair(temp_csv_file)
    assert result.repaired_rows == 3

def test_repair_empty_fields(temp_csv_file):
    data = "id,name,email\n1,,\n,Jane,jane@test.com\n3,,"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    engine = RepairEngine()
    result = engine.repair(temp_csv_file)
    assert result.repaired_rows == 4
    assert ',,' in result.output_data

def test_repair_whitespace_only_fields(temp_csv_file):
    data = "id,name,value\n1,  ,3\n2,Jane,  \n  ,Bob,5"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    engine = RepairEngine()
    result = engine.repair(temp_csv_file)
    assert result.repaired_rows == 4

def test_repair_special_characters(temp_csv_file):
    data = "id,name,notes\n1,Test,Line with \t tab\n2,Data,Symbols: @#$%^&*()"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    engine = RepairEngine()
    result = engine.repair(temp_csv_file)
    assert result.repaired_rows >= 2

def test_detect_delimiter_ambiguous(temp_csv_file):
    data = "a,b;c\n1,2;3\n4,5;6"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    result = detect_delimiter(temp_csv_file)
    assert result.value in [',', ';']
    assert result.confidence > 0.0

def test_repair_consecutive_quotes(temp_csv_file):
    data = 'id,name,desc\n1,John,""Empty""\n2,Jane,Normal'
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    engine = RepairEngine()
    result = engine.repair(temp_csv_file)
    assert result.repaired_rows >= 2

def test_repair_quote_in_middle(temp_csv_file):
    data = 'id,name,desc\n1,John,He said "hello" today\n2,Jane,Normal'
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    engine = RepairEngine()
    result = engine.repair(temp_csv_file)
    assert result.repaired_rows >= 2

def test_repair_numeric_strings(temp_csv_file):
    data = 'id,code,value\n1,"00123",456\n2,"00456",789'
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    engine = RepairEngine()
    result = engine.repair(temp_csv_file)
    assert result.repaired_rows == 3
    assert '00123' in result.output_data

def test_repair_all_empty_columns(temp_csv_file):
    data = ",,\n,,\n,,"
    with open(temp_csv_file, 'w', encoding='utf-8') as f:
        f.write(data)
    engine = RepairEngine()
    result = engine.repair(temp_csv_file)
    assert result.repaired_rows == 3

def test_detect_encoding_mixed_content(temp_csv_file):
    with open(temp_csv_file, 'wb') as f:
        f.write("id,name\n".encode('utf-8'))
        f.write("1,Test\n".encode('utf-8'))
    result = detect_encoding(temp_csv_file)
    assert result.value is not None
    assert result.confidence > 0.0

def test_repair_windows_line_endings(temp_csv_file):
    with open(temp_csv_file, 'wb') as f:
        f.write(b"id,name\r\n1,John\r\n2,Jane\r\n")
    engine = RepairEngine()
    result = engine.repair(temp_csv_file)
    assert result.repaired_rows == 3

def test_repair_no_final_newline(temp_csv_file):
    with open(temp_csv_file, 'w', encoding='utf-8', newline='') as f:
        f.write("id,name\n1,John\n2,Jane")
    engine = RepairEngine()
    result = engine.repair(temp_csv_file)
    assert result.repaired_rows == 3
