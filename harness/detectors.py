"""R28: rule-based collusion detectors D1, D2, D3 (no model call). EXPLORATORY, post-freeze.

Definitions and thresholds: PREREGISTRATION_ADDENDUM.md ("Frozen texts and thresholds", "Detector definitions").
A detector sees a finished game log and returns a flag; it never reads the condition.
"""
from pathlib import Path

ADDENDUM_PATH = Path(__file__).resolve().parent.parent / "PREREGISTRATION_ADDENDUM.md"

D1_LAST_ROUNDS = None
D1_GAP_FRACTION = None
D3_MIN_ABS_CORR = None
D3_MIN_PAIRS = None
PACT_PATTERN = None


def load_detector_params(path=None):
    raise NotImplementedError


def pearson(x, y):
    raise NotImplementedError


def price_changes(log, firm):
    raise NotImplementedError


def received_message(log):
    raise NotImplementedError


def matches_pact(text):
    raise NotImplementedError


def d1_price_level(log):
    raise NotImplementedError


def d2_message(log):
    raise NotImplementedError


def d3_score(log):
    raise NotImplementedError


def d3_action_dependence(log):
    raise NotImplementedError


DETECTORS = (("D1", d1_price_level), ("D2", d2_message), ("D3", d3_action_dependence))


def detector_flags(log):
    raise NotImplementedError
