"""Phase 4 without real API calls: configs (R16), dry runs with the mock client (R12), budget cap (R17),
cost per game (R17), E validation on dry logs (R13), real-run refusal while models are placeholders (H2).

Frozen design values (PREREGISTRATION.md, Design, frozen at d5e7ebc): 20 rounds, spy_start 8, logit demand
a = 2, a0 = 0, mu = 0.25, c = 1, beta = 100, alpha = 1; 5 seeds; 2 model families; core 6 x 5 x 2 = 60 games.
"""
import json
import socket
from pathlib import Path

import pytest
import yaml

from harness.clients import BudgetExceeded
from harness.costs import cost_summary
from harness.dryclient import make_dry_client
from harness.runner import RealRunRefused, expand_games, run_batch, validate_config
from helpers3 import full_log
from tools import run as run_tool
from tools import validate_e

ROOT = Path(__file__).resolve().parent.parent
CONFIGS = ROOT / "configs"
FROZEN_DEMAND = {"type": "logit", "a": 2.0, "a0": 0.0, "mu": 0.25, "c": 1.0, "beta": 100.0, "alpha": 1.0}


def load(name):
    return yaml.safe_load((CONFIGS / f"{name}.yaml").read_text(encoding="utf-8"))


ALL = ["espion_dry", "espion_smoke", "espion_pilot", "espion_core"]
REAL = ["espion_smoke", "espion_pilot", "espion_core"]


def block_network(monkeypatch):
    def no_net(*a, **k):
        raise AssertionError("network used")

    monkeypatch.setattr(socket, "socket", no_net)
    monkeypatch.setattr(socket, "create_connection", no_net)


# ---------------- R16 configs ----------------

@pytest.mark.parametrize("name", ALL)
def test_R16_P4_config_valid_and_matches_frozen_design(name):
    cfg = load(name)
    validate_config(cfg)
    assert cfg["name"] == name
    assert cfg["n_rounds"] == 20 and cfg["spy_start"] == 8
    assert {k: float(v) if k != "type" else v for k, v in cfg["demand"].items()} == FROZEN_DEMAND
    assert len(cfg["families"]) == 2
    assert len({f["family"] for f in cfg["families"]}) == 2
    assert float(cfg["budget_usd"]) > 0


@pytest.mark.parametrize("name", REAL)
def test_R16_P4_real_configs_are_not_mock_and_write_to_runs(name):
    cfg = load(name)
    assert cfg["mock"] is False
    assert cfg["out_dir"] == "runs"


def test_R16_P4_dry_config_is_mock_and_never_writes_to_runs():
    cfg = load("espion_dry")
    assert cfg["mock"] is True
    assert cfg["out_dir"] != "runs" and not cfg["out_dir"].startswith("runs/")
    assert set(cfg["conditions"]) == {"A", "E", "B", "B_T", "C", "D"}


def test_R16_P4_smoke_and_pilot_are_A_and_E_only():
    # v7 section 10 step 1: smoke then pilot on A and E only.
    assert set(load("espion_smoke")["conditions"]) == {"A", "E"}
    pilot = load("espion_pilot")
    assert set(pilot["conditions"]) == {"A", "E"} and pilot["seeds"] == [1, 2, 3, 4, 5]


def test_R16_P4_core_plus_pilot_is_the_60_game_design():
    # core = B, B_T, C, D x 5 seeds x 2 families = 40 ; pilot = A, E x 5 x 2 = 20 ; total 60 = 6 x 5 x 2
    core, pilot = load("espion_core"), load("espion_pilot")
    assert set(core["conditions"]) == {"B", "B_T", "C", "D"} and core["seeds"] == [1, 2, 3, 4, 5]
    assert len(expand_games(core)) == 40 and len(expand_games(pilot)) == 20
    assert core["families"] == pilot["families"]
    ids = {g.game_id.split("__", 1)[1] for g in expand_games(core) + expand_games(pilot)}
    assert len(ids) == 60


def test_R16_P4_smoke_size():
    # A, E x 1 seed x 2 families = 4 games
    assert len(expand_games(load("espion_smoke"))) == 4


def test_R16_P4_config_rejects_mock_writing_to_runs_and_real_writing_elsewhere():
    dry = load("espion_dry")
    dry["out_dir"] = "runs"
    with pytest.raises(ValueError):
        validate_config(dry)
    real = load("espion_smoke")
    real["out_dir"] = "elsewhere"
    with pytest.raises(ValueError):
        validate_config(real)


# ---------------- H2: no real call while models are placeholders ----------------

@pytest.mark.parametrize("name", REAL)
def test_H2_P4_real_config_refused_while_models_are_placeholders(name, tmp_path, monkeypatch):
    block_network(monkeypatch)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(RealRunRefused):
        run_tool.main([str(CONFIGS / f"{name}.yaml"), "--out-dir", str(tmp_path / "runs")])
    assert not (tmp_path / "runs").exists() or list((tmp_path / "runs").iterdir()) == []


# ---------------- R12 dry runs ----------------

def test_R12_P4_dry_client_is_deterministic_and_well_formed():
    cfg = load("espion_dry")
    c1, c2 = make_dry_client(cfg), make_dry_client(cfg)
    assert c1.is_mock is True
    msgs = [{"role": "system", "content": "s"}, {"role": "user", "content": 'Round 8 of 20.\nMessage received this round: "x"'}]
    t1, cost1 = c1.complete(msgs, "mockA/m", 3)
    t2, cost2 = c2.complete(msgs, "mockA/m", 3)
    assert (t1, cost1) == (t2, cost2)
    reply = json.loads(t1)
    assert reply["price"] > 0 and reply["response_to_message"] in ("accept", "decline")
    no_msg = [{"role": "system", "content": "s"}, {"role": "user", "content": "Round 2 of 20.\nNo message this round."}]
    assert json.loads(c1.complete(no_msg, "mockA/m", 3)[0])["response_to_message"] == "no_message"
    # mock cost per call comes from the config
    assert cost1 == pytest.approx(float(cfg["mock_cost_per_call"]))


def test_R12_P4_dry_run_writes_complete_mock_logs(tmp_path, monkeypatch):
    block_network(monkeypatch)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    cfg = load("espion_dry")
    out = tmp_path / "dry"
    assert run_tool.main([str(CONFIGS / "espion_dry.yaml"), "--out-dir", str(out)]) == 0
    logs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(out.glob("*.json"))]
    # 6 conditions x len(seeds) x 2 families
    assert len(logs) == 6 * len(cfg["seeds"]) * 2
    for g in logs:
        assert g["mock"] is True and len(g["rounds"]) == 20 and g["spy_start"] == 8
        assert g["git_commit"] and g["config_hash"] and g["models"]


def test_R12_P4_dry_run_twice_identical_prices(tmp_path, monkeypatch):
    block_network(monkeypatch)
    run_tool.main([str(CONFIGS / "espion_dry.yaml"), "--out-dir", str(tmp_path / "a")])
    run_tool.main([str(CONFIGS / "espion_dry.yaml"), "--out-dir", str(tmp_path / "b")])
    def prices(d):
        return {p.name: [[r["firms"][f]["price"] for f in ("0", "1")] for r in json.loads(p.read_text(encoding="utf-8"))["rounds"]]
                for p in sorted(d.glob("*.json"))}
    assert prices(tmp_path / "a") == prices(tmp_path / "b")


# ---------------- R17 budget cap and cost per game ----------------

def test_R17_P4_dry_run_budget_cap_stops(tmp_path, monkeypatch):
    # mock cost per call x 2 firms x 20 rounds = cost per game. A cap of 1.5 games stops inside game 2.
    block_network(monkeypatch)
    cfg = load("espion_dry")
    per_game = float(cfg["mock_cost_per_call"]) * 2 * 20
    cfg["budget_usd"] = 1.5 * per_game
    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    with pytest.raises(BudgetExceeded):
        run_tool.main([str(p), "--out-dir", str(tmp_path / "dry")])
    assert len(list((tmp_path / "dry").glob("*.json"))) == 1


def test_R17_P4_cost_summary_hand_values():
    # family fx: games cost 0.5 and 1.5 -> total 2.0, mean 1.0 ; family fy: one game 0.25
    a = full_log("A", "fx", 1, [(10.0, 10.0)] * 10)
    b = full_log("E", "fx", 1, [(10.0, 10.0)] * 10)
    c = full_log("A", "fy", 1, [(10.0, 10.0)] * 10)
    a["cost_usd"], b["cost_usd"], c["cost_usd"] = 0.5, 1.5, 0.25
    s = cost_summary([a, b, c])
    assert s["fx"] == {"games": 2, "total_usd": pytest.approx(2.0), "mean_per_game_usd": pytest.approx(1.0)}
    assert s["fy"] == {"games": 1, "total_usd": pytest.approx(0.25), "mean_per_game_usd": pytest.approx(0.25)}
    assert s["all"]["games"] == 3 and s["all"]["mean_per_game_usd"] == pytest.approx(2.25 / 3)
    assert cost_summary([]) == {"all": {"games": 0, "total_usd": 0.0, "mean_per_game_usd": None}}


def test_R17_P4_dry_run_cost_per_game_measured(tmp_path, monkeypatch):
    block_network(monkeypatch)
    cfg = load("espion_dry")
    run_tool.main([str(CONFIGS / "espion_dry.yaml"), "--out-dir", str(tmp_path / "dry")])
    logs = [json.loads(p.read_text(encoding="utf-8")) for p in (tmp_path / "dry").glob("*.json")]
    # every call costs mock_cost_per_call, 40 calls per game
    expected = float(cfg["mock_cost_per_call"]) * 40
    assert cost_summary(logs)["all"]["mean_per_game_usd"] == pytest.approx(expected)


# ---------------- R13 on dry logs ----------------

def test_R13_P4_validate_e_reports_each_dry_family(tmp_path, monkeypatch, capsys):
    block_network(monkeypatch)
    cfg = load("espion_dry")
    run_tool.main([str(CONFIGS / "espion_dry.yaml"), "--out-dir", str(tmp_path / "dry")])
    capsys.readouterr()
    validate_e.main([str(tmp_path / "dry")])
    out = capsys.readouterr().out
    for fam in cfg["families"]:
        assert f"{fam['family']}: " in out
