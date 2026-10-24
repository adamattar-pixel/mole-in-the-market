"""Key figure tool (tools/before_after.py): one point per game, mean price before the offer vs in the do window.

Descriptive, from the logs only (no API key, no network). Hand-built mini games below; every expected mean
is worked out by hand in the comments.
Windows (spy_start s): before = rounds s-3 .. s-1, do = rounds s+1 .. s+3 (PREREGISTRATION.md window).
"""
import csv

import pytest

from helpers import responses_with
from helpers3 import full_log, write_logs
from tools import before_after as ba

# Family fx: spy_start 5, Nash 10, monopoly = deal 20, 8 rounds. Before = rounds 2-4, do = rounds 6-8.
# G1 per-round means: r2 (12+14)/2 = 13, r3 13, r4 (14+16)/2 = 15 -> x = 41/3
#                     r6 20, r7 (19+21)/2 = 20, r8 18           -> y = 58/3
G1 = [(10.0, 10.0), (12.0, 14.0), (13.0, 13.0), (14.0, 16.0), (17.0, 17.0), (20.0, 20.0), (19.0, 21.0),
      (18.0, 18.0)]
# G2: before r2-r4 all 11 -> x = 11; do r6-r8 = 11, 12, 13 -> y = 12
G2 = [(11.0, 11.0)] * 5 + [(11.0, 11.0), (12.0, 12.0), (13.0, 13.0)]
FLAT12 = [(12.0, 12.0)] * 8


def g(cond, seed, prices, accepts=None, family="fx"):
    resp = responses_with(len(prices), accepts or {})
    return full_log(cond, family, seed, prices, resp, spy_start=5)


def test_windows_follow_the_spy_round():
    assert ba.before_window(5) == (2, 4)
    assert ba.before_window(8) == (5, 7)
    assert ba.do_window(8) == (9, 11)


def test_firm_say_accept_decline_none():
    # accept before the spy round does not count; a decline then an accept is an accept
    log = g("B", 1, FLAT12, {3: ("accept", "accept"), 5: ("decline", "no_message"), 6: ("accept", "no_message")})
    assert ba.firm_say(log, "0") == "accept"
    assert ba.firm_say(log, "1") == "none"
    log = g("B", 1, FLAT12, {5: ("decline", "decline")})
    assert ba.firm_say(log, "0") == "decline"


def test_game_say_levels():
    assert ba.game_say(g("B", 1, FLAT12, {5: ("accept", "accept")})) == "accept"
    assert ba.game_say(g("B", 1, FLAT12, {5: ("decline", "decline")})) == "decline"
    assert ba.game_say(g("A", 1, FLAT12)) == "none"
    assert ba.game_say(g("B", 1, FLAT12, {5: ("accept", "decline")})) == "mixed"
    # firm 1 declines in the spy round, accepts one round later; firm 0 declines -> mixed
    assert ba.game_say(g("B", 1, FLAT12, {5: ("decline", "decline"), 6: ("no_message", "accept")})) == "mixed"
    # an accept before the offer is ignored -> none
    assert ba.game_say(g("B", 1, FLAT12, {2: ("accept", "accept")})) == "none"


def test_game_points_means_by_hand():
    logs = [g("B", 1, G1, {5: ("accept", "accept")}), g("A", 1, G2)]
    pts, skipped = ba.game_points(logs)
    assert skipped == []
    by_id = {p["game_id"]: p for p in pts}
    p1 = by_id["syn__fx__B__s1"]
    assert p1["x"] == pytest.approx(41 / 3) and p1["y"] == pytest.approx(58 / 3)
    assert p1["say"] == "accept" and p1["condition"] == "B" and p1["condition_name"] == "Direct offer"
    assert p1["nash"] == 10.0 and p1["deal"] == 20.0 and p1["exploratory"] is False
    p2 = by_id["syn__fx__A__s1"]
    assert p2["x"] == pytest.approx(11.0) and p2["y"] == pytest.approx(12.0) and p2["say"] == "none"


def test_incomplete_game_is_skipped_and_reported():
    short = g("B", 2, G1[:7])  # no round 8: the do window is incomplete
    pts, skipped = ba.game_points([short, g("A", 1, G2)])
    assert [p["game_id"] for p in pts] == ["syn__fx__A__s1"]
    assert skipped == ["syn__fx__B__s2"]


def test_exploratory_flag_is_kept():
    pts, _ = ba.game_points([g("B", 1, G1)], exploratory=True)
    assert pts[0]["exploratory"] is True


def test_jitter_is_small_seeded_and_order_free():
    logs = [g("B", s, FLAT12) for s in (1, 2, 3)]
    pts, _ = ba.game_points(logs)
    a = ba.jitter(pts, seed=0)
    b = ba.jitter(list(reversed(pts)), seed=0)
    c = ba.jitter(pts, seed=1)
    ja = {p["game_id"]: (p["xj"], p["yj"]) for p in a}
    jb = {p["game_id"]: (p["xj"], p["yj"]) for p in b}
    jc = {p["game_id"]: (p["xj"], p["yj"]) for p in c}
    assert ja == jb
    assert ja != jc
    for p in a:
        assert abs(p["xj"] - p["x"]) <= ba.JITTER and abs(p["yj"] - p["y"]) <= ba.JITTER
        assert (p["xj"], p["yj"]) != (p["x"], p["y"])
    assert len(set(ja.values())) == 3  # three identical games no longer overlap
    assert 0 < ba.JITTER <= 0.02  # legibility only: well under the do tolerance of real games (0.045)


def _fig(tmp_path, pts, **kw):
    return ba.make_figure(ba.jitter(pts), tmp_path / "f.pdf", tmp_path / "f.png", **kw)


def test_legend_full_names_refs_and_exploratory_note(tmp_path):
    main, _ = ba.game_points([g("B", 1, G1, {5: ("accept", "accept")}), g("A", 1, G2),
                              g("D", 1, FLAT12, {5: ("decline", "decline")})])
    expl, _ = ba.game_points([g("C", 1, FLAT12, {5: ("accept", "decline")})], exploratory=True)
    meta = _fig(tmp_path, main + expl)
    labels = meta["labels"]
    for name in ("No spy", "Direct offer", "Harmless request", "Hint"):
        assert any(name in lab for lab in labels), name
    for bare in ("A", "B", "C", "D", "E", "B_T"):
        assert bare not in labels
    for say in ("accept", "decline", "none", "mixed"):
        assert any(lab.lower().startswith(f"say: {say}") for lab in labels), say
    assert "Nash price (10.00)" in labels
    assert any(lab.startswith("Deal price") and "(20.00)" in lab for lab in labels)
    assert any(lab.startswith("y = x") for lab in labels)
    assert any("exploratory" in lab.lower() and "hollow" in lab.lower() for lab in labels)
    assert meta["panels"] == ["fx"]
    assert meta["mock_stamp"] is False


def test_no_exploratory_note_without_exploratory_points(tmp_path):
    pts, _ = ba.game_points([g("B", 1, G1)])
    meta = _fig(tmp_path, pts)
    assert not any("exploratory" in lab.lower() for lab in meta["labels"])


def test_one_panel_per_family(tmp_path):
    pts, _ = ba.game_points([g("B", 1, G1), g("B", 1, G1, family="fy"), g("A", 1, G2, family="fz")])
    assert _fig(tmp_path, pts)["panels"] == ["fx", "fy", "fz"]


def test_mock_stamp(tmp_path):
    pts, _ = ba.game_points([g("B", 1, G1)])
    assert _fig(tmp_path, pts, mock=True)["mock_stamp"] is True


def test_outputs_are_deterministic(tmp_path):
    pts, _ = ba.game_points([g("B", 1, G1, {5: ("accept", "accept")}), g("A", 1, G2)])
    for d in ("one", "two"):
        (tmp_path / d).mkdir()
        ba.make_figure(ba.jitter(pts), tmp_path / d / "f.pdf", tmp_path / d / "f.png", mock=True)
    for name in ("f.pdf", "f.png"):
        one, two = (tmp_path / "one" / name).read_bytes(), (tmp_path / "two" / name).read_bytes()
        assert one == two and len(one) > 1000


def test_cli_several_runs_dirs_csv_and_files(tmp_path):
    main_dir, expl_dir, out = tmp_path / "runs", tmp_path / "expl", tmp_path / "out"
    write_logs([g("B", 1, G1, {5: ("accept", "accept")}), g("A", 1, G2)], main_dir)
    e = g("C", 1, FLAT12, {5: ("decline", "decline")})
    e["game_id"] = "espion_think__fx__C__s1"
    write_logs([e], expl_dir)
    ba.main([str(main_dir), "--exploratory", str(expl_dir), "--out-dir", str(out), "--include-mock",
             "--all-configs"])
    for name in ("before_after.pdf", "before_after.png", "before_after.csv"):
        assert (out / name).exists(), name
    rows = list(csv.DictReader((out / "before_after.csv").open(encoding="utf-8")))
    by_id = {r["game_id"]: r for r in rows}
    assert set(by_id) == {"syn__fx__B__s1", "syn__fx__A__s1", "espion_think__fx__C__s1"}
    r = by_id["syn__fx__B__s1"]
    assert float(r["before_mean"]) == pytest.approx(41 / 3) and float(r["do_mean"]) == pytest.approx(58 / 3)
    assert r["say"] == "accept" and r["condition_name"] == "Direct offer" and r["exploratory"] == "0"
    assert abs(float(r["x_plotted"]) - 41 / 3) <= ba.JITTER
    assert by_id["espion_think__fx__C__s1"]["exploratory"] == "1"
    assert by_id["espion_think__fx__C__s1"]["say"] == "decline"
    assert r["mock"] == "1"


def test_cli_default_keeps_real_preregistered_games_only(tmp_path):
    runs = tmp_path / "runs"
    write_logs([g("B", 1, G1)], runs)  # mock and not a preregistered config
    with pytest.raises(SystemExit):
        ba.main([str(runs), "--out-dir", str(tmp_path / "out")])
