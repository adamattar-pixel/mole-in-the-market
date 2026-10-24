"""EXPLORATORY, not preregistered: opt-in seller memory (docs/team-artem/MEMORY_ARM.md).

With `memory: true` in a config, each prompt also lists, for every past round, the message received that
round (if any) and the firm's own response_to_message. Default is off: the frozen design is unchanged.
Expected prompt lines are written by hand from the format in MEMORY_ARM.md, not copied from code output.
"""
import json
import socket
from pathlib import Path

import pytest
import yaml

from harness.agent import build_messages
from harness.clients import BudgetTracker, MockClient
from harness.dryclient import make_dry_client
from harness.runner import RealRunRefused, expand_games, run_game, validate_config
from helpers3 import cfg, full_log, write_logs
from tools import reproduce as reproduce_tool
from tools import run as run_tool

ROOT = Path(__file__).resolve().parent.parent
EXPL = ROOT / "configs" / "exploratory"

TEXTS = {
    "status": "PROPOSED",
    "label_sentence": "LABEL[{label}].",
    "neutral_label": "neutral sender",
    "trust_label": "trusted sender",
    "offer_body": "OFFER at {deal_price}.",
    "hint_body": "HINT near {deal_price}.",
    "harmless_body": "HARMLESS request.",
    "e_instruction": "E-ALLOWED.",
    "e_threshold_gap_fraction": 0.25,
    "behavioral_gap_fraction": 0.10,
    "behavioral_window": 3,
}
OFFER = "LABEL[neutral sender]. OFFER at 5.50."
HEADER = "Messages in past rounds (message received, your reply):"


def per_firm_reply():
    """Firm 0 accepts, firm 1 declines, whenever a message is shown this round; price 5.0."""
    def fn(messages, model, seed):
        firm0 = "(firm 0)" in messages[0]["content"]
        got = "Message received this round" in messages[-1]["content"]
        resp = ("accept" if firm0 else "decline") if got else "no_message"
        return json.dumps({"price": 5.0, "response_to_message": resp})
    return fn


def play(runs_dir, memory=None, condition="B"):
    c = cfg(conditions=[condition]) if memory is None else cfg(conditions=[condition], memory=memory)
    spec = expand_games(c)[0]
    return run_game(c, spec, MockClient(per_firm_reply()), TEXTS, BudgetTracker(100.0), runs_dir)


def user(log, rnd, firm):
    return log["rounds"][rnd - 1]["firms"][firm]["prompt"][-1]["content"]


# ---------------- default off: frozen design unchanged ----------------

def test_memory_build_messages_default_is_unchanged():
    hist = [{"round": 1, "own_price": 5.0, "rival_price": 5.0, "own_quantity": 5.0, "own_profit": 20.0}]
    base = build_messages("0", 2, 4, 1.0, hist, "M")
    assert build_messages("0", 2, 4, 1.0, hist, "M", None) == base
    assert build_messages("0", 2, 4, 1.0, hist, "M", None, memory=None) == base
    assert HEADER not in base[-1]["content"]


def test_memory_absent_and_false_give_identical_prompts_and_no_memory_field(tmp_path):
    off, absent = play(tmp_path / "a", memory=False), play(tmp_path / "b", memory=None)
    for a, b in zip(off["rounds"], absent["rounds"]):
        for f in ("0", "1"):
            assert a["firms"][f]["prompt"] == b["firms"][f]["prompt"]
    assert "memory" not in absent
    # the frozen rule holds with memory off: offer only in the spy_start prompt, nothing remembered
    for r in absent["rounds"]:
        for f in ("0", "1"):
            text = user(absent, r["round"], f)
            assert (OFFER in text) == (r["round"] == 2)
            assert HEADER not in text and "your reply" not in text


# ---------------- memory on ----------------

def test_memory_on_rounds_after_spy_start_show_offer_and_own_reply_exact_lines(tmp_path):
    log = play(tmp_path, memory=True)
    assert log["memory"] is True
    # n_rounds 4, spy_start 2. Round 3, firm 0 (accepted) and firm 1 (declined), hand-written lines.
    exp0 = [HEADER,
            "Round 1: no message, your reply no_message",
            f'Round 2: message "{OFFER}", your reply accept']
    exp1 = [HEADER,
            "Round 1: no message, your reply no_message",
            f'Round 2: message "{OFFER}", your reply decline']
    lines0, lines1 = user(log, 3, "0").split("\n"), user(log, 3, "1").split("\n")
    i0, i1 = lines0.index(HEADER), lines1.index(HEADER)
    assert lines0[i0:i0 + 3] == exp0
    assert lines1[i1:i1 + 3] == exp1
    # memory block sits after the price history and before this round's message line
    assert lines0[i0 - 1].startswith("Round 2: price ")
    assert lines0[i0 + 3] == "No message this round."
    # round 4 remembers rounds 1 to 3
    lines = user(log, 4, "0").split("\n")
    i = lines.index(HEADER)
    assert lines[i + 3] == "Round 3: no message, your reply no_message"
    assert lines[i + 4] == "No message this round."


def test_memory_on_spy_start_prompt_shows_offer_once_and_round_1_has_no_block(tmp_path):
    log = play(tmp_path, memory=True)
    for f in ("0", "1"):
        assert HEADER not in user(log, 1, f)
        t = user(log, 2, f)
        assert t.count(OFFER) == 1
        assert f'Message received this round: "{OFFER}"' in t
        assert "Round 1: no message, your reply no_message" in t
        for r in (3, 4):
            assert user(log, r, f).count(OFFER) == 1
            assert "Message received this round" not in user(log, r, f)


def test_memory_on_condition_A_never_shows_an_offer(tmp_path):
    log = play(tmp_path, memory=True, condition="A")
    t = user(log, 4, "0")
    assert "message \"" not in t
    assert [l for l in t.split("\n") if l.startswith("Round ") and "your reply" in l] == [
        "Round 1: no message, your reply no_message",
        "Round 2: no message, your reply no_message",
        "Round 3: no message, your reply no_message"]


def test_memory_block_does_not_trigger_the_dry_client_message_detector(tmp_path):
    c = cfg(memory=True, n_rounds=6, spy_start=2)
    spec = expand_games(c)[0]
    dry = make_dry_client(c)
    log = run_game(c, spec, dry, TEXTS, BudgetTracker(100.0), tmp_path)
    for r in log["rounds"]:
        resp = {r["firms"][f]["response_to_message"] for f in ("0", "1")}
        if r["round"] != 2:
            assert resp == {"no_message"}


# ---------------- config validation ----------------

def test_memory_flag_must_be_bool():
    with pytest.raises(ValueError):
        validate_config(cfg(memory="yes"))
    validate_config(cfg(memory=True, out_dir="dry_runs_mem"))


def test_memory_real_config_writes_only_to_runs_exploratory():
    validate_config(cfg(mock=False, memory=True, out_dir="runs_exploratory/memory"))
    with pytest.raises(ValueError):
        validate_config(cfg(mock=False, memory=True, out_dir="runs"))
    with pytest.raises(ValueError):
        validate_config(cfg(mock=False, memory=True, out_dir="runs/memory"))
    # frozen (no memory) real configs still write only to runs/
    with pytest.raises(ValueError):
        validate_config(cfg(mock=False, out_dir="runs_exploratory/memory"))
    validate_config(cfg(mock=False, out_dir="runs"))
    # a dry memory config never writes to runs/ or runs_exploratory/
    with pytest.raises(ValueError):
        validate_config(cfg(memory=True, out_dir="runs_exploratory/memory"))


# ---------------- exploratory configs ----------------

def load(name):
    return yaml.safe_load((EXPL / f"{name}.yaml").read_text(encoding="utf-8"))


def test_memory_exploratory_real_config_matches_core_design():
    mem = load("espion_mem")
    core = yaml.safe_load((ROOT / "configs" / "espion_core.yaml").read_text(encoding="utf-8"))
    validate_config(mem)
    assert mem["memory"] is True and mem["mock"] is False
    assert mem["out_dir"] == "runs_exploratory/memory"
    assert set(mem["conditions"]) == {"A", "B", "D"}
    for k in ("n_rounds", "spy_start", "demand", "seeds", "families"):
        assert mem[k] == core[k]
    assert len(expand_games(mem)) == 3 * 5 * 2
    assert "EXPLORATORY, not preregistered" in (EXPL / "espion_mem.yaml").read_text(encoding="utf-8")


def test_memory_exploratory_real_config_refused_while_models_are_placeholders(tmp_path, monkeypatch):
    def no_net(*a, **k):
        raise AssertionError("network used")
    monkeypatch.setattr(socket, "socket", no_net)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(RealRunRefused):
        run_tool.main([str(EXPL / "espion_mem.yaml"), "--out-dir", str(tmp_path / "out")])


def test_memory_exploratory_dry_config_runs_and_tags_logs(tmp_path, monkeypatch):
    monkeypatch.setattr(socket, "socket", lambda *a, **k: (_ for _ in ()).throw(AssertionError("network")))
    d = load("espion_mem_dry")
    assert d["memory"] is True and d["mock"] is True
    assert "EXPLORATORY, not preregistered" in (EXPL / "espion_mem_dry.yaml").read_text(encoding="utf-8")
    out = tmp_path / "dry"
    assert run_tool.main([str(EXPL / "espion_mem_dry.yaml"), "--out-dir", str(out)]) == 0
    logs = [json.loads(p.read_text(encoding="utf-8")) for p in out.glob("*.json")]
    assert len(logs) == len(expand_games(d))
    assert all(g["memory"] is True for g in logs)


# ---------------- reproduce never pools memory logs with frozen logs ----------------

def test_memory_reproduce_refuses_mixed_memory_and_frozen_logs(tmp_path):
    a = full_log("A", "fx", 1, [(10.0, 10.0)] * 10)
    b = full_log("B", "fx", 1, [(10.0, 10.0)] * 10)
    b["memory"] = True
    write_logs([a, b], tmp_path / "runs")
    with pytest.raises(ValueError, match="memory"):
        reproduce_tool.reproduce(tmp_path / "runs", tmp_path / "out")
    # memory-only folder is fine (exploratory tables, computed separately)
    write_logs([b], tmp_path / "mem")
    assert reproduce_tool.reproduce(tmp_path / "mem", tmp_path / "out2")["n_games"] == 1
