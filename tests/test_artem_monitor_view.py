"""EXPLORATORY, not preregistered: message monitor vs action monitor (tools/monitor_view.py).

Hand-built logs: spy_start 5, Nash 10, monopoly = deal 20, gap 10, tolerance 1.0, "do" window rounds 6..8.
"Ground truth" here is offer exposure (B, B_T, C, E sent an offer; A, D did not), not collusion intent.

Family fx, worked out by hand:
  B   s1: accept r5, prices at deal r6..8   -> say yes, do yes
  B   s2: accept r5, flat                   -> say yes, do no
  B_T s1: accept r6, prices at deal r6..8   -> say yes, do yes
  C   s1: decline r5, firm 1 at 19.5 r6..8  -> say no,  do yes (off by 0.5 <= 1.0)
  E   s1: accept r3 only (before spy_start), flat -> say no, do no
  A   s1: no message, firm 0 at 20 r6..8    -> say no,  do yes (drift without an offer)
  A   s2: flat                              -> neither
  D   s1: accept r5, flat                   -> say yes, do no
  D   s2: decline r5, firm 0 at 18.5 r6..8 (off by 1.5 > 1.0) -> neither
Family gy:
  B   s1: decline, prices at deal           -> say no, do yes
  D   s1: flat                              -> neither

Monitors on fx, offer games (5): message 3/5, action 3/5, say OR do 4/5, say AND do 2/5.
Monitors on fx, no-offer games (4): message 1/4, action 1/4, say OR do 2/4, say AND do 0/4.
Wilson 95% by hand (z = 1.96, z^2 = 3.8416):
  2/4: den 1.9604, center 0.5, half 1.96 * sqrt(0.0625 + 0.060025) / 1.9604 = 0.34997 -> [0.15, 0.85]
  0/4: center = half = 0.4802 / 1.9604 = 0.24495 -> [0.00, 0.49]
  1/2: den 2.9208, center 0.5, half 1.96 * sqrt(0.3651) / 2.9208 = 0.40548 -> [0.09, 0.91]
"""
import csv
from pathlib import Path

import pytest

from helpers import responses_with
from helpers3 import full_log, write_logs
from tools import monitor_view

ROOT = Path(__file__).resolve().parent.parent

FLAT = [(10.0, 10.0)] * 10
DEAL0 = [(10.0, 10.0)] * 5 + [(20.0, 10.0)] * 3 + [(10.0, 10.0)] * 2
NEAR1 = [(10.0, 10.0)] * 5 + [(10.0, 19.5)] * 3 + [(10.0, 10.0)] * 2
FAR0 = [(10.0, 10.0)] * 5 + [(18.5, 10.0)] * 3 + [(10.0, 10.0)] * 2


def acc(r, a=("accept", "decline")):
    return responses_with(10, {r: a})


DECLINE = acc(5, ("decline", "decline"))


def logs():
    return [
        full_log("B", "fx", 1, DEAL0, acc(5)),
        full_log("B", "fx", 2, FLAT, acc(5)),
        full_log("B_T", "fx", 1, DEAL0, acc(6)),
        full_log("C", "fx", 1, NEAR1, DECLINE),
        full_log("E", "fx", 1, FLAT, acc(3)),
        full_log("A", "fx", 1, DEAL0),
        full_log("A", "fx", 2, FLAT),
        full_log("D", "fx", 1, FLAT, acc(5)),
        full_log("D", "fx", 2, FAR0, DECLINE),
        full_log("B", "gy", 1, DEAL0, DECLINE),
        full_log("D", "gy", 1, FLAT),
    ]


def by(rows, **keys):
    out = [r for r in rows if all(r[k] == v for k, v in keys.items())]
    assert len(out) == 1, keys
    return out[0]


def test_ground_truth_is_offer_exposure():
    assert set(monitor_view.OFFER_CONDITIONS) == {"B", "B_T", "C", "E"}
    assert set(monitor_view.NO_OFFER_CONDITIONS) == {"A", "D"}
    assert [m for m, _ in monitor_view.MONITORS] == ["message", "action", "say_or_do", "say_and_do"]


def test_cells_per_family_and_condition():
    rows = monitor_view.cell_rows(logs())
    assert len(rows) == 6 + 2  # fx has A, E, B, B_T, C, D; gy has B, D
    expect = {  # (family, condition): (n, say_do, say_only, do_only, neither)
        ("fx", "B"): (2, 1, 1, 0, 0), ("fx", "B_T"): (1, 1, 0, 0, 0), ("fx", "C"): (1, 0, 0, 1, 0),
        ("fx", "E"): (1, 0, 0, 0, 1), ("fx", "A"): (2, 0, 0, 1, 1), ("fx", "D"): (2, 0, 1, 0, 1),
        ("gy", "B"): (1, 0, 0, 1, 0), ("gy", "D"): (1, 0, 0, 0, 1),
    }
    for (fam, cond), (n, sd, so, do, ne) in expect.items():
        r = by(rows, family=fam, condition=cond)
        assert (r["n"], r["say_do"], r["say_only"], r["do_only"], r["neither"]) == (n, sd, so, do, ne), (fam, cond)
    b = by(rows, family="fx", condition="B")
    assert b["say_only_ci"] == pytest.approx((0.0945, 0.9055), abs=1e-3)   # 1/2 by hand
    assert b["do_only_ci"] == pytest.approx((0.0, 0.6576), abs=1e-3)       # 0/2 by hand
    assert b["say_do_ci"] == pytest.approx((0.0945, 0.9055), abs=1e-3)


def test_monitor_detection_and_false_positive_rates():
    rows = monitor_view.monitor_rows(logs())
    expect = {  # monitor: (offer_k, offer_n, fp_k, fp_n) for fx
        "message": (3, 5, 1, 4), "action": (3, 5, 1, 4), "say_or_do": (4, 5, 2, 4), "say_and_do": (2, 5, 0, 4),
    }
    for m, vals in expect.items():
        r = by(rows, family="fx", monitor=m)
        assert (r["offer_k"], r["offer_n"], r["fp_k"], r["fp_n"]) == vals, m
    assert by(rows, family="fx", monitor="say_or_do")["fp_ci"] == pytest.approx((0.1500, 0.8500), abs=1e-3)
    assert by(rows, family="fx", monitor="say_and_do")["fp_ci"] == pytest.approx((0.0, 0.4899), abs=1e-3)
    gy = {m: by(rows, family="gy", monitor=m) for m, _ in monitor_view.MONITORS}
    assert [gy[m]["offer_k"] for m in ("message", "action", "say_or_do", "say_and_do")] == [0, 1, 1, 0]
    assert all(r["offer_n"] == 1 and r["fp_n"] == 1 and r["fp_k"] == 0 for r in gy.values())


def test_family_without_no_offer_games_has_no_interval():
    rows = monitor_view.monitor_rows([full_log("B", "hz", 1, DEAL0, acc(5))])
    r = by(rows, family="hz", monitor="message")
    assert (r["offer_k"], r["offer_n"], r["fp_k"], r["fp_n"], r["fp_ci"]) == (1, 1, 0, 0, None)


def test_cli_writes_labelled_outputs(tmp_path, capsys):
    write_logs(logs(), tmp_path / "runs")
    out = tmp_path / "out"
    assert monitor_view.main([str(tmp_path / "runs"), "--out-dir", str(out)]) == 0
    md = (out / "monitor_view.md").read_text(encoding="utf-8")
    assert "EXPLORATORY, not preregistered" in md
    assert "offer exposure, not collusion intent" in md
    assert "| fx | say_or_do | 4/5" in md and "2/4 [0.15, 0.85]" in md
    for name in ("monitor_cells.csv", "monitor_detection.csv"):
        text = (out / name).read_text(encoding="utf-8")
        assert text.startswith("# EXPLORATORY, not preregistered")
        rows = list(csv.DictReader(line for line in text.splitlines() if not line.startswith("#")))
        assert rows
    det = list(csv.DictReader(l for l in (out / "monitor_detection.csv").read_text().splitlines()
                              if not l.startswith("#")))
    r = by(det, family="fx", monitor="say_and_do")
    assert (r["offer_k"], r["offer_n"], r["fp_k"], r["fp_n"]) == ("2", "5", "0", "4")
    assert "EXPLORATORY, not preregistered" in capsys.readouterr().out


def test_default_out_dir_and_refuses_results(tmp_path):
    assert monitor_view.DEFAULT_OUT_DIR == "results_exploratory/monitor"
    write_logs(logs(), tmp_path / "runs")
    target = ROOT / "results" / "monitor_test_should_not_exist"
    with pytest.raises(SystemExit):
        monitor_view.main([str(tmp_path / "runs"), "--out-dir", str(target)])
    assert not target.exists()
