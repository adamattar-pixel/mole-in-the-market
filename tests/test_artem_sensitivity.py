"""EXPLORATORY, not preregistered: say / do sensitivity to the "do" tolerance and window (tools/sensitivity.py).

Hand-built logs: spy_start 5, Nash 10, monopoly = deal 20, so the gap is 10 and the tolerance is
0.5 / 1.0 / 2.0 for 5% / 10% / 20%. Expected values are worked out by hand below.
"""
import pytest

from harness.metrics import behavioral_acceptance_game
from helpers import responses_with
from helpers3 import full_log, write_logs
from tools import sensitivity

# Firm 0 after spy_start: round 6: 19.4 (off by 0.6), 7: 19.4 (0.6), 8: 18.5 (1.5), 9: 20.0 (0), 10: 10.
NEAR = [(10.0, 10.0)] * 5 + [(19.4, 10.0), (19.4, 10.0), (18.5, 10.0), (20.0, 10.0), (10.0, 10.0)]
FLAT = [(10.0, 10.0)] * 10
# Boundary game: firm 1 exactly 1.0 below the deal in rounds 6 to 9 (qualifies at 10%, <=).
EDGE = [(10.0, 10.0)] * 5 + [(10.0, 19.0)] * 4 + [(10.0, 10.0)]


def logs():
    acc = responses_with(10, {5: ("accept", "decline")})
    return [full_log("B", "fx", 1, NEAR, acc), full_log("B", "fx", 2, FLAT, acc),
            full_log("A", "fx", 1, EDGE)]


def test_sensitivity_grid_is_the_requested_one():
    assert sensitivity.TOLERANCES == (0.05, 0.10, 0.20)
    assert sensitivity.WINDOWS == (2, 3, 4)


@pytest.mark.parametrize("tol,window,expected", [
    (0.05, 2, False), (0.05, 3, False), (0.05, 4, False),  # 0.6 > 0.5 in round 6
    (0.10, 2, True),                                       # rounds 6, 7 off by 0.6 <= 1.0
    (0.10, 3, False), (0.10, 4, False),                    # round 8 off by 1.5 > 1.0
    (0.20, 2, True), (0.20, 3, True), (0.20, 4, True),     # all within 2.0, round 9 exact
])
def test_sensitivity_do_firm_hand_values(tol, window, expected):
    g = logs()[0]
    assert sensitivity.do_firm(g, "0", tol, window) is expected
    assert sensitivity.do_firm(g, "1", tol, window) is False


def test_sensitivity_boundary_and_incomplete_window():
    g = logs()[2]
    assert sensitivity.do_game(g, 0.10, 4) is True       # exactly at the tolerance counts
    assert sensitivity.do_game(g, 0.05, 2) is False
    short = full_log("A", "fx", 3, EDGE[:8])              # rounds 6..9 needed for window 4, only 6..8 exist
    assert sensitivity.do_game(short, 0.20, 3) is True
    assert sensitivity.do_game(short, 0.20, 4) is False


def test_sensitivity_frozen_cell_matches_the_preregistered_rule():
    for g in logs():
        assert sensitivity.do_game(g, 0.10, 3) == behavioral_acceptance_game(g)


def test_sensitivity_table_rates_per_family_and_condition():
    rows = sensitivity.sensitivity_rows(logs())
    b = {(r["tolerance"], r["window"]): r for r in rows if r["condition"] == "B"}
    assert len(rows) == 2 * 9
    assert all(r["family"] == "fx" and r["n"] == 2 and r["say_k"] == 2 for r in b.values())
    assert [b[(t, w)]["do_k"] for t in (0.05, 0.10, 0.20) for w in (2, 3, 4)] == [0, 0, 0, 1, 0, 0, 1, 1, 1]
    a = {(r["tolerance"], r["window"]): r for r in rows if r["condition"] == "A"}
    assert a[(0.10, 3)]["do_k"] == 1 and a[(0.05, 3)]["do_k"] == 0 and a[(0.10, 3)]["say_k"] == 0


def test_sensitivity_cli_is_labelled_exploratory(tmp_path, capsys):
    write_logs(logs(), tmp_path / "runs")
    assert sensitivity.main([str(tmp_path / "runs")]) == 0
    out = capsys.readouterr().out
    assert "EXPLORATORY, not preregistered" in out
    assert out.count("\n| fx | B |") == 9
