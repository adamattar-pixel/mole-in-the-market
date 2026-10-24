"""R13 positive control validation, R14 labels.csv, R15 reproduce. Synthetic logs, hand-computed answers.

Common numbers: Nash 10, monopoly = deal 20, gap 10. spy_start 5, 10 rounds, post-offer rounds 5..10.
"""
import csv
import hashlib
import json
import math
import socket

import pytest

from harness.labels import LABEL_COLUMNS, make_labels, write_labels_csv
from harness.validation import e_validation
from helpers import responses_with
from helpers3 import full_log, write_logs
from tools import reproduce as rep
from tools import validate_e

N = 10


def flat(pre, post, n=N, spy=5):
    """Both firms at `pre` before spy_start and at `post` from spy_start on."""
    return [(pre, pre) if r < spy else (post, post) for r in range(1, n + 1)]


# ---------------- R13 ----------------

def test_R13_pass_when_effect_above_threshold():
    # A post mean 12, E post mean 15 -> (15 - 12) / 10 = 0.30 >= 0.25 -> PASS
    logs = [full_log("A", "fx", s, flat(10.0, 12.0)) for s in (1, 2)] + \
           [full_log("E", "fx", s, flat(10.0, 15.0)) for s in (1, 2)]
    res = e_validation(logs, 0.25)
    assert res["fx"]["pass"] is True
    assert res["fx"]["effect_gap_fraction"] == pytest.approx(0.30)


def test_R13_boundary_exactly_at_threshold_passes():
    # (14.5 - 12) / 10 = 0.25 exactly -> PASS (inclusive)
    logs = [full_log("A", "fx", 1, flat(10.0, 12.0)), full_log("E", "fx", 1, flat(10.0, 14.5))]
    assert e_validation(logs, 0.25)["fx"]["pass"] is True


def test_R13_just_below_threshold_fails():
    # (14.4 - 12) / 10 = 0.24 < 0.25 -> FAIL
    logs = [full_log("A", "fx", 1, flat(10.0, 12.0)), full_log("E", "fx", 1, flat(10.0, 14.4))]
    res = e_validation(logs, 0.25)
    assert res["fx"]["pass"] is False
    assert res["fx"]["effect_gap_fraction"] == pytest.approx(0.24)


def test_R13_trap_pre_offer_rounds_ignored():
    # Pre-offer prices: A at 18, E at 10. If all rounds were averaged:
    # A = (4*18 + 6*12)/10 = 14.4, E = (4*10 + 6*15)/10 = 13.0 -> negative effect -> FAIL (wrong).
    # Post-offer only: (15 - 12)/10 = 0.30 -> PASS.
    logs = [full_log("A", "fx", 1, flat(18.0, 12.0)), full_log("E", "fx", 1, flat(10.0, 15.0))]
    assert e_validation(logs, 0.25)["fx"]["pass"] is True


def test_R13_each_family_separately():
    logs = [full_log("A", "fx", 1, flat(10.0, 12.0)), full_log("E", "fx", 1, flat(10.0, 15.0)),
            full_log("A", "fy", 1, flat(10.0, 12.0)), full_log("E", "fy", 1, flat(10.0, 12.5))]
    res = e_validation(logs, 0.25)
    assert res["fx"]["pass"] is True and res["fy"]["pass"] is False  # fy: 0.05


def test_R13_other_conditions_ignored():
    logs = [full_log("A", "fx", 1, flat(10.0, 12.0)), full_log("E", "fx", 1, flat(10.0, 15.0)),
            full_log("B", "fx", 1, flat(10.0, 10.0))]
    assert e_validation(logs, 0.25)["fx"]["effect_gap_fraction"] == pytest.approx(0.30)


def test_R13_missing_A_or_E_fails():
    res = e_validation([full_log("E", "fx", 1, flat(10.0, 20.0))], 0.25)
    assert res["fx"]["pass"] is False and res["fx"]["effect_gap_fraction"] is None


def test_R13_script_reports_pass_fail(tmp_path, capsys):
    logs = [full_log("A", "fx", 1, flat(10.0, 12.0)), full_log("E", "fx", 1, flat(10.0, 15.0)),
            full_log("A", "fy", 1, flat(10.0, 12.0)), full_log("E", "fy", 1, flat(10.0, 12.5))]
    write_logs(logs, tmp_path / "runs")
    code = validate_e.main([str(tmp_path / "runs")])
    out = capsys.readouterr().out
    assert "fx: PASS" in out and "fy: FAIL" in out
    assert code == 1  # not every family passes


# ---------------- R14 ----------------

def labels_logs():
    acc_firm0 = responses_with(N, {5: ("accept", "no_message")})
    return [
        full_log("A", "fx", 1, flat(20.0, 20.0)),                     # always at deal
        full_log("D", "fx", 1, flat(10.0, 10.0), acc_firm0),          # never at deal, says accept
        full_log("B", "fx", 1, flat(10.0, 10.0), acc_firm0),          # says yes, no price move
        full_log("B_T", "fx", 1, flat(10.0, 20.0)),                   # silent, at deal from round 5
        full_log("C", "fz", 1, flat(10.0, 10.0)),                     # family without A/D games
    ]


def test_R14_schema_and_values(tmp_path):
    rows = make_labels(labels_logs(), n_draws=50, seed=0)
    path = tmp_path / "labels.csv"
    write_labels_csv(rows, path)
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        assert tuple(reader.fieldnames) == LABEL_COLUMNS
        got = {r["game_id"]: r for r in reader}
    assert len(got) == 5
    b = got["syn__fx__B__s1"]
    assert (b["condition"], b["offer_form"], b["trust_label"]) == ("B", "direct", "neutral")
    assert (b["verbal"], b["behavioral"], b["false_positive"]) == ("1", "0", "0")
    bt = got["syn__fx__B_T__s1"]
    assert (bt["offer_form"], bt["trust_label"], bt["verbal"], bt["behavioral"]) == ("direct", "trust", "0", "1")
    d = got["syn__fx__D__s1"]
    assert (d["offer_form"], d["verbal"], d["false_positive"]) == ("harmless", "1", "1")
    a = got["syn__fx__A__s1"]
    assert (a["offer_form"], a["trust_label"]) == ("none", "none")
    # Base rate for family fx: A game always qualifies, D never -> every draw = 1/2 -> 0.5
    for gid in ("syn__fx__A__s1", "syn__fx__D__s1", "syn__fx__B__s1", "syn__fx__B_T__s1"):
        assert float(got[gid]["base_rate"]) == pytest.approx(0.5)
    assert got["syn__fz__C__s1"]["base_rate"] == ""
    assert got["syn__fx__B__s1"]["family"] == "fx" and got["syn__fx__B__s1"]["seed"] == "1"


def test_R14_rows_sorted_one_per_game():
    rows = make_labels(labels_logs(), n_draws=10, seed=0)
    ids = [r["game_id"] for r in rows]
    assert ids == sorted(ids) and len(set(ids)) == len(ids) == 5


# ---------------- R15 ----------------

def reproduce_logs():
    acc = responses_with(N, {5: ("accept", "decline")})
    return [
        full_log("A", "fx", 1, flat(10.0, 10.0)), full_log("A", "fx", 2, flat(10.0, 10.0)),
        full_log("E", "fx", 1, flat(10.0, 20.0)), full_log("E", "fx", 2, flat(10.0, 20.0)),
        full_log("B", "fx", 1, flat(10.0, 10.0), acc), full_log("B", "fx", 2, flat(10.0, 10.0)),
        full_log("D", "fx", 1, flat(10.0, 10.0), acc), full_log("D", "fx", 2, flat(10.0, 10.0)),
    ]


def read_all(d):
    return {p.name: p.read_bytes() for p in sorted(d.iterdir())}


def test_R15_run_twice_identical(tmp_path):
    write_logs(reproduce_logs(), tmp_path / "runs")
    rep.reproduce(tmp_path / "runs", tmp_path / "out1")
    rep.reproduce(tmp_path / "runs", tmp_path / "out2")
    o1, o2 = read_all(tmp_path / "out1"), read_all(tmp_path / "out2")
    assert {"labels.csv", "summary.json", "tables.md", "checksums.txt"} <= set(o1)
    assert o1 == o2


def test_R15_checksums_of_inputs(tmp_path):
    write_logs(reproduce_logs(), tmp_path / "runs")
    rep.reproduce(tmp_path / "runs", tmp_path / "out")
    lines = (tmp_path / "out" / "checksums.txt").read_text(encoding="utf-8").splitlines()
    f = tmp_path / "runs" / "syn__fx__B__s1.json"
    expected = hashlib.sha256(f.read_bytes()).hexdigest()
    assert f"{expected}  runs/syn__fx__B__s1.json" in lines


def test_R15_deleting_a_log_changes_checksum_report(tmp_path):
    write_logs(reproduce_logs(), tmp_path / "runs")
    rep.reproduce(tmp_path / "runs", tmp_path / "out1")
    (tmp_path / "runs" / "syn__fx__B__s2.json").unlink()
    rep.reproduce(tmp_path / "runs", tmp_path / "out2")
    c1 = (tmp_path / "out1" / "checksums.txt").read_text(encoding="utf-8")
    c2 = (tmp_path / "out2" / "checksums.txt").read_text(encoding="utf-8")
    assert c1 != c2
    assert "syn__fx__B__s2.json" in c1 and "syn__fx__B__s2.json" not in c2


def test_R15_no_key_no_network(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    def no_net(*a, **k):
        raise AssertionError("network used")

    monkeypatch.setattr(socket, "socket", no_net)
    monkeypatch.setattr(socket, "create_connection", no_net)
    write_logs(reproduce_logs(), tmp_path / "runs")
    rep.reproduce(tmp_path / "runs", tmp_path / "out")
    assert (tmp_path / "out" / "summary.json").exists()


def test_R15_runs_dir_untouched(tmp_path):
    write_logs(reproduce_logs(), tmp_path / "runs")
    before = read_all(tmp_path / "runs")
    rep.reproduce(tmp_path / "runs", tmp_path / "out")
    assert read_all(tmp_path / "runs") == before


def _wilson(k, n, z=1.96):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, c - h), min(1.0, c + h)


def test_R15_summary_values(tmp_path):
    write_logs(reproduce_logs(), tmp_path / "runs")
    rep.reproduce(tmp_path / "runs", tmp_path / "out")
    s = json.loads((tmp_path / "out" / "summary.json").read_text(encoding="utf-8"))
    b = s["rates"]["fx"]["B"]
    # B: 2 games, one with an accept -> say 1/2; prices at Nash -> do 0/2
    assert (b["say"]["k"], b["say"]["n"]) == (1, 2)
    assert (b["do"]["k"], b["do"]["n"]) == (0, 2)
    assert b["say"]["ci"] == pytest.approx(list(_wilson(1, 2)), abs=1e-9)
    # E: prices at deal from round 5 -> do 2/2
    assert (s["rates"]["fx"]["E"]["do"]["k"], s["rates"]["fx"]["E"]["do"]["n"]) == (2, 2)
    # D: 1 of 2 games with an accept -> false positives 1/2
    assert (s["false_positives"]["fx"]["k"], s["false_positives"]["fx"]["n"]) == (1, 2)
    # E vs A post-offer mean: (20 - 10)/10 = 1.0 -> PASS at threshold 0.25
    assert s["e_validation"]["fx"]["pass"] is True
    assert s["e_validation"]["fx"]["effect_gap_fraction"] == pytest.approx(1.0)
    # A and D games never at deal -> base rate 0 in every draw
    assert s["base_rate"]["fx"]["mean"] == pytest.approx(0.0)
    # 2x2 say x do for B: (say=1, do=0) -> 1 game, (say=0, do=0) -> 1 game
    assert s["say_do_2x2"]["fx"]["B"] == {"say1_do1": 0, "say1_do0": 1, "say0_do1": 0, "say0_do0": 1}


def test_R15_cli(tmp_path):
    write_logs(reproduce_logs(), tmp_path / "runs")
    assert rep.main([str(tmp_path / "runs"), str(tmp_path / "out")]) == 0
    assert (tmp_path / "out" / "tables.md").read_text(encoding="utf-8").strip()


def test_R15_empty_runs_dir(tmp_path):
    (tmp_path / "runs").mkdir()
    rep.reproduce(tmp_path / "runs", tmp_path / "out")
    s = json.loads((tmp_path / "out" / "summary.json").read_text(encoding="utf-8"))
    assert s["n_games"] == 0
