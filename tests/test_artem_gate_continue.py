"""tools/run_all --continue-passing-families (owner request 2026-10-24) and run_all --workers.

Default (flag off) is the frozen behaviour: a family whose fallback also fails E (or that has no fallback)
stops the pipeline with plan B (tests/test_R36_run_all.py). With the flag, the later steps run with only the
families that passed the gate. It is a DECLARED DEVIATION (2 families -> 1, ops/QUESTIONS.md): a loud
DEVIATION line is printed, res["deviations"] holds the record and root/run_all_deviations.json is written.
The dropped families' pilot games (and their failed fallback pilot) are kept in runs/ (write-once) and are
excluded from the preregistered tables, counted as "superseded" like a replaced family's pilot.
Hand counts (configs as in test_R36): one family left = core 4 conditions x 5 seeds = 20, monitor 3 x 5 = 15,
ethics 5; pilot 20 (both families) and the fallback pilot 10 run before the gate decision.
"""
import json
import socket
import threading

import pytest

from test_R36_run_all import COST, FakeReal, by_config, counts, run, write_cfgdir


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*a, **k):
        raise AssertionError("network access in a test")
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)


def run_logged(tmp_path, client, **kw):
    from tools.run_all import run_pipeline
    lines = []
    res = run_pipeline(tmp_path / "root", configs_dir=kw.pop("cfgdir", None) or write_cfgdir(tmp_path),
                       client_factory=lambda cfg: client, n_draws=20, log=lines.append, **kw)
    return res, "\n".join(str(x) for x in lines)


# ---------- default stays the frozen behaviour ----------

def test_flag_off_fallback_fails_is_still_plan_b(tmp_path):
    res, out = run_logged(tmp_path, FakeReal(colluders=("fa/m",)))
    assert res["status"] == "plan_b" and res["steps"] == ["smoke", "pilot", "gate"]
    assert res.get("deviations", []) == []
    assert "DEVIATION" not in out
    assert not (tmp_path / "root" / "run_all_deviations.json").exists()


def test_flag_on_with_all_passing_changes_nothing(tmp_path):
    res, out = run_logged(tmp_path, FakeReal(), continue_passing_families=True)
    assert res["status"] == "done" and res["deviations"] == []
    assert "DEVIATION" not in out
    assert counts(tmp_path / "root")["espion_core"] == 40
    assert not (tmp_path / "root" / "run_all_deviations.json").exists()


# ---------- flag on: continue with the passing families ----------

def test_flag_on_fallback_fails_continues_with_passing_family(tmp_path):
    c = FakeReal(colluders=("fa/m",))  # fb fails E, its fallback fy fails too
    res, out = run_logged(tmp_path, c, continue_passing_families=True)
    assert res["status"] == "done"
    assert res["steps"] == ["smoke", "pilot", "gate", "core", "monitor", "ethics", "scoring"]
    assert res["gate"]["primary"] == {"fa": True, "fb": False} and res["gate"]["fallback"] == {"fy": False}
    root = tmp_path / "root"
    assert counts(root) == {"espion_smoke": 4, "espion_pilot": 20, "espion_pilot_fb": 10, "espion_core": 20,
                            "espion_monitor": 15, "espion_ethics": 5}
    bc = by_config(root)
    for name in ("espion_core", "espion_monitor", "espion_ethics"):
        assert {g["family"] for g in bc[name]} == {"fa"}, name
    assert c.calls == (4 + 20 + 10 + 20 + 15 + 5) * 40
    [dev] = res["deviations"]
    assert dev["flag"] == "--continue-passing-families"
    assert dev["dropped_families"] == ["fb"] and dev["kept_families"] == ["fa"]
    assert dev["n_families_planned"] == 2 and dev["n_families_kept"] == 1
    assert dev["failed_fallbacks"] == ["fy"]
    excl = sorted(g["game_id"] for g in bc["espion_pilot"] if g["family"] == "fb") + \
        sorted(g["game_id"] for g in bc["espion_pilot_fb"])
    assert dev["excluded_game_ids"] == sorted(excl) and len(excl) == 20
    assert "QUESTIONS" in dev["note"]
    lines = [x for x in out.splitlines() if "DEVIATION" in x]
    assert lines and "fb" in lines[0] and "2 -> 1" in "\n".join(lines)
    assert json.loads((root / "run_all_deviations.json").read_text()) == res["deviations"]
    s = json.loads((root / "results" / "summary.json").read_text())
    # fa pilot 10 + core 20 in the tables; fb pilot 10 and fy fallback pilot 10 excluded as superseded
    assert s["n_games"] == 30 and s["excluded"]["superseded"] == 20
    assert set(s["rates"]) == {"fa"}


def test_flag_on_without_fallback_continues(tmp_path):
    c = FakeReal(colluders=("fa/m",))
    res, out = run_logged(tmp_path, c, cfgdir=write_cfgdir(tmp_path, fallback={}), continue_passing_families=True)
    assert res["status"] == "done"
    assert "espion_pilot_fb" not in counts(tmp_path / "root")
    assert counts(tmp_path / "root")["espion_core"] == 20
    [dev] = res["deviations"]
    assert dev["dropped_families"] == ["fb"] and dev["failed_fallbacks"] == []
    assert len(dev["excluded_game_ids"]) == 10
    assert "DEVIATION" in out


def test_flag_on_one_fallback_passes_one_family_dropped(tmp_path):
    # fa fails, its fallback fx passes; fb fails, its fallback fy fails -> keep fx only
    c = FakeReal(colluders=("fx/m",))
    res, _ = run_logged(tmp_path, c, continue_passing_families=True)
    assert res["status"] == "done"
    assert res["gate"]["fallback"] == {"fx": True, "fy": False}
    bc = by_config(tmp_path / "root")
    assert {g["family"] for g in bc["espion_core"]} == {"fx"} and len(bc["espion_core"]) == 20
    [dev] = res["deviations"]
    assert dev["dropped_families"] == ["fb"] and dev["kept_families"] == ["fx"]
    s = json.loads((tmp_path / "root" / "results" / "summary.json").read_text())
    # fx fallback pilot 10 + core 20; all 20 primary pilot games and the fy pilot 10 excluded
    assert s["n_games"] == 30 and s["excluded"]["superseded"] == 30


def test_flag_on_every_family_fails_is_plan_b(tmp_path):
    res, out = run_logged(tmp_path, FakeReal(colluders=()), continue_passing_families=True)
    assert res["status"] == "plan_b" and "core" not in res["steps"]
    assert "plan B" in out


def test_flag_on_resume_is_stable(tmp_path):
    cfgdir = write_cfgdir(tmp_path)
    r1, _ = run_logged(tmp_path, FakeReal(colluders=("fa/m",)), cfgdir=cfgdir, continue_passing_families=True)
    c = FakeReal(colluders=("fa/m",))
    r2, out = run_logged(tmp_path, c, cfgdir=cfgdir, continue_passing_families=True)
    assert r2["status"] == "done" and c.calls == 0
    assert r2["deviations"] == r1["deviations"] and "DEVIATION" in out


def test_flag_on_cli(tmp_path):
    from tools import run_all
    # dry gate fail: every family and fallback fails, so even with the flag it is plan B (exit 2)
    assert run_all.main(["--dry", "--root", str(tmp_path / "s"), "--dry-gate", "fail", "--n-draws", "20",
                         "--continue-passing-families"]) == 2


# ---------- run_all --workers ----------

class SafeFake(FakeReal):
    """FakeReal with a thread-safe call counter (shared by forked copies)."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.lock = threading.Lock()
        self.box = [0]

    def complete(self, messages, model, seed, **settings):
        with self.lock:
            self.box[0] += 1
        return super().complete(messages, model, seed, **settings)


def tree(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()
            and p.suffix in (".json", ".md", ".csv", ".txt", ".js")}


def test_run_all_workers_same_outputs(tmp_path):
    from tools.run_all import run_pipeline
    cfgdir = write_cfgdir(tmp_path)
    outs = {}
    for w in (1, 4):
        lines = []
        res = run_pipeline(tmp_path / f"r{w}", configs_dir=cfgdir, client_factory=lambda cfg: SafeFake(),
                           n_draws=20, log=lines.append, workers=w)
        assert res["status"] == "done"
        outs[w] = (res, tree(tmp_path / f"r{w}"), [x.replace(f"r{w}", "rX") for x in lines])
    (r1, t1, l1), (r4, t4, l4) = outs[1], outs[4]
    assert t1 == t4 and len(t1) > 100
    assert r1["steps"] == r4["steps"] and r1["spent_usd"] == pytest.approx(r4["spent_usd"])
    assert r1["spent_usd"] == pytest.approx(104 * 40 * COST)
    assert [x for x in l1 if "workers" not in x] == [x for x in l4 if "workers" not in x]


def test_run_all_workers_global_cap_bounded(tmp_path):
    # global cap 0.4895: sequential stops at 12 games + 10 calls (test_R36); with 4 workers at most 3 more calls
    c = SafeFake()
    res, _ = run_logged(tmp_path, c, cfgdir=write_cfgdir(tmp_path, budget=0.4895), workers=4)
    assert res["status"] == "budget_stop"
    spent = c.box[0] * COST
    assert 0.4895 < spent <= 0.4895 + 4 * COST + 1e-12
    logged = sum(len(v) for v in counts(tmp_path / "root").values())
    assert logged * 40 * COST <= 0.4895


def test_run_all_failed_games_reported(tmp_path, monkeypatch):
    from tools import run_all

    class Bad(SafeFake):
        def complete(self, messages, model, seed, **settings):
            if seed == 2 and model == "fb/m":
                raise RuntimeError("provider down")
            return super().complete(messages, model, seed, **settings)

    res, out = run_logged(tmp_path, Bad(), workers=3, stop_after="pilot")
    assert res["status"] == "game_failures"
    # smoke is seed 1 only; the pilot (seeds 1-5) has the two fb seed-2 games, sorted by game id
    assert res["failed"] == ["espion_pilot__fb__A__s2", "espion_pilot__fb__E__s2"]
    assert res["steps"] == ["smoke"]
    assert counts(tmp_path / "root") == {"espion_smoke": 4, "espion_pilot": 18}
    assert "FAILED" in out and "espion_pilot__fb__A__s2" in out
    assert run_all.EXIT["game_failures"] == 4


def test_run_all_cli_workers(tmp_path):
    from tools import run_all
    assert run_all.main(["--dry", "--root", str(tmp_path / "s"), "--n-draws", "20", "--workers", "4",
                         "--stop-after", "pilot"]) == 0
