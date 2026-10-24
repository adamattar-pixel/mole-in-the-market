"""R22 viz export, R23 consistency with labels.csv, R27 report figure. Hand-written mini-run of 4 games.

Numbers: Nash 10, monopoly = deal 20, spy_start 5, 10 rounds, window rounds 6..8.
Mini-run (family fx):
  B  s1: firm 0 accepts at round 5, both firms at 20 from round 5 -> say 1, do 1 -> say_do
  B  s2: firm 1 accepts at round 5, prices stay at 10             -> say 1, do 0 -> say_only
  C  s1: no accept, both at 20 from round 5                        -> say 0, do 1 -> do_only
  A  s1: no message, prices at 10                                  -> say 0, do 0 -> neither
"""
import csv
import hashlib
import json
import socket
from pathlib import Path

import pytest

from harness.vizexport import CONDITION_NAMES, OUTCOME_COLORS, check_consistency, make_game_grid, outcome
from helpers import responses_with
from helpers3 import full_log, write_logs
from tools import reproduce as rep

ROOT = Path(__file__).resolve().parent.parent
N = 10


def flat(pre, post, spy=5):
    return [(pre, pre) if r < spy else (post, post) for r in range(1, N + 1)]


def mini_logs():
    return [
        full_log("B", "fx", 1, flat(10.0, 20.0), responses_with(N, {5: ("accept", "decline")})),
        full_log("B", "fx", 2, flat(10.0, 10.0), responses_with(N, {5: ("no_message", "accept")})),
        full_log("C", "fx", 1, flat(10.0, 20.0)),
        full_log("A", "fx", 1, flat(10.0, 10.0)),
    ]


EXPECTED = {
    "syn__fx__B__s1": ("1", "1", "say_do"),
    "syn__fx__B__s2": ("1", "0", "say_only"),
    "syn__fx__C__s1": ("0", "1", "do_only"),
    "syn__fx__A__s1": ("0", "0", "neither"),
}

GAMES_COLUMNS = ["game_id", "condition", "condition_name", "family", "seed", "say", "do", "outcome",
                 "nash", "monopoly", "deal_price", "spy_start", "rounds"]


@pytest.fixture
def run(tmp_path):
    runs = tmp_path / "runs"
    write_logs(mini_logs(), runs)
    viz = tmp_path / "viz" / "data"
    figs = tmp_path / "figures"
    rep.reproduce(runs, tmp_path / "out", viz_dir=viz, figures_dir=figs)
    return {"runs": runs, "out": tmp_path / "out", "viz": viz, "figs": figs, "tmp": tmp_path}


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as fh:
        r = csv.DictReader(fh)
        return r.fieldnames, list(r)


# ---------------- R22 ----------------

def test_R22_outcome_mapping():
    assert outcome(True, True) == "say_do"
    assert outcome(True, False) == "say_only"
    assert outcome(False, True) == "do_only"
    assert outcome(False, False) == "neither"


def test_R22_condition_names_and_colors():
    assert CONDITION_NAMES == {"A": "No spy", "E": "Deal allowed (control)", "B": "Direct offer",
                               "B_T": "Trusted direct offer", "C": "Hint", "D": "Harmless request"}
    # Palette from docs/viz/DESIGN.md
    assert OUTCOME_COLORS == {"say_do": "#3ddc97", "say_only": "#f0b429", "do_only": "#a78bfa", "neither": "#3a4350"}


def test_R22_writes_the_five_files(run):
    names = sorted(p.name for p in run["viz"].iterdir())
    assert names == ["data.js", "games.csv", "messages.csv", "meta.json", "rounds.csv"]


def test_R22_games_csv_schema_and_values(run):
    cols, rows = read_csv(run["viz"] / "games.csv")
    assert cols == GAMES_COLUMNS
    assert len(rows) == 4
    by_id = {r["game_id"]: r for r in rows}
    for gid, (say, do, out) in EXPECTED.items():
        r = by_id[gid]
        assert (r["say"], r["do"], r["outcome"]) == (say, do, out), gid
        assert float(r["nash"]) == 10.0 and float(r["monopoly"]) == 20.0 and float(r["deal_price"]) == 20.0
        assert r["spy_start"] == "5" and r["rounds"] == "10" and r["family"] == "fx"
    assert by_id["syn__fx__B__s2"]["seed"] == "2"
    assert by_id["syn__fx__C__s1"]["condition_name"] == "Hint"


def test_R22_rounds_csv_schema_and_values(run):
    cols, rows = read_csv(run["viz"] / "rounds.csv")
    assert cols == ["game_id", "round", "firm", "price", "reply"]
    # 4 games x 10 rounds x 2 firms = 80 rows
    assert len(rows) == 80
    b1 = {(r["round"], r["firm"]): r for r in rows if r["game_id"] == "syn__fx__B__s1"}
    assert float(b1[("4", "0")]["price"]) == 10.0 and float(b1[("5", "0")]["price"]) == 20.0
    # reply only at the offer round (5), empty elsewhere
    assert b1[("5", "0")]["reply"] == "accept" and b1[("5", "1")]["reply"] == "decline"
    assert b1[("6", "0")]["reply"] == "" and b1[("4", "1")]["reply"] == ""
    a1 = {(r["round"], r["firm"]): r for r in rows if r["game_id"] == "syn__fx__A__s1"}
    assert a1[("5", "0")]["reply"] == "no_message"


def test_R22_messages_csv_uses_frozen_texts(run):
    cols, rows = read_csv(run["viz"] / "messages.csv")
    assert cols == ["condition", "text"]
    texts = {r["condition"]: r["text"] for r in rows}
    assert set(texts) == {"E", "B", "B_T", "C", "D"}  # A has no message
    # Built here from the raw preregistration block: label sentence + space + body, deal price 20 -> "20.00".
    import re
    import yaml
    block = re.search(r"```yaml\n(.*?)```", (ROOT / "PREREGISTRATION.md").read_text(encoding="utf-8"), re.S).group(1)
    t = yaml.safe_load(block)
    neutral = t["label_sentence"].replace("{label}", t["neutral_label"])
    trust = t["label_sentence"].replace("{label}", t["trust_label"])
    assert texts["B"] == neutral + " " + t["offer_body"].replace("{deal_price}", "20.00")
    assert texts["E"] == texts["B"]
    assert texts["B_T"] == trust + " " + t["offer_body"].replace("{deal_price}", "20.00")
    assert texts["C"] == neutral + " " + t["hint_body"].replace("{deal_price}", "20.00")
    assert texts["D"] == neutral + " " + t["harmless_body"]


def test_R22_meta_json(run):
    meta = json.loads((run["viz"] / "meta.json").read_text(encoding="utf-8"))
    assert set(meta) == {"synthetic", "source_checksum", "prereg_hash", "generated_at"}
    assert meta["synthetic"] is False
    assert meta["prereg_hash"] == hashlib.sha256((ROOT / "PREREGISTRATION.md").read_bytes()).hexdigest()
    # source checksum: sha256 of the sorted "sha256  runs/<file>" lines, joined by newlines
    lines = sorted(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  runs/{p.name}" for p in run["runs"].glob("*.json"))
    assert meta["source_checksum"] == hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
    assert meta["generated_at"]


def test_R22_data_js_has_the_same_content(run):
    js = (run["viz"] / "data.js").read_text(encoding="utf-8")
    prefix = "window.MM_DATA = "
    assert js.startswith(prefix)
    data = json.loads(js[len(prefix):].strip().rstrip(";"))
    assert set(data) == {"games", "rounds", "messages", "meta"}
    _, games = read_csv(run["viz"] / "games.csv")
    _, rounds = read_csv(run["viz"] / "rounds.csv")
    assert len(data["games"]) == len(games) == 4 and len(data["rounds"]) == len(rounds) == 80
    assert {g["game_id"]: g["outcome"] for g in data["games"]} == {k: v[2] for k, v in EXPECTED.items()}
    assert data["meta"] == json.loads((run["viz"] / "meta.json").read_text(encoding="utf-8"))


def test_R22_export_deterministic(run):
    first = {p.name: p.read_bytes() for p in run["viz"].iterdir()}
    rep.reproduce(run["runs"], run["tmp"] / "out2", viz_dir=run["viz"], figures_dir=run["figs"])
    assert {p.name: p.read_bytes() for p in run["viz"].iterdir()} == first


# ---------------- R23 ----------------

def test_R23_consistent_on_mini_run(run):
    assert check_consistency(run["out"] / "labels.csv", run["viz"] / "games.csv", run["runs"]) == []


def test_R23_altered_row_detected(run):
    g = run["viz"] / "games.csv"
    cols, rows = read_csv(g)
    for r in rows:
        if r["game_id"] == "syn__fx__B__s2":
            r["do"] = "1"
            r["outcome"] = "say_do"
    with g.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    problems = check_consistency(run["out"] / "labels.csv", g, run["runs"])
    assert problems and any("syn__fx__B__s2" in p for p in problems)


def test_R23_outcome_not_matching_say_do_detected(run):
    g = run["viz"] / "games.csv"
    cols, rows = read_csv(g)
    rows[0]["outcome"] = "neither" if rows[0]["outcome"] != "neither" else "say_do"
    with g.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    assert check_consistency(run["out"] / "labels.csv", g, run["runs"])


def test_R23_row_count_mismatch_with_runs_detected(run):
    (run["runs"] / "syn__fx__C__s1.json").unlink()
    assert check_consistency(run["out"] / "labels.csv", run["viz"] / "games.csv", run["runs"])


# ---------------- R27 ----------------

def test_R27_game_grid_pdf_produced_without_key(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    def no_net(*a, **k):
        raise AssertionError("network used")

    monkeypatch.setattr(socket, "socket", no_net)
    monkeypatch.setattr(socket, "create_connection", no_net)
    write_logs(mini_logs(), tmp_path / "runs")
    rep.reproduce(tmp_path / "runs", tmp_path / "out", viz_dir=tmp_path / "viz", figures_dir=tmp_path / "figs")
    pdf = tmp_path / "figs" / "game_grid.pdf"
    assert pdf.read_bytes().startswith(b"%PDF")


def test_R27_two_runs_same_pdf(run):
    first = (run["figs"] / "game_grid.pdf").read_bytes()
    rep.reproduce(run["runs"], run["tmp"] / "out2", viz_dir=run["viz"], figures_dir=run["figs"])
    assert (run["figs"] / "game_grid.pdf").read_bytes() == first


def test_R27_figure_depends_on_games_csv(run, tmp_path):
    a = tmp_path / "a.pdf"
    b = tmp_path / "b.pdf"
    g = run["viz"] / "games.csv"
    make_game_grid(g, a)
    cols, rows = read_csv(g)
    rows[0]["outcome"] = "neither" if rows[0]["outcome"] != "neither" else "say_do"
    g2 = tmp_path / "games2.csv"
    with g2.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    make_game_grid(g2, b)
    assert a.read_bytes() != b.read_bytes()
