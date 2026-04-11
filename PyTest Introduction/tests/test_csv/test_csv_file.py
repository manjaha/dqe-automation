import pytest
import re


def test_file_not_empty(csv_content):
    assert len(csv_content) > 0, (
        "CSV file is empty: it must contain at least one data row"
    )


@pytest.mark.validate_csv
@pytest.mark.xfail(
    reason="data.csv contains a known duplicate row for id=4 (Shaquille O'Neal). "
           "This test is expected to fail until the source data is cleaned.",
    strict=True,   # must actually fail; if it passes unexpectedly, report as xpass
)
def test_duplicates(csv_content):
    duplicate_rows = csv_content[csv_content.duplicated()]
    assert duplicate_rows.empty, (
        f"Found {len(duplicate_rows)} duplicate row(s) in the CSV file:\n"
        f"{duplicate_rows.to_string(index=False)}"
    )


@pytest.mark.validate_csv
def test_validate_schema(validate_schema):
    expected = ["id", "name", "age", "email", "is_active"]
    validate_schema(expected)


@pytest.mark.validate_csv
@pytest.mark.skip(reason="Age validation deferred to next sprint — skipping intentionally")
def test_age_column_valid(csv_content):
    invalid_ages = csv_content[
        (csv_content["age"] < 0) | (csv_content["age"] > 100)
    ]
    assert invalid_ages.empty, (
        f"Found {len(invalid_ages)} row(s) with an age outside the valid range [0, 100]:\n"
        f"{invalid_ages[['id', 'name', 'age']].to_string(index=False)}"
    )


@pytest.mark.validate_csv
def test_email_column_valid(csv_content):
    email_pattern = re.compile(r"^[\w.\-+]+@[\w\-]+\.[a-zA-Z]{2,}$")
    invalid_emails = csv_content[
        ~csv_content["email"].astype(str).apply(lambda e: bool(email_pattern.match(e)))
    ]
    assert invalid_emails.empty, (
        f"Found {len(invalid_emails)} row(s) with an invalid email address:\n"
        f"{invalid_emails[['id', 'name', 'email']].to_string(index=False)}"
    )


@pytest.mark.parametrize("player_id, expected_is_active", [
    (1, False),
    (2, True)
])
def test_active_players(csv_content, player_id, expected_is_active):
    row = csv_content[csv_content["id"] == player_id]
    assert not row.empty, (
        f"No row found in CSV for id={player_id}. "
        "Cannot validate is_active."
    )
    actual = bool(row.iloc[0]["is_active"])
    assert actual == expected_is_active, (
        f"is_active mismatch for id={player_id} ({row.iloc[0]['name']}):\n"
        f"  Expected : {expected_is_active}\n"
        f"  Actual   : {actual}"
    )

def test_active_player(csv_content):
    player_id = 2
    expected_is_active = True
    row = csv_content[csv_content["id"] == player_id]
    assert not row.empty, (
        f"No row found in CSV for id={player_id}. "
        "Cannot validate is_active."
    )
    actual = bool(row.iloc[0]["is_active"])
    assert actual == expected_is_active, (
        f"is_active mismatch for id={player_id} ({row.iloc[0]['name']}):\n"
        f"  Expected : {expected_is_active}\n"
        f"  Actual   : {actual}"
    )
