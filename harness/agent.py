"""R05: agent reply field response_to_message in {accept, decline, no_message}."""

VALID_RESPONSES = ("accept", "decline", "no_message")


def normalize_response(value):
    """Return (value, invalid). Only case and surrounding spaces are normalized; anything else
    that is not an exact valid value maps to no_message and is flagged invalid."""
    if isinstance(value, str):
        v = value.strip().lower()
        if v in VALID_RESPONSES:
            return v, False
    return "no_message", True


def count_invalid(values):
    return sum(1 for v in values if normalize_response(v)[1])
