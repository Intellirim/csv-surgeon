import pytest
import os
import tempfile

@pytest.fixture
def temp_csv_file():
    fd, path = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)

@pytest.fixture
def broken_quotes_file():
    return os.path.join(os.path.dirname(__file__), 'fixtures', 'broken_quotes.csv')

@pytest.fixture
def wrong_encoding_file():
    return os.path.join(os.path.dirname(__file__), 'fixtures', 'wrong_encoding.csv')

@pytest.fixture
def embedded_linebreaks_file():
    return os.path.join(os.path.dirname(__file__), 'fixtures', 'embedded_linebreaks.csv')

@pytest.fixture
def mixed_delimiters_file():
    return os.path.join(os.path.dirname(__file__), 'fixtures', 'mixed_delimiters.csv')

@pytest.fixture
def simple_csv_data():
    return "id,name,email\n1,John,john@example.com\n2,Jane,jane@example.com"

@pytest.fixture
def malformed_quotes_data():
    return 'id,name,description\n1,John,"This is a test\n2,Jane,"Another test"'

@pytest.fixture
def pii_data():
    return """id,name,email,phone
1,John Doe,john@example.com,555-123-4567
2,Jane Smith,jane@test.com,555-987-6543
3,Bob Lee,bob@demo.org,555-555-5555"""
