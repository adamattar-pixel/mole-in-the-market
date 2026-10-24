"""Integration R28 x R31: detector D2 must see the message the firms actually received.

A blocked monitored game (B_MON) has the spy text in log["monitor"]["spy_message"] only; the firms got no
message. D2 reads log["received_message"] if present, else log["message"]. These tests run the real runner
on the dry monitor config with a test double that ALWAYS answers accept, so D2 would fire on any game whose
log exposes the pact text through the field D2 reads. Expected flags are by hand: the frozen B text matches
the pact rule (it says "we both set our price"), so D2 fires on B and on no blocked B_MON game.
"""
import json
from pathlib import Path

import yaml

from harness.clients import MockClient
from harness.detectors import d2_message, received_message
from harness.runner import run_batch
from harness.runlog import load_logs
from tools.score_detectors import score_detectors

ROOT = Path(__file__).resolve().parent.parent


def load_cfg(rel):
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))


def always_accept(messages, model, seed):
    return json.dumps({"price": 1.5, "response_to_message": "accept"})


def run(rel, out, conditions=None):
    cfg = load_cfg(rel)
    if conditions is not None:
        cfg["conditions"] = conditions
    run_batch(cfg, MockClient(always_accept), out, git_commit="test")


def test_blocked_B_MON_log_does_not_expose_pact_text_to_D2(tmp_path):
    run("configs/espion_monitor_dry.yaml", tmp_path, ["B_MON"])
    logs = load_logs(tmp_path)
    assert len(logs) == 4  # 1 condition x 2 seeds x 2 families
    for g in logs:
        assert g["monitor"]["blocked"] is True
        assert g["monitor"]["spy_message"]  # the spy text is kept, but only under "monitor"
        assert received_message(g) is None
        assert d2_message(g) is False


def test_D2_fires_on_B_but_not_on_matched_blocked_B_MON_with_always_accept(tmp_path):
    run("configs/espion_dry.yaml", tmp_path, ["B"])
    run("configs/espion_monitor_dry.yaml", tmp_path, ["B_MON", "C_MON", "D_MON"])
    by_cond = {}
    for g in load_logs(tmp_path):
        by_cond.setdefault(g["condition"], []).append(d2_message(g))
    # Hand: B text matches the rule and every firm accepts -> 4/4. B_MON blocked -> 0/4.
    # C (hint) and D (harmless) texts do not match the rule -> 0/4 each, even with accept.
    assert by_cond == {"B": [True] * 4, "B_MON": [False] * 4, "C_MON": [False] * 4, "D_MON": [False] * 4}


def test_score_detectors_ignores_monitored_games(tmp_path):
    run("configs/espion_dry.yaml", tmp_path, ["B"])
    run("configs/espion_monitor_dry.yaml", tmp_path, ["B_MON"])
    s = score_detectors(load_logs(tmp_path), n_draws=10)
    assert s["n_core_games"] == 4 and s["n_excluded_non_core"] == 4
