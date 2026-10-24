"""R24 static offline page (tools/check_viz.py) and R25 demo data (tools/make_demo_data.py).

Page layout (docs/viz/DESIGN.md): viz/index.html loads ONLY data/data.js (real export of reproduce);
viz/demo.html loads ONLY demo/data.js (invented data). Both share viz/app.js and viz/style.css.
"""
import csv
import json
from pathlib import Path

import pytest

from harness.vizexport import GAMES_COLUMNS, ROUNDS_COLUMNS, outcome
from tools import check_viz, make_demo_data

ROOT = Path(__file__).resolve().parent.parent
VIZ = ROOT / "viz"

CLEAN_INDEX = '<!doctype html><html><head><link rel="stylesheet" href="style.css"></head><body>' \
              '<script src="data/data.js"></script><script src="app.js"></script></body></html>'


# ---------------- R24 check_viz on hand-built pages ----------------

def test_R24_clean_page_has_no_problem():
    assert check_viz.check_page(CLEAN_INDEX, "data/data.js", js_sources={"app.js": "const x = 1;"}) == []


@pytest.mark.parametrize("bad", [
    '<script src="https://cdn.example.org/d3.js"></script>',
    '<link rel="stylesheet" href="https://fonts.example.org/x.css">',
    '<img src="//cdn.example.org/a.png">',
])
def test_R24_external_url_detected(bad):
    html = CLEAN_INDEX.replace("</body>", bad + "</body>")
    assert check_viz.check_page(html, "data/data.js", js_sources={"app.js": ""})


@pytest.mark.parametrize("js", ["fetch('data/games.csv')", "new XMLHttpRequest()", "new WebSocket('ws://x')",
                                "navigator.sendBeacon('/x')", "import('https://x.org/m.js')", "new EventSource('/s')"])
def test_R24_network_call_in_js_detected(js):
    assert check_viz.check_page(CLEAN_INDEX, "data/data.js", js_sources={"app.js": js})


def test_R24_only_the_expected_data_file_is_loaded():
    # Trap: a second data file (for example the demo data) loaded by the real page.
    two = CLEAN_INDEX.replace('<script src="app.js">', '<script src="demo/data.js"></script><script src="app.js">')
    assert check_viz.check_page(two, "data/data.js", js_sources={"app.js": ""})
    missing = CLEAN_INDEX.replace('<script src="data/data.js"></script>', "")
    assert check_viz.check_page(missing, "data/data.js", js_sources={"app.js": ""})
    other = CLEAN_INDEX.replace('<script src="app.js"></script>', '<script src="extra.js"></script><script src="app.js"></script>')
    assert check_viz.check_page(other, "data/data.js", js_sources={"app.js": "", "extra.js": ""})


def test_R24_inline_external_url_in_js_detected():
    assert check_viz.check_page(CLEAN_INDEX, "data/data.js", js_sources={"app.js": "img.src = 'https://x.org/a.png'"})


# ---------------- R24 on the real page files ----------------

def test_R24_real_index_and_demo_pages_pass():
    assert check_viz.check_repo(VIZ) == []


def test_R24_real_index_loads_only_real_data_and_demo_only_demo_data():
    idx = (VIZ / "index.html").read_text(encoding="utf-8")
    demo = (VIZ / "demo.html").read_text(encoding="utf-8")
    assert check_viz.script_sources(idx) == ["data/data.js", "app.js"]
    assert check_viz.script_sources(demo) == ["demo/data.js", "app.js"]


def test_R25_page_has_demo_banner_gated_on_synthetic():
    app = (VIZ / "app.js").read_text(encoding="utf-8")
    assert "DEMO DATA | NOT RESULTS" in app
    assert "meta.synthetic" in app


def test_R24_page_has_the_design_sections():
    app = (VIZ / "app.js").read_text(encoding="utf-8") + (VIZ / "index.html").read_text(encoding="utf-8")
    for title in ("Pick a game", "Replay", "Inspector", "What the games say", "Prices in this game"):
        assert title in app, title
    assert "prefers-reduced-motion" in (VIZ / "app.js").read_text(encoding="utf-8") + (VIZ / "style.css").read_text(encoding="utf-8")


# ---------------- R25 demo data ----------------

def read_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        r = csv.DictReader(fh)
        return r.fieldnames, list(r)


@pytest.fixture
def demo(tmp_path):
    root = tmp_path / "repo"
    (root / "runs").mkdir(parents=True)
    (root / "runs" / "real.json").write_text('{"keep": true}', encoding="utf-8")
    (root / "results").mkdir()
    (root / "results" / "labels.csv").write_text("game_id\nreal\n", encoding="utf-8")
    out = root / "viz" / "demo"
    make_demo_data.main(["--out", str(out), "--seed", "1"])
    return root, out


def test_R25_writes_contract_files_with_synthetic_true(demo):
    _, out = demo
    assert sorted(p.name for p in out.iterdir()) == ["data.js", "games.csv", "messages.csv", "meta.json", "rounds.csv"]
    meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
    assert meta["synthetic"] is True
    js = (out / "data.js").read_text(encoding="utf-8")
    data = json.loads(js[len("window.MM_DATA = "):].strip().rstrip(";"))
    assert data["meta"]["synthetic"] is True


def test_R25_never_touches_runs_or_labels(demo):
    root, out = demo
    assert (root / "runs" / "real.json").read_text(encoding="utf-8") == '{"keep": true}'
    assert sorted(p.name for p in (root / "runs").iterdir()) == ["real.json"]
    assert (root / "results" / "labels.csv").read_text(encoding="utf-8") == "game_id\nreal\n"
    written = [p for p in root.rglob("*") if p.is_file()]
    assert all(out in p.parents or p.parent in (root / "runs", root / "results") for p in written)


@pytest.mark.parametrize("bad", ["runs", "runs/demo", "viz/data", "results"])
def test_R25_refuses_real_data_locations(tmp_path, bad):
    with pytest.raises(ValueError):
        make_demo_data.main(["--out", str(tmp_path / bad)])


def test_R25_demo_schema_and_consistency(demo):
    _, out = demo
    gcols, games = read_csv(out / "games.csv")
    rcols, rounds = read_csv(out / "rounds.csv")
    assert tuple(gcols) == GAMES_COLUMNS and tuple(rcols) == ROUNDS_COLUMNS
    # 6 conditions x 5 seeds x 2 families = 60 games, 20 rounds x 2 firms each
    assert len(games) == 60 and len(rounds) == 60 * 20 * 2
    for g in games:
        assert g["outcome"] == outcome(g["say"] == "1", g["do"] == "1")


def test_R25_demo_offer_texts_are_the_frozen_texts(demo):
    _, out = demo
    import re
    import yaml
    t = yaml.safe_load(re.search(r"```yaml\n(.*?)```", (ROOT / "PREREGISTRATION.md").read_text(encoding="utf-8"), re.S).group(1))
    _, msgs = read_csv(out / "messages.csv")
    texts = {m["condition"]: m["text"] for m in msgs}
    neutral = t["label_sentence"].replace("{label}", t["neutral_label"])
    assert texts["D"] == neutral + " " + t["harmless_body"]
    assert texts["B"].startswith(neutral + " ") and texts["B_T"].startswith(t["label_sentence"].replace("{label}", t["trust_label"]))


def test_R25_demo_deterministic(tmp_path):
    a, b = tmp_path / "viz" / "demo_a", tmp_path / "viz" / "demo_b"
    make_demo_data.main(["--out", str(a), "--seed", "3"])
    make_demo_data.main(["--out", str(b), "--seed", "3"])
    assert (a / "games.csv").read_bytes() == (b / "games.csv").read_bytes()
    assert (a / "rounds.csv").read_bytes() == (b / "rounds.csv").read_bytes()
