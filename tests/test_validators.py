import pytest
from csv_surgeon.core import (
    calculate_column_counts,
    find_mode_columns,
    validate_column_consistency,
    detect_unclosed_quotes,
    find_structure_issues,
    infer_data_type,
    StructureIssue
)
def test_calculate_column_counts():
    lines = ["a,b,c", "1,2,3", "x,y,z"]
    counts = calculate_column_counts(lines, ',')
    assert counts == [3, 3, 3]
    assert len(counts) == 3
    assert all(c == 3 for c in counts)


def test_find_mode_columns_consistent():
    counts = [3, 3, 3, 3]
    mode = find_mode_columns(counts)
    assert mode == 3
    assert isinstance(mode, int)
def test_find_mode_columns_with_outliers():
    counts = [3, 3, 3, 2, 3, 4]
    mode = find_mode_columns(counts)
    assert mode == 3
    assert isinstance(mode, int)
def test_find_mode_columns_empty():
    counts = []
    mode = find_mode_columns(counts)
    assert mode == 0
    assert isinstance(mode, int)

def test_validate_column_consistency_all_consistent():
    lines = ["a,b,c", "1,2,3", "x,y,z"]
    expected, inconsistent = validate_column_consistency(lines, ',')
    assert expected == 3
    assert inconsistent == []
    assert len(inconsistent) == 0
def test_validate_column_consistency_with_mismatches():
    lines = ["a,b,c", "1,2", "x,y,z", "p,q"]
    expected, inconsistent = validate_column_consistency(lines, ',')
    assert expected == 3
    assert len(inconsistent) == 2
    assert 1 in inconsistent
    assert 3 in inconsistent

def test_detect_unclosed_quotes_balanced():
    line = 'id,name,"description"'
    result = detect_unclosed_quotes(line)
    assert result == 0
    assert isinstance(result, int)
def test_detect_unclosed_quotes_unbalanced():
    line = 'id,name,"description'
    result = detect_unclosed_quotes(line)
    assert result == 1
    assert isinstance(result, int)



def test_find_structure_issues_column_mismatch():
    lines = ["a,b,c", "1,2", "x,y,z"]
    issues = find_structure_issues(lines, ',')
    assert len(issues) >= 1
    mismatch_issues = [i for i in issues if i.issue_type == "column_mismatch"]
    assert len(mismatch_issues) == 1
    assert mismatch_issues[0].line_number == 2
def test_find_structure_issues_unclosed_quotes():
    lines = ['a,b,c', '1,2,"test', 'x,y,z']
    issues = find_structure_issues(lines, ',')
    quote_issues = [i for i in issues if i.issue_type == "unclosed_quote"]
    assert len(quote_issues) >= 1
    assert any(i.line_number == 2 for i in quote_issues)

def test_infer_data_type_integer():
    assert infer_data_type("123") == "int"
    assert infer_data_type("0") == "int"
    assert infer_data_type("-456") == "int"

def test_infer_data_type_string():
    assert infer_data_type("hello") == "string"
    assert infer_data_type("world123") == "string"
    assert infer_data_type("test@example.com") == "string"

def test_infer_data_type_float():
    assert infer_data_type("123.45") == "float"
    assert infer_data_type("0.001") == "float"
    assert infer_data_type("-99.99") == "float"

def test_infer_data_type_bool():
    assert infer_data_type("true") == "bool"
    assert infer_data_type("FALSE") == "bool"
    assert infer_data_type("yes") == "bool"
    assert infer_data_type("NO") == "bool"

def test_infer_data_type_empty():
    assert infer_data_type("") == "empty"
    assert infer_data_type("   ") == "empty"
    assert infer_data_type('""') == "empty"

def test_infer_data_type_quoted():
    assert infer_data_type('"hello"') == "string"
    assert infer_data_type("'123'") == "int"
    assert infer_data_type('"45.67"') == "float"

def test_calculate_column_counts_various_delimiters():
    lines = ["a;b;c", "1;2;3"]
    counts = calculate_column_counts(lines, ';')
    assert counts == [3, 3]

def test_calculate_column_counts_empty_list():
    counts = calculate_column_counts([], ',')
    assert counts == []

def test_validate_column_consistency_forced_expected():
    lines = ["a,b,c", "1,2,3"]
    expected, inconsistent = validate_column_consistency(lines, ',', expected_columns=3)
    assert expected == 3
    assert inconsistent == []

def test_validate_column_consistency_forced_mismatch():
    lines = ["a,b,c", "1,2"]
    expected, inconsistent = validate_column_consistency(lines, ',', expected_columns=3)
    assert expected == 3
    assert len(inconsistent) == 1

def test_detect_unclosed_quotes_multiple():
    line = 'id,name,"desc","other'
    result = detect_unclosed_quotes(line)
    assert result == 1

def test_find_structure_issues_no_issues():
    lines = ["a,b,c", "1,2,3", "4,5,6"]
    issues = find_structure_issues(lines, ',')
    assert len(issues) == 0

def test_find_structure_issues_both_types():
    lines = ["a,b,c", '1,2,"test', "3,4"]
    issues = find_structure_issues(lines, ',')
    assert len(issues) >= 2
    assert any(i.issue_type == "column_mismatch" for i in issues)
    assert any(i.issue_type == "unclosed_quote" for i in issues)


