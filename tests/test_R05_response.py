"""R05: response_to_message in {accept, decline, no_message}; invalid values mapped to no_message and counted."""
import pytest

from harness.agent import VALID_RESPONSES, count_invalid, normalize_response


def test_R05_valid_set():
    assert set(VALID_RESPONSES) == {"accept", "decline", "no_message"}
    assert {normalize_response(v)[0] for v in VALID_RESPONSES} == set(VALID_RESPONSES)


@pytest.mark.parametrize("v", ["accept", "decline", "no_message"])
def test_R05_valid_values_kept(v):
    assert normalize_response(v) == (v, False)


@pytest.mark.parametrize("v", [" Accept ", "DECLINE"])
def test_R05_case_and_spaces_normalized(v):
    value, invalid = normalize_response(v)
    assert value == v.strip().lower() and invalid is False


@pytest.mark.parametrize("v", ["yes", "accepted", "I accept", "", None, 5, True, ["accept"]])
def test_R05_invalid_mapped_to_no_message(v):
    # Trap: "accepted" or "I accept" must NOT become accept (no fuzzy matching).
    assert normalize_response(v) == ("no_message", True)


def test_R05_invalid_values_counted():
    vals = ["accept", "yes", None, "decline", "no_message", "ok", "Accept"]
    # invalid: "yes", None, "ok" -> 3
    assert count_invalid(vals) == 3
    assert count_invalid([]) == 0
