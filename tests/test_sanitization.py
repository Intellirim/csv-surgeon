import pytest
from csv_surgeon.core import sanitize_pii

def test_sanitize_email_basic():
    text = "Contact: john@example.com for info"
    result, counts = sanitize_pii(text)
    assert '[REDACTED_EMAIL]' in result
    assert counts['emails'] == 1
    assert 'john@example.com' not in result

def test_sanitize_email_multiple():
    text = "Email john@test.com or jane@example.org"
    result, counts = sanitize_pii(text)
    assert counts['emails'] == 2
    assert result.count('[REDACTED_EMAIL]') == 2

def test_sanitize_phone_format_dashes():
    text = "Call 555-123-4567 today"
    result, counts = sanitize_pii(text)
    assert '[REDACTED_PHONE]' in result
    assert counts['phones'] == 1
    assert '555-123-4567' not in result

def test_sanitize_phone_format_dots():
    text = "Call 555.123.4567 today"
    result, counts = sanitize_pii(text)
    assert '[REDACTED_PHONE]' in result
    assert counts['phones'] == 1

def test_sanitize_phone_format_spaces():
    text = "Call 555 123 4567 today"
    result, counts = sanitize_pii(text)
    assert '[REDACTED_PHONE]' in result
    assert counts['phones'] == 1

def test_sanitize_phone_format_parens():
    text = "Call (555) 123-4567 today"
    result, counts = sanitize_pii(text)
    assert '[REDACTED_PHONE]' in result
    assert counts['phones'] == 1

def test_sanitize_phone_international():
    text = "Call +1-555-123-4567 or +44 20 1234 5678"
    result, counts = sanitize_pii(text)
    assert counts['phones'] >= 1
    assert '[REDACTED_PHONE]' in result

def test_sanitize_ssn_format():
    text = "SSN: 123-45-6789"
    result, counts = sanitize_pii(text)
    assert '[REDACTED_SSN]' in result
    assert counts['ssns'] == 1
    assert '123-45-6789' not in result

def test_sanitize_ssn_multiple():
    text = "SSN1: 123-45-6789, SSN2: 987-65-4321"
    result, counts = sanitize_pii(text)
    assert counts['ssns'] == 2
    assert result.count('[REDACTED_SSN]') == 2

def test_sanitize_mixed_pii():
    text = "Contact john@test.com at 555-123-4567, SSN: 123-45-6789"
    result, counts = sanitize_pii(text)
    assert counts['emails'] == 1
    assert counts['phones'] == 1
    assert counts['ssns'] == 1
    assert '[REDACTED_EMAIL]' in result
    assert '[REDACTED_PHONE]' in result
    assert '[REDACTED_SSN]' in result

def test_sanitize_no_pii():
    text = "This is just normal text with no sensitive data"
    result, counts = sanitize_pii(text)
    assert result == text
    assert counts['emails'] == 0
    assert counts['phones'] == 0
    assert counts['ssns'] == 0

def test_sanitize_empty_string():
    text = ""
    result, counts = sanitize_pii(text)
    assert result == ""
    assert counts['emails'] == 0
    assert counts['phones'] == 0

def test_sanitize_email_edge_cases():
    text = "test+tag@example.co.uk and user_name@sub.domain.com"
    result, counts = sanitize_pii(text)
    assert counts['emails'] == 2
    assert result.count('[REDACTED_EMAIL]') == 2

def test_sanitize_false_positive_email():
    text = "This is not@an email address"
    result, counts = sanitize_pii(text)
    assert counts['emails'] == 0
    assert result == text

def test_sanitize_false_positive_phone():
    text = "Version 1.2.3.4567 released"
    result, counts = sanitize_pii(text)
    assert counts['phones'] == 0

def test_sanitize_false_positive_ssn():
    text = "Date format: 123-45-67890 (too long)"
    result, counts = sanitize_pii(text)
    assert counts['ssns'] == 0

def test_sanitize_pii_in_csv_row():
    text = "1,John Doe,john@example.com,555-123-4567,123-45-6789"
    result, counts = sanitize_pii(text)
    assert counts['emails'] == 1
    assert counts['phones'] == 1
    assert counts['ssns'] == 1
    assert 'John Doe' in result
    assert '[REDACTED_EMAIL]' in result

def test_sanitize_preserves_structure():
    text = "id,email,phone\n1,test@example.com,555-123-4567"
    result, counts = sanitize_pii(text)
    assert '\n' in result
    assert ',' in result
    assert 'id' in result
