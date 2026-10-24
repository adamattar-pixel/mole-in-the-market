"""Report figure tool (tools/price_paths.py): price paths per family and the page 1 excerpt.

Descriptive figure from the logs only (no API key, no network). Hand-built mini runs below, with the
expected per-round means, minima and maxima worked out by hand in the comments.
"""
import json

import pytest

from harness.conditions import CONDITIONS
from helpers import responses_with
from helpers3 import full_log, write_logs
from tools import price_paths as pp

# Family fx, spy_start 2, Nash 10, monopoly = deal 20, 4 rounds.
# B seed 1: per-round mean of both firms = 11, 15, 19, 19
B1 = [(10.0, 12.0), (14.0, 16.0), (20.0, 18.0), (19.0, 19.0)]
# B seed 2: per-round mean = 10, 12, 18, 13
B2 = [(10.0, 10.0), (10.0, 14.0), (16.0, 20.0), (13.0, 13.0)]
# -> B mean over seeds: 10.5, 13.5, 18.5, 16.0 | min 10, 12, 18, 13 | max 11, 15, 19, 19
# A seed 1: per-round mean = 12, 12, 12, 12 (min = max = mean)
A1 = [(11.0, 13.0), (12.0, 12.0), (12.0, 12.0), (12.0, 12.0)]
# Memory arm, B seed 1: 20 everywhere
M1 = [(20.0, 20.0)] * 4
# Family fy: B seed 1 = 10 everywhere (4 rounds), B seed 2 = 17 per round but only 3 rounds.
# -> rounds 1-3 mean (10 + 17) / 2 = 13.5, min 10, max 17, n 2 | round 4 mean 10, n 1
FY1 = [(10.0, 10.0)] * 4
FY2 = [(16.0, 18.0)] * 3


def core_logs():
    return [full_log("B", "fx", 1, B1, spy_start=2), full_log("B", "fx", 2, B2, spy_start=2),
            full_log("A", "fx", 1, A1, spy_start=2),
            full_log("B", "fy", 1, FY1, spy_start=2), full_log("B", "fy", 2, FY2, spy_start=2)]


def memory_log():
    g = full_log("B", "fx", 1, M1, spy_start=2)
    g["memory"] = True
    g["game_id"] = "espion_mem__fx__B__s1"
    return g


def test_per_round_mean_min_max_over_seeds_by_hand():
    paths = pp.price_paths(core_logs())
    b = paths["fx"]["B"]
    assert b["round"] == [1, 2, 3, 4]
    assert b["mean"] == pytest.approx([10.5, 13.5, 18.5, 16.0])
    assert b["lo"] == pytest.approx([10.0, 12.0, 18.0, 13.0])
    assert b["hi"] == pytest.approx([11.0, 15.0, 19.0, 19.0])
    assert b["n"] == [2, 2, 2, 2]
    a = paths["fx"]["A"]
    assert a["mean"] == pytest.approx([12.0] * 4)
    assert a["lo"] == pytest.approx([12.0] * 4) and a["hi"] == pytest.approx([12.0] * 4)
    assert set(paths) == {"fx", "fy"}
    assert set(paths["fx"]) == {"A", "B"}


def test_unequal_game_lengths_use_available_games_only():
    fy = pp.price_paths(core_logs())["fy"]["B"]
    assert fy["round"] == [1, 2, 3, 4]
    assert fy["mean"] == pytest.approx([13.5, 13.5, 13.5, 10.0])
    assert fy["lo"] == pytest.approx([10.0, 10.0, 10.0, 10.0])
    assert fy["hi"] == pytest.approx([17.0, 17.0, 17.0, 10.0])
    assert fy["n"] == [2, 2, 2, 1]


def test_memory_arm_is_a_separate_arm():
    paths = pp.price_paths(core_logs() + [memory_log()])
    assert set(paths["fx"]) == {"A", "B", "B_mem"}
    assert paths["fx"]["B_mem"]["mean"] == pytest.approx([20.0] * 4)
    assert paths["fx"]["B"]["mean"] == pytest.approx([10.5, 13.5, 18.5, 16.0])


def test_arm_order_follows_condition_order_then_memory():
    paths = pp.price_paths(core_logs() + [memory_log()])
    assert pp.ordered_arms(paths["fx"]) == ["A", "B", "B_mem"]


def test_reference_lines_and_do_window():
    refs = pp.reference_lines(core_logs())
    assert refs["fx"] == {"nash": 10.0, "monopoly": 20.0, "deal": 20.0, "spy_start": 2}
    # behavioral window 3 (PREREGISTRATION.md): rounds spy_start+1 .. spy_start+3
    assert pp.do_window(2) == (3, 5)
    assert pp.do_window(8) == (9, 11)


def test_reference_lines_refuse_inconsistent_games_in_a_family():
    logs = core_logs()
    logs[1]["nash_price"] = 11.0
    with pytest.raises(ValueError):
        pp.reference_lines(logs)


def test_labels_use_full_condition_names_never_bare_letters():
    assert pp.arm_label("A") == "No spy"
    assert pp.arm_label("B_T") == "Trusted direct offer"
    assert pp.arm_label("E") == "Deal allowed (control)"
    assert pp.arm_label("B_mem") == "Direct offer (memory arm, exploratory)"
    for c in CONDITIONS:
        assert pp.arm_label(c) not in CONDITIONS


def test_figure_legend_labels_are_full_names(tmp_path):
    logs = core_logs() + [memory_log()]
    labels = pp.make_price_paths(pp.price_paths(logs), pp.reference_lines(logs), tmp_path / "p.pdf")
    assert "Direct offer" in labels and "No spy" in labels
    assert "Direct offer (memory arm, exploratory)" in labels
    assert not set(labels) & set(CONDITIONS)
    assert not set(labels) & {"B_mem", "A_mem", "D_mem"}


def test_pdf_written_without_key_and_byte_identical(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    logs = core_logs() + [memory_log()]
    out = tmp_path / "figs" / "price_paths.pdf"
    pp.make_price_paths(pp.price_paths(logs), pp.reference_lines(logs), out)
    first = out.read_bytes()
    assert first.startswith(b"%PDF")
    assert b"CreationDate" not in first and b"ModDate" not in first
    pp.make_price_paths(pp.price_paths(logs), pp.reference_lines(logs), out)
    assert out.read_bytes() == first


# Excerpt game: spy_start 5, Nash 10, monopoly = deal 20, 9 rounds. do tolerance = 10% x 10 = 1.0
EX_PRICES = [(10.0, 10.0)] * 3 + [(11.0, 10.5), (12.25, 10.0), (19.5, 10.0), (20.0, 11.0),
                                 (19.125, 10.0), (15.0, 15.0)]
REPLY0 = '{"price": 12.25, "response_to_message": "accept", "note": "ok | fine"}'
REPLY1 = '```json\n{"price": 10.0, "response_to_message": "decline"}\n```'


def excerpt_log():
    g = full_log("B", "fx", 3, EX_PRICES, responses_with(9, {5: ("accept", "decline")}))
    g["message"] = "This message is from another agent in the market. Proposal: test text."
    g["rounds"][4]["firms"]["0"]["reply"] = REPLY0
    g["rounds"][4]["firms"]["1"]["reply"] = REPLY1
    return g


def test_excerpt_has_message_replies_verbatim_and_price_table():
    md = pp.excerpt_md(excerpt_log())
    assert "syn__fx__B__s3" in md
    assert "Direct offer" in md
    assert "This message is from another agent in the market. Proposal: test text." in md
    assert REPLY0 in md and REPLY1 in md
    assert "20.000" in md and "10.000" in md and "1.000" in md  # deal, Nash, tolerance
    lines = md.splitlines()
    head = lines.index("| Round | Firm 0 price | Firm 1 price | Firm 0 reply field | Firm 1 reply field | Note |")
    rows = lines[head + 2: head + 7]
    assert rows == [
        "| 4 | 11.000 | 10.500 | no_message | no_message | before the spy message |",
        "| 5 | 12.250 | 10.000 | accept | decline | spy message |",
        "| 6 | 19.500 | 10.000 | no_message | no_message | do window |",
        "| 7 | 20.000 | 11.000 | no_message | no_message | do window |",
        "| 8 | 19.125 | 10.000 | no_message | no_message | do window |",
    ]
    assert not lines[head + 7].startswith("| 9 ")  # round spy_start+4 is not in the excerpt


def test_excerpt_fence_survives_backticks_in_a_reply():
    md = pp.excerpt_md(excerpt_log())
    # REPLY1 holds a ``` fence, so its block must use a longer fence and stay intact
    assert "````\n" + REPLY1 + "\n````" in md


def test_excerpt_short_game_and_no_message():
    g = full_log("A", "fx", 1, [(10.0, 10.0)] * 6)  # spy_start 5, rounds 4..6 only
    g["message"] = None
    md = pp.excerpt_md(g)
    assert "No spy" in md and "(no message)" in md
    assert "| 6 | 10.000 | 10.000 |" in md
    assert "| 7 |" not in md and "| 3 |" not in md


def test_find_game_unknown_id_raises():
    with pytest.raises(KeyError):
        pp.find_game(core_logs(), "nope")
    assert pp.find_game(core_logs(), "syn__fx__A__s1")["condition"] == "A"


def _real(g):
    g = json.loads(json.dumps(g))
    g["mock"] = False
    g["game_id"] = "espion_core__" + g["game_id"]
    return g


def test_cli_writes_outputs_and_filters_like_reproduce(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    runs, mem, out = tmp_path / "runs", tmp_path / "mem", tmp_path / "out"
    real = [_real(g) for g in core_logs()] + [_real(excerpt_log())]
    write_logs(real + [full_log("C", "fx", 9, A1, spy_start=2)], runs)  # mock C game: dropped by default
    m = memory_log()
    m["mock"] = False
    write_logs([m], mem)
    pp.main([str(runs), "--out-dir", str(out), "--memory-runs", str(mem),
             "--game-id", "espion_core__syn__fx__B__s3"])
    assert (out / "price_paths.pdf").read_bytes().startswith(b"%PDF")
    ex = (out / "excerpt.md").read_text(encoding="utf-8")
    assert REPLY0 in ex
    assert REPLY0 in capsys.readouterr().out
    used = pp.load_arms(runs, mem, include_mock=False, all_configs=False)
    assert "C" not in {g["condition"] for g in used}
    assert any(g.get("memory") for g in used)


def test_cli_refuses_memory_logs_in_the_main_folder_and_frozen_logs_in_memory_folder(tmp_path):
    runs, mem = tmp_path / "runs", tmp_path / "mem"
    write_logs(core_logs() + [memory_log()], runs)
    with pytest.raises(ValueError):
        pp.load_arms(runs, None, include_mock=True, all_configs=True)
    write_logs(core_logs(), tmp_path / "r2")
    write_logs([full_log("A", "fx", 7, A1, spy_start=2)], mem)
    with pytest.raises(ValueError):
        pp.load_arms(tmp_path / "r2", mem, include_mock=True, all_configs=True)
