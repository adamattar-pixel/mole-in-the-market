"""R31-R35 (EXPLORATORY, post-freeze): rule monitor, ethics condition, defense metrics, addendum guard.

Frozen texts and definitions come only from PREREGISTRATION_ADDENDUM.md (frozen at 8b7b5a1).
"""
import re
from pathlib import Path

import yaml

ADDENDUM_PATH = Path(__file__).resolve().parent.parent / "PREREGISTRATION_ADDENDUM.md"

ADDENDUM_CONDITIONS = ("B_ETH", "B_MON", "C_MON", "D_MON")
MONITORED_CONDITIONS = ("B_MON", "C_MON", "D_MON")
BASE_CONDITION = {"B_ETH": "B", "B_MON": "B", "C_MON": "C", "D_MON": "D"}


def load_addendum(path=None):
    """The ```yaml block of PREREGISTRATION_ADDENDUM.md (frozen texts and thresholds)."""
    text = Path(path or ADDENDUM_PATH).read_text(encoding="utf-8")
    m = re.search(r"```yaml\n(.*?)```", text, flags=re.DOTALL)
    if not m:
        raise ValueError("no ```yaml block in the addendum")
    data = yaml.safe_load(m.group(1))
    missing = [k for k in ("status", "ethics_instruction", "pact_pattern") if k not in data]
    if missing:
        raise ValueError(f"addendum is missing: {missing}")
    return data


def addendum_is_frozen(path=None):
    raise NotImplementedError


def pact_rule_matches(message, pattern):
    """Addendum: `pact_pattern` is matched case-insensitively (anywhere in the message)."""
    return bool(message) and re.search(pattern, message, flags=re.IGNORECASE) is not None


def apply_monitor(message, pattern):
    """R31: (delivered message, blocked). A matching spy message is blocked: the firms receive none."""
    if message is not None and pact_rule_matches(message, pattern):
        return None, True
    return message, False


def monitor_metrics(logs, family=None):
    raise NotImplementedError


def defenses_comparison(logs, family=None):
    raise NotImplementedError
