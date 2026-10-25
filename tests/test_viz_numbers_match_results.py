"""Guard: the numbers the replay page shows (it reads only viz/data/data.js) equal the committed outputs.

- data.js holds the same games, rounds and meta as the committed CSV/JSON files of viz/data/;
- per condition, the say and do counts of viz/data/games.csv equal results/summary.json (family meta-llama);
- the failed family banner uses the pilot-only E effect: anthropic FAIL, 0.111 (validate_e --config espion_pilot),
  never the pooled 0.277 that validate_e prints without --config (OPEN_ISSUES #24).
"""
import csv
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
VIZ = ROOT / "viz" / "data"


def data_js():
    text = (VIZ / "data.js").read_text(encoding="utf-8")
    prefix = "window.MM_DATA = "
    assert text.startswith(prefix)
    return json.loads(text[len(prefix):].strip().rstrip(";"))


def games_csv():
    with (VIZ / "games.csv").open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_data_js_equals_the_committed_csv_and_meta():
    d = data_js()
    assert d["meta"] == json.loads((VIZ / "meta.json").read_text(encoding="utf-8"))
    g = games_csv()
    assert len(d["games"]) == len(g) == 30
    assert {x["game_id"]: (int(x["say"]), int(x["do"]), x["outcome"]) for x in d["games"]} == \
           {x["game_id"]: (int(x["say"]), int(x["do"]), x["outcome"]) for x in g}


def test_say_do_counts_equal_results_summary():
    rates = json.loads((ROOT / "results" / "summary.json").read_text(encoding="utf-8"))["rates"]["meta-llama"]
    g = games_csv()
    for cond, r in rates.items():
        rows = [x for x in g if x["condition"] == cond]
        assert len(rows) == r["n"], cond
        assert sum(int(x["say"]) for x in rows) == r["say"]["k"], cond
        assert sum(int(x["do"]) for x in rows) == r["do"]["k"], cond


def test_failed_family_banner_is_the_pilot_only_value():
    ev = data_js()["meta"]["excluded_families"]["anthropic"]["e_validation"]
    assert ev["pass"] is False
    assert ev["effect_gap_fraction"] == pytest.approx(0.111, abs=0.0005)
    assert (ev["n_A"], ev["n_E"]) == (5, 5)  # pilot only: 5 + 5 games, no smoke game pooled
    for f in ("data.js", "meta.json"):
        assert "0.277" not in (VIZ / f).read_text(encoding="utf-8")
    for f in ("index.html", "app.js"):
        assert "0.277" not in (ROOT / "viz" / f).read_text(encoding="utf-8")
