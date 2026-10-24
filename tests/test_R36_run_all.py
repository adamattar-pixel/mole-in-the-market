"""R36: tools/run_all, the one-command pipeline (SPEC.md R36, DECISIONS.md D20).

Order smoke -> pilot (A, E) -> E gate (fallback models once, else plan B) -> core -> monitor -> ethics ->
offline scoring -> [exploratory memory arm + sensitivity, monitor_view, price_paths] -> [O1 last].
Global budget cap, resumable (write-once logs are skipped), refuses unless the addendum and the
preregistration are FROZEN and no model id is `tbd`, --dry mode on the mock client into a scratch folder.

Real-mode tests use a test double client (is_mock False) with sockets blocked: no network, no key.
Expected counts are by hand from the configs:
  smoke A, E x 1 seed x 2 families = 4 | pilot A, E x 5 x 2 = 20 | core B, B_T, C, D x 5 x 2 = 40
  monitor B_MON, C_MON, D_MON x 5 x 2 = 30 | ethics B_ETH x 5 x 2 = 10 | memory A, B, D x 5 x 2 = 30
  O1 B, B_T, C, D x seeds 6-10 x 2 = 40. Every game is 20 rounds x 2 firms = 40 calls.
Test double prices (frozen logit demand: Nash 1.4729, deal = joint monopoly 1.9250): Nash everywhere, except a
"colluding" model in E, which prices at the deal price. E effect (rounds spy_start..20) is then
(deal - Nash) / (monopoly - Nash) = 1.0 >= 0.25 for a colluding model (PASS) and 0.0 for the others (FAIL).
"""
import json
import shutil
import socket
from pathlib import Path

import pytest
import yaml

from harness.conditions import load_prereg_texts
from harness.config import GameConfig
from harness.runlog import load_logs

ROOT = Path(__file__).resolve().parent.parent
CONFIGS = ROOT / "configs"
STEP_CONFIGS = ("espion_smoke", "espion_pilot", "espion_core", "espion_monitor", "espion_ethics")
FA = {"family": "fa", "models": {"0": "fa/m", "1": "fa/m"}}
FB = {"family": "fb", "models": {"0": "fb/m", "1": "fb/m"}}
FX = {"family": "fx", "models": {"0": "fx/m", "1": "fx/m"}}
FY = {"family": "fy", "models": {"0": "fy/m", "1": "fy/m"}}
E_TEXT = load_prereg_texts()["e_instruction"]
GC = GameConfig.from_dict(yaml.safe_load((CONFIGS / "espion_core.yaml").read_text(encoding="utf-8")))
COST = 0.001  # per call -> 0.04 per game


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*a, **k):
        raise AssertionError("network access in a test")
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)


class FakeReal:
    """Test double of the real client (never the thing under test)."""
    is_mock = False

    def __init__(self, colluders=("fa/m", "fb/m", "fx/m", "fy/m")):
        self.colluders = set(colluders)
        self.calls = 0
        self.last_call = None

    def complete(self, messages, model, seed, **settings):
        self.calls += 1
        system, user = messages[0]["content"], messages[-1]["content"]
        price = GC.deal_price if (E_TEXT in system and model in self.colluders) else GC.nash_price
        resp = "accept" if "Message received this round" in user else "no_message"
        return json.dumps({"price": round(price, 6), "response_to_message": resp}), COST


def write_cfgdir(tmp_path, families=(FA, FB), fallback=None, budget=1000.0, edit=None):
    """Copies of the repo step configs with non-placeholder test ids, plus run_all.yaml."""
    d = tmp_path / "configs"
    (d / "exploratory").mkdir(parents=True)
    for name in STEP_CONFIGS + ("exploratory/espion_mem",):
        cfg = yaml.safe_load((CONFIGS / f"{name}.yaml").read_text(encoding="utf-8"))
        cfg["families"] = [dict(f) for f in families]
        if edit and name in edit:
            edit[name](cfg)
        (d / f"{name}.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
    ra = yaml.safe_load((CONFIGS / "run_all.yaml").read_text(encoding="utf-8"))
    ra["budget_usd"] = budget
    ra["fallback"] = {"fa": FX, "fb": FY} if fallback is None else fallback
    (d / "run_all.yaml").write_text(yaml.safe_dump(ra), encoding="utf-8")
    return d


def run(tmp_path, client, cfgdir=None, **kw):
    from tools.run_all import run_pipeline
    names = []

    def factory(cfg):
        names.append(cfg["name"])
        return client

    res = run_pipeline(tmp_path / "root", configs_dir=cfgdir or write_cfgdir(tmp_path),
                       client_factory=factory, n_draws=20, log=lambda *a: None, **kw)
    return res, names


def by_config(root):
    out = {}
    for sub in ("runs", "runs_exploratory/memory"):
        p = Path(root) / sub
        if p.exists():
            for g in load_logs(p):
                out.setdefault(g["game_id"].split("__")[0], []).append(g)
    return out


def counts(root):
    return {k: len(v) for k, v in by_config(root).items()}


# ---------- order and outputs ----------

def test_R36_order_and_game_counts(tmp_path):
    c = FakeReal()
    res, names = run(tmp_path, c)
    assert res["status"] == "done"
    assert res["steps"] == ["smoke", "pilot", "gate", "core", "monitor", "ethics", "scoring"]
    assert names == list(STEP_CONFIGS)
    assert counts(tmp_path / "root") == {"espion_smoke": 4, "espion_pilot": 20, "espion_core": 40,
                                         "espion_monitor": 30, "espion_ethics": 10}
    assert c.calls == 104 * 40
    assert res["gate"]["fallback_used"] is False
    assert res["gate"]["primary"] == {"fa": True, "fb": True}
    assert not (tmp_path / "root" / "runs_exploratory").exists()


def test_R36_scoring_outputs(tmp_path):
    res, _ = run(tmp_path, FakeReal())
    r = tmp_path / "root"
    for n in ("labels.csv", "summary.json", "tables.md", "detectors.json", "detectors.md", "checksums.txt",
              "defenses.json", "defenses.md"):
        assert (r / "results" / n).is_file(), n
    for n in ("games.csv", "rounds.csv", "messages.csv", "meta.json", "data.js"):
        assert (r / "viz" / "data" / n).is_file(), n
    assert (r / "figures" / "game_grid.pdf").is_file()
    s = json.loads((r / "results" / "summary.json").read_text())
    # pilot 20 + core 40; smoke 4, monitor 30, ethics 10 are not preregistered tables
    assert s["n_games"] == 60
    assert s["excluded"]["non_core_config"] == {"espion_ethics": 10, "espion_monitor": 30, "espion_smoke": 4}
    d = json.loads((r / "results" / "defenses.json").read_text())
    pooled = d["all"]
    assert pooled["monitor"]["B"]["n_pairs"] == 10 and pooled["monitor"]["C"]["n_pairs"] == 10
    assert pooled["monitor"]["B"]["blocked"]["k"] == 10  # frozen B text matches the pact rule
    assert pooled["monitor"]["false_blocks"]["k"] == 0 and pooled["monitor"]["false_blocks"]["n"] == 10
    assert pooled["comparison"]["n_matched"] == 10
    assert d["fa"]["comparison"]["n_matched"] == 5 and d["fb"]["comparison"]["n_matched"] == 5
    assert "EXPLORATORY" in (r / "results" / "defenses.md").read_text()


def test_R36_stop_after(tmp_path):
    res, names = run(tmp_path, FakeReal(), stop_after="smoke")
    assert res["status"] == "stopped" and res["steps"] == ["smoke"] and names == ["espion_smoke"]
    assert counts(tmp_path / "root") == {"espion_smoke": 4}


# ---------- resume ----------

def test_R36_resume_skips_finished_games(tmp_path):
    cfgdir = write_cfgdir(tmp_path)
    c1 = FakeReal()
    run(tmp_path, c1, cfgdir=cfgdir, stop_after="pilot")
    assert c1.calls == 24 * 40
    c2 = FakeReal()
    res, _ = run(tmp_path, c2, cfgdir=cfgdir)
    assert res["status"] == "done"
    assert c2.calls == (40 + 30 + 10) * 40  # smoke and pilot games already logged
    c3 = FakeReal()
    res, _ = run(tmp_path, c3, cfgdir=cfgdir)
    assert res["status"] == "done" and c3.calls == 0


def test_R36_resume_partial_step(tmp_path):
    cfgdir = write_cfgdir(tmp_path)
    run(tmp_path, FakeReal(), cfgdir=cfgdir, stop_after="pilot")
    runs = tmp_path / "root" / "runs"
    for p in sorted(runs.glob("espion_pilot__fb__E__*.json"))[:2]:
        p.unlink()  # test folder only: simulate 2 games lost to a crash
    c = FakeReal()
    run(tmp_path, c, cfgdir=cfgdir, stop_after="pilot")
    assert c.calls == 2 * 40


# ---------- budget ----------

def test_R36_global_budget_stop(tmp_path):
    # cap 0.4895: 12 games x 0.04 = 0.48 fit; the 13th game reaches 0.490 > 0.4895 on its 10th call, dropped
    c = FakeReal()
    res, _ = run(tmp_path, c, cfgdir=write_cfgdir(tmp_path, budget=0.4895))
    assert res["status"] == "budget_stop"
    assert counts(tmp_path / "root") == {"espion_smoke": 4, "espion_pilot": 8}
    assert c.calls == 12 * 40 + 10
    assert "core" not in res["steps"] and "scoring" not in res["steps"]


def test_R36_budget_counts_spend_already_in_logs(tmp_path):
    cfgdir = write_cfgdir(tmp_path)
    run(tmp_path, FakeReal(), cfgdir=cfgdir, stop_after="smoke")  # 4 games x 0.04 = 0.16 logged
    ra = yaml.safe_load((cfgdir / "run_all.yaml").read_text())
    ra["budget_usd"] = 0.15
    (cfgdir / "run_all.yaml").write_text(yaml.safe_dump(ra))
    c = FakeReal()
    res, _ = run(tmp_path, c, cfgdir=cfgdir)
    assert res["status"] == "budget_stop" and c.calls == 0
    assert res["spent_usd"] == pytest.approx(0.16)


def test_R36_budget_cli_exit_code(tmp_path, monkeypatch):
    from tools import run_all
    cfgdir = write_cfgdir(tmp_path, budget=0.05)
    monkeypatch.setattr(run_all, "default_client_factory", lambda dry, gate: (lambda cfg: FakeReal()))
    assert run_all.main(["--root", str(tmp_path / "root"), "--configs-dir", str(cfgdir), "--n-draws", "20"]) == 3


# ---------- E gate ----------

def test_R36_gate_fallback_once_then_continue(tmp_path):
    c = FakeReal(colluders=("fa/m", "fy/m"))  # fb fails E, its fallback fy passes
    res, names = run(tmp_path, c)
    assert res["status"] == "done"
    assert res["gate"]["primary"] == {"fa": True, "fb": False}
    assert res["gate"]["fallback_used"] is True and res["gate"]["fallback"] == {"fy": True}
    assert names == ["espion_smoke", "espion_pilot", "espion_pilot_fb", "espion_core", "espion_monitor",
                     "espion_ethics"]
    bc = by_config(tmp_path / "root")
    assert len(bc["espion_pilot_fb"]) == 10 and {g["family"] for g in bc["espion_pilot_fb"]} == {"fy"}
    for name in ("espion_core", "espion_monitor", "espion_ethics"):
        assert {g["family"] for g in bc[name]} == {"fa", "fy"}, name
    s = json.loads((tmp_path / "root" / "results" / "summary.json").read_text())
    # fa pilot 10 + fy pilot_fb 10 + core 40; the 10 fb pilot games are superseded
    assert s["n_games"] == 60 and s["excluded"]["superseded"] == 10
    assert set(s["rates"]) == {"fa", "fy"}


def test_R36_gate_fallback_resume_is_stable(tmp_path):
    cfgdir = write_cfgdir(tmp_path)
    run(tmp_path, FakeReal(colluders=("fa/m", "fy/m")), cfgdir=cfgdir)
    c = FakeReal(colluders=("fa/m", "fy/m"))
    res, _ = run(tmp_path, c, cfgdir=cfgdir)
    assert res["status"] == "done" and res["gate"]["fallback_used"] is True and c.calls == 0


def test_R36_gate_fallback_fails_plan_b(tmp_path, capsys):
    from tools.run_all import run_pipeline
    c = FakeReal(colluders=("fa/m",))  # fb fails, fy fails too
    res = run_pipeline(tmp_path / "root", configs_dir=write_cfgdir(tmp_path), client_factory=lambda cfg: c,
                       n_draws=20)
    assert res["status"] == "plan_b"
    assert res["steps"] == ["smoke", "pilot", "gate"]
    assert set(counts(tmp_path / "root")) == {"espion_smoke", "espion_pilot", "espion_pilot_fb"}
    out = capsys.readouterr().out
    assert "plan B" in out and "1.5" in out


def test_R36_gate_without_fallback_plan_b(tmp_path):
    c = FakeReal(colluders=("fa/m",))
    res, names = run(tmp_path, c, cfgdir=write_cfgdir(tmp_path, fallback={}))
    assert res["status"] == "plan_b" and "espion_pilot_fb" not in names
    assert c.calls == 24 * 40


def test_R36_gate_uses_pilot_not_smoke(tmp_path):
    # fb colludes only in seed 1 (smoke and pilot seed 1). Pilot alone: E mean over 5 seeds,
    # effect = 1/5 of the gap = 0.2 < 0.25 -> FAIL. Pooling smoke would give 2/6 = 0.33 -> PASS (wrong).
    class SeedOne(FakeReal):
        def complete(self, messages, model, seed, **settings):
            if model == "fb/m" and seed != 1:
                self.colluders.discard("fb/m")
                text, cost = super().complete(messages, model, seed, **settings)
                self.colluders.add("fb/m")
                return text, cost
            return super().complete(messages, model, seed, **settings)
    res, _ = run(tmp_path, SeedOne(colluders=("fa/m", "fb/m", "fy/m")))
    assert res["gate"]["primary"] == {"fa": True, "fb": False}


def test_R36_dry_gate_cli_exit_code_plan_b(tmp_path):
    from tools import run_all
    assert run_all.main(["--dry", "--root", str(tmp_path / "s"), "--dry-gate", "fail", "--n-draws", "20"]) == 2


# ---------- guards ----------

def unfrozen_addendum(tmp_path):
    text = (ROOT / "PREREGISTRATION_ADDENDUM.md").read_text(encoding="utf-8")
    p = tmp_path / "ADDENDUM_COPY.md"
    p.write_text(text.replace("FROZEN", "PROPOSED"), encoding="utf-8")
    return p


def test_R36_refuses_unfrozen_addendum(tmp_path):
    from tools.run_all import RunAllRefused
    c = FakeReal()
    with pytest.raises(RunAllRefused, match="ADDENDUM"):
        run(tmp_path, c, addendum_path=unfrozen_addendum(tmp_path))
    assert c.calls == 0 and not (tmp_path / "root" / "runs").exists()


def test_R36_refuses_unfrozen_prereg(tmp_path):
    from tools.run_all import RunAllRefused
    p = tmp_path / "PREREG_COPY.md"
    p.write_text((ROOT / "PREREGISTRATION.md").read_text(encoding="utf-8").replace("FROZEN", "PROPOSED"))
    c = FakeReal()
    with pytest.raises(RunAllRefused, match="PREREGISTRATION"):
        run(tmp_path, c, prereg_path=p)
    assert c.calls == 0


@pytest.mark.parametrize("name", STEP_CONFIGS)
def test_R36_refuses_tbd_ids_in_any_step(tmp_path, name):
    from tools.run_all import RunAllRefused

    def put_tbd(cfg):
        cfg["families"][1] = {"family": "fb", "models": {"0": "fb/model-tbd", "1": "fb/m"}}
    c = FakeReal()
    with pytest.raises(RunAllRefused, match="tbd"):
        run(tmp_path, c, cfgdir=write_cfgdir(tmp_path, edit={name: put_tbd}))
    assert c.calls == 0


def test_R36_refuses_tbd_in_repo_configs(tmp_path):
    from helpers_placeholder import placeholder_copy, placeholder_families
    from tools.run_all import RunAllRefused, run_pipeline
    # copies of the repo configs in their placeholder state: tbd step ids and a tbd fallback
    d = tmp_path / "configs"
    for name in STEP_CONFIGS + ("exploratory/espion_mem",):
        placeholder_copy(CONFIGS / f"{name}.yaml", (d / name).parent)
    ra = yaml.safe_load((CONFIGS / "run_all.yaml").read_text(encoding="utf-8"))
    fb = [{"family": f"family{i}fb-tbd", "models": {"0": f"family{i}fb-tbd/model-tbd", "1": f"family{i}fb-tbd/model-tbd"}}
          for i in (1, 2)]
    ra["fallback"] = {f["family"]: g for f, g in zip(placeholder_families(2), fb)}
    (d / "run_all.yaml").write_text(yaml.safe_dump(ra), encoding="utf-8")
    c = FakeReal()
    with pytest.raises(RunAllRefused, match="tbd"):
        run_pipeline(tmp_path / "root", configs_dir=d, client_factory=lambda cfg: c, log=lambda *a: None)
    assert c.calls == 0


def test_R36_refuses_tbd_memory_config_only_with_exploratory(tmp_path):
    from tools.run_all import RunAllRefused

    def put_tbd(cfg):
        cfg["families"][0] = {"family": "fa", "models": {"0": "fa/tbd", "1": "fa/tbd"}}
    cfgdir = write_cfgdir(tmp_path, edit={"exploratory/espion_mem": put_tbd})
    with pytest.raises(RunAllRefused, match="tbd"):
        run(tmp_path, FakeReal(), cfgdir=cfgdir, exploratory=True)
    res, _ = run(tmp_path, FakeReal(), cfgdir=cfgdir, stop_after="smoke")
    assert res["status"] == "stopped"


def test_R36_refuses_tbd_fallback(tmp_path):
    from tools.run_all import RunAllRefused
    fb = {"fa": {"family": "fx", "models": {"0": "fx/tbd", "1": "fx/tbd"}}}
    with pytest.raises(RunAllRefused, match="tbd"):
        run(tmp_path, FakeReal(), cfgdir=write_cfgdir(tmp_path, fallback=fb))


def test_R36_refuses_fallback_clashing_with_other_family(tmp_path):
    from tools.run_all import RunAllRefused
    with pytest.raises(RunAllRefused, match="fallback"):
        run(tmp_path, FakeReal(), cfgdir=write_cfgdir(tmp_path, fallback={"fa": FB}))


def test_R36_refuses_families_differing_between_steps(tmp_path):
    from tools.run_all import RunAllRefused

    def other(cfg):
        cfg["families"][1] = dict(FY)
    with pytest.raises(RunAllRefused, match="families"):
        run(tmp_path, FakeReal(), cfgdir=write_cfgdir(tmp_path, edit={"espion_monitor": other}))


def test_R36_real_mode_needs_api_key(tmp_path):
    from tools import run_all
    # no factory injected: the real OpenRouter path; key unset -> refused before any call (sockets blocked)
    assert run_all.main(["--root", str(tmp_path / "root"), "--configs-dir", str(write_cfgdir(tmp_path))]) == 1
    assert not (tmp_path / "root" / "runs").exists()


# ---------- exploratory and O1 ----------

def test_R36_exploratory_step(tmp_path):
    c = FakeReal()
    res, names = run(tmp_path, c, exploratory=True)
    r = tmp_path / "root"
    assert res["steps"][-1] == "exploratory" and names[-1] == "espion_mem"
    mem = load_logs(r / "runs_exploratory" / "memory")
    assert len(mem) == 30 and all(g["memory"] is True for g in mem)
    assert not any(g["game_id"].startswith("espion_mem") for g in load_logs(r / "runs"))
    assert c.calls == (104 + 30) * 40
    for p in ("results_exploratory/sensitivity.md", "results_exploratory/monitor/monitor_view.md",
              "results_exploratory/memory/tables.md", "figures/exploratory/price_paths.pdf"):
        assert (r / p).is_file(), p


def test_R36_o1_runs_last(tmp_path):
    res, names = run(tmp_path, FakeReal(), o1=True, exploratory=True)
    assert res["steps"][-2:] == ["exploratory", "o1"] and names[-1] == "espion_o1"
    o1 = by_config(tmp_path / "root")["espion_o1"]
    assert len(o1) == 40 and sorted({g["seed"] for g in o1}) == [6, 7, 8, 9, 10]
    assert sorted({g["condition"] for g in o1}) == ["B", "B_T", "C", "D"]
    assert (tmp_path / "root" / "results_o1" / "tables.md").is_file()
    s = json.loads((tmp_path / "root" / "results" / "summary.json").read_text())
    assert s["n_games"] == 60  # O1 never enters the preregistered tables


# ---------- dry mode ----------

def test_R36_dry_end_to_end_on_repo_configs(tmp_path):
    from tools.run_all import run_pipeline
    runs_before = sorted(p.name for p in (ROOT / "runs").glob("*"))
    res = run_pipeline(tmp_path / "scratch", dry=True, exploratory=True, n_draws=20, log=lambda *a: None)
    assert res["status"] == "done"
    s = tmp_path / "scratch"
    logs = load_logs(s / "runs")
    assert len(logs) == 104 and all(g["mock"] is True for g in logs)
    assert len(load_logs(s / "runs_exploratory" / "memory")) == 30
    for p in ("results/tables.md", "results/detectors.md", "results/defenses.md", "viz/data/games.csv",
              "figures/game_grid.pdf", "results_exploratory/sensitivity.md", "figures/exploratory/price_paths.pdf"):
        assert (s / p).is_file(), p
    assert json.loads((s / "results" / "summary.json").read_text())["n_games"] == 60
    assert sorted(p.name for p in (ROOT / "runs").glob("*")) == runs_before


def test_R36_dry_refuses_repo_root(tmp_path):
    from tools.run_all import RunAllRefused, run_pipeline
    with pytest.raises(RunAllRefused):
        run_pipeline(ROOT, dry=True, log=lambda *a: None)


def test_R36_dry_cli(tmp_path):
    from tools import run_all
    assert run_all.main(["--dry", "--root", str(tmp_path / "s"), "--n-draws", "20"]) == 0
    assert (tmp_path / "s" / "results" / "tables.md").is_file()


# ---------- smoke report ----------

def test_R36_smoke_report_hand_values():
    from tools.run_all import smoke_report

    def g(fam, cost, inv_p, inv_r, served, provider, rtok):
        firm = {"provenance": {"served_model": served, "provider": provider, "reasoning_tokens": rtok}}
        return {"game_id": f"espion_smoke__{fam}__A__s1", "family": fam, "cost_usd": cost, "n_rounds": 20,
                "invalid_prices": inv_p, "invalid_responses": inv_r, "reasoning_tokens": rtok,
                "rounds": [{"round": 1, "firms": {"0": firm, "1": firm}}]}
    rep = smoke_report([g("fa", 0.1, 2, 0, "fa/m-1", "P1", 0), g("fa", 0.3, 0, 4, "fa/m-1", "P2", 0),
                        g("fb", 0.05, 0, 0, None, None, None)])
    assert rep["fa"]["games"] == 2
    assert rep["fa"]["mean_cost_usd"] == pytest.approx(0.2)
    # 2 games x 20 rounds x 2 firms = 80 replies: invalid prices 2/80, invalid responses 4/80
    assert rep["fa"]["invalid_price_rate"] == pytest.approx(2 / 80)
    assert rep["fa"]["invalid_response_rate"] == pytest.approx(4 / 80)
    assert rep["fa"]["served_models"] == ["fa/m-1"] and rep["fa"]["providers"] == ["P1", "P2"]
    assert rep["fa"]["reasoning_tokens"] == 0
    assert rep["fb"]["reasoning_tokens"] is None and rep["fb"]["providers"] == []
