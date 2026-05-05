import pytest
import pandas as pd
from pathlib import Path

# Fixture to read the CSV file
@pytest.fixture(scope="session")
def csv_content():
    """
    Reads the CSV file and returns a pandas DataFrame.
    The fixture is session-scoped so the file is read only once.
    """
    # Get the path relative to the conftest.py location
    tests_dir = Path(__file__).parent  # tests/
    csv_path = tests_dir.parent / "src" / "data" / "data.csv"  # PyTest Introduction/src/data/data.csv
    
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")
    
    df = pd.read_csv(csv_path)
    return df

# Fixture to validate the schema of the file
@pytest.fixture(scope="session")
def validate_schema(csv_content):
    """
    Returns a helper function that compares the actual column names of the
    DataFrame against an expected schema list.
    Usage inside a test:
        def test_something(validate_schema):
            validate_schema(["id", "name", "age", "email", "is_active"])
    """
    def _validate(expected_schema: list):
        actual_schema = list(csv_content.columns)
        assert actual_schema == expected_schema, (
            f"Schema mismatch!\n"
            f"  Expected columns : {expected_schema}\n"
            f"  Actual columns   : {actual_schema}"
        )
    return _validate

# Pytest hook to mark unmarked tests with a custom mark
def pytest_collection_modifyitems(items):
    """
    After test collection, inspect every test item.
    If a test has no marks at all, assign the custom 'unmarked' mark so it
    can be targeted with `-m unmarked`.
    """
    for item in items:
        # item.own_markers contains only the markers applied directly to the test
        if not item.own_markers:
            item.add_marker(pytest.mark.unmarked)