"""THINK showcase - EXPLORATORY, not preregistered (docs/team-artem/THINK_ARM.md, "Showcase").

Two higher-tier open-weight reasoning models that return the raw trace, each its own family in self-play
(no mixing), conditions B and E, seed 1: exactly 4 games, reasoning effort medium, pinned providers, writes to
runs_exploratory/think_showcase. Model ids and pins are written by hand from the OpenRouter /models and
/endpoints data of 2026-10-24 (THINK_ARM.md). The trace export keeps the offer round and the next 3 rounds:
the full traces go to a sidecar JSON file, the markdown excerpt is capped at 1,500 characters per firm.
"""
import json
from pathlib import Path

import pytest
import yaml

from harness.clients import load_prices
from harness.runner import expand_games, validate_config
from helpers3 import full_log
from tools import think_view

ROOT = Path(__file__).resolve().parent.parent
CONFIGS = ROOT / "configs"
DEEPSEEK = "deepseek/deepseek-v4-pro-0813"
QWEN = "qwen/qwen3.8-2.4t-a95b"
PINS = {
    "deepseek": {"order": ["deepinfra"], "allow_fallbacks": False, "quantizations": ["fp8"], "require_parameters": True},
    "qwen": {"order": ["novita"], "allow_fallbacks": False, "require_parameters": True},
}


def load(name):
    return yaml.safe_load((CONFIGS / f"{name}.yaml").read_text(encoding="utf-8"))


def test_showcase_config():
    s, core = load("exploratory/espion_think_showcase"), load("espion_core")
    validate_config(s)
    raw = (CONFIGS / "exploratory" / "espion_think_showcase.yaml").read_text(encoding="utf-8")
    assert "EXPLORATORY, not preregistered" in raw
    assert s["name"] == "espion_think_showcase" and s["think"] is True and s["mock"] is False
    assert s["out_dir"] == "runs_exploratory/think_showcase"
    assert s["conditions"] == ["B", "E"] and s["seeds"] == [1]
    for k in ("n_rounds", "spy_start", "demand", "temperature"):
        assert s[k] == core[k], k
    assert s["families"] == [
        {"family": "deepseek", "models": {"0": DEEPSEEK, "1": DEEPSEEK}, "reasoning": {"effort": "medium"},
         "provider": PINS["deepseek"]},
        {"family": "qwen", "models": {"0": QWEN, "1": QWEN}, "reasoning": {"effort": "medium"},
         "provider": PINS["qwen"]}]
    games = expand_games(s)
    assert len(games) == 4
    assert all(len(set(g.models.values())) == 1 for g in games)  # self-play only
    prices = load_prices()
    assert DEEPSEEK in prices and QWEN in prices


def long_game(family="deepseek", model=DEEPSEEK):
    """spy_start 2, 6 rounds; each trace is 1,000 characters, so 4 rounds give 4,000 > the 1,500 cap."""
    prices = [(10.0, 10.0)] * 6
    resp = [("no_message", "no_message"), ("accept", "decline")] + [("no_message", "no_message")] * 4
    g = full_log("B", family, 1, prices, resp, spy_start=2)
    g["game_id"] = f"espion_think_showcase__{family}__B__s1"
    g["models"] = {"0": model, "1": model}
    g["think"] = True
    for r in g["rounds"]:
        for fid, f in r["firms"].items():
            f["provenance"] = {"reasoning_text": f"r{r['round']}f{fid} " + "y" * (1000 - len(f"r{r['round']}f{fid} "))}
    return g


def test_trace_excerpt_is_capped_and_starts_at_offer_round():
    g = long_game()
    ex = think_view.trace_excerpt(g, "0", cap=1500)
    assert len(ex) <= 1500
    assert ex.startswith("[round 2] r2f0 ")
    assert "[round 1]" not in ex and "r6f0" not in ex


def test_export_traces_sidecar_has_full_traces(tmp_path):
    g = long_game()
    paths = think_view.export_traces([g], tmp_path, cap=1500)
    side = tmp_path / "traces" / f"{g['game_id']}.json"
    assert side in paths and (tmp_path / "think_traces.md") in paths
    data = json.loads(side.read_text(encoding="utf-8"))
    assert data["game_id"] == g["game_id"]
    for fid in ("0", "1"):
        rounds = data["firms"][fid]
        assert [r["round"] for r in rounds] == [2, 3, 4, 5]
        assert all(len(r["reasoning_text"]) == 1000 for r in rounds)
        assert rounds[0]["reasoning_text"].startswith(f"r2f{fid} ")
    md = (tmp_path / "think_traces.md").read_text(encoding="utf-8")
    assert "EXPLORATORY" in md
    assert think_view.trace_excerpt(g, "0", cap=1500) in md
    assert "y" * 1500 not in md


def test_think_view_handles_two_families(tmp_path):
    logs = [long_game(), long_game("qwen", QWEN)]
    rows = think_view.think_rows(logs, think_view.load_coder())
    assert {r["family"] for r in rows} == {"deepseek", "qwen"} and len(rows) == 16


def test_think_view_cli(tmp_path):
    runs = tmp_path / "runs_exploratory" / "think_showcase"
    runs.mkdir(parents=True)
    for g in (long_game(), long_game("qwen", QWEN)):
        (runs / f"{g['game_id']}.json").write_text(json.dumps(g), encoding="utf-8")
    out = tmp_path / "results_exploratory" / "think_showcase"
    assert think_view.main([str(runs), str(out)]) == 0
    for p in ("think_view.csv", "think_view.md", "think_excerpts.md", "think_traces.md",
              "traces/espion_think_showcase__qwen__B__s1.json"):
        assert (out / p).is_file(), p
