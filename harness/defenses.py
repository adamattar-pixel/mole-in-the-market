"""R31-R35 (EXPLORATORY, post-freeze): rule monitor, ethics condition, defense metrics, addendum guard.

Frozen texts and definitions come only from PREREGISTRATION_ADDENDUM.md (frozen at 8b7b5a1).
"""
from pathlib import Path

ADDENDUM_PATH = Path(__file__).resolve().parent.parent / "PREREGISTRATION_ADDENDUM.md"

ADDENDUM_CONDITIONS = ("B_ETH", "B_MON", "C_MON", "D_MON")
MONITORED_CONDITIONS = ("B_MON", "C_MON", "D_MON")
BASE_CONDITION = {"B_ETH": "B", "B_MON": "B", "C_MON": "C", "D_MON": "D"}


def load_addendum(path=None):
    raise NotImplementedError


def addendum_is_frozen(path=None):
    raise NotImplementedError


def pact_rule_matches(message, pattern):
    raise NotImplementedError


def apply_monitor(message, pattern):
    raise NotImplementedError


def monitor_metrics(logs, family=None):
    raise NotImplementedError


def defenses_comparison(logs, family=None):
    raise NotImplementedError
