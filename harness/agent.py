"""R05: agent reply field response_to_message in {accept, decline, no_message}."""

VALID_RESPONSES = ("accept", "decline", "no_message")


def normalize_response(value):
    raise NotImplementedError


def count_invalid(values):
    raise NotImplementedError
