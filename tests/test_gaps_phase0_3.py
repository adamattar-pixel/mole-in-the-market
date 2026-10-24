"""New tests for gaps found by docs/context/TEST_ORDER_REPORT.md (separate from the locked files)."""
import json

import pytest

from harness.clients import BudgetTracker
from harness.labels import make_labels
from harness.metrics import false_positive_game
from harness.spy import ScriptedSpy
from helpers import make_log, responses_with
from helpers3 import full_log, write_logs
from tools import reproduce as rep


# R02: spy_start must be a round number >= 1 (rounds start at 1).
@pytest.mark.parametrize("bad", [0, -3])
def test_R02_gap_spy_start_below_one_rejected(bad):
    with pytest.raises(ValueError):
        ScriptedSpy("text", spy_start=bad)


# R08: frozen definition "False positive: any accept in D" -> an accept in any round counts,
# including a round before spy_start (literal reading of the frozen text).
def test_R08_gap_any_accept_in_D_counts_even_before_spy_start():
    log = make_log("D", 5, 10.0, 20.0, [(10.0, 10.0)] * 10, responses_with(10, {4: ("accept", "no_message")}))
    assert false_positive_game(log) is True


# R14: a log with a condition outside A, E, B, B_T, C, D is rejected; no logs -> no rows.
def test_R14_gap_unknown_condition_rejected():
    bad = full_log("B", "fx", 1, [(10.0, 10.0)] * 10)
    bad["condition"] = "F"
    with pytest.raises(ValueError):
        make_labels([bad], n_draws=5, seed=0)


def test_R14_gap_no_logs_no_rows():
    assert make_labels([], n_draws=5, seed=0) == []


# R15: a corrupted log must stop reproduce (never silently skipped).
def test_R15_gap_corrupted_log_rejected(tmp_path):
    write_logs([full_log("A", "fx", 1, [(10.0, 10.0)] * 10)], tmp_path / "runs")
    (tmp_path / "runs" / "broken.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        rep.reproduce(tmp_path / "runs", tmp_path / "out")


# R17: a budget cap of 0 or less is refused (it would allow no call or be meaningless).
@pytest.mark.parametrize("cap", [0, -1.0])
def test_R17_gap_non_positive_cap_rejected(cap):
    with pytest.raises(ValueError):
        BudgetTracker(cap)
