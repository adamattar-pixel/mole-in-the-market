"""Review M3 (docs/team-artem/REVIEW_ARTEM_DIFF.md), R36: run_all keeps each step's own family settings and
refuses settings that differ between steps whose games are pooled or matched.

Pooled: pilot (A, E) with core (B, B_T, C, D) in the preregistered tables. Matched: core B, C, D with
monitor B_MON, C_MON, D_MON (R32) and ethics B_ETH (R34). A temperature or reasoning difference between
these steps is refused unless allow_settings_mismatch (CLI --allow-settings-mismatch) is given. The frozen
design (n_rounds, spy_start, demand) and the matched seeds are refused without an override.
The smoke step is not pooled, so its settings may differ.
"""
import json

import pytest

from test_R36_run_all import FA, FB, FakeReal, by_config, no_network, run, write_cfgdir  # noqa: F401

NONE = {"effort": "none"}


def fam_reasoning(cfg, label="fa", r=NONE):
    cfg["families"] = [dict(f, reasoning=r) if f["family"] == label else dict(f) for f in cfg["families"]]


def set_temp(t):
    def edit(cfg):
        cfg["temperature"] = t
    return edit


def refused(tmp_path, edit, match, **kw):
    from tools.run_all import RunAllRefused
    c = FakeReal()
    with pytest.raises(RunAllRefused, match=match):
        run(tmp_path, c, cfgdir=write_cfgdir(tmp_path, edit=edit), **kw)
    assert c.calls == 0


def test_M3_core_family_reasoning_not_in_pilot_refused(tmp_path):
    refused(tmp_path, {"espion_core": fam_reasoning}, "reasoning")


def test_M3_core_temperature_not_in_pilot_refused(tmp_path):
    refused(tmp_path, {"espion_core": set_temp(0.7)}, "temperature")


def test_M3_ethics_temperature_differs_from_core_refused(tmp_path):
    refused(tmp_path, {"espion_ethics": set_temp(0.3)}, "temperature")


def test_M3_monitor_family_reasoning_differs_from_core_refused(tmp_path):
    refused(tmp_path, {"espion_monitor": lambda c: fam_reasoning(c, "fb")}, "reasoning")


def test_M3_override_keeps_each_step_own_family_settings(tmp_path):
    def core(cfg):
        fam_reasoning(cfg)
        cfg["temperature"] = 0.7
    def pilot(cfg):
        cfg["temperature"] = None  # pinned in the copy: the repo pilot value is the owner's choice
    res, _ = run(tmp_path, FakeReal(), cfgdir=write_cfgdir(tmp_path, edit={"espion_core": core, "espion_pilot": pilot}),
                 stop_after="core", allow_settings_mismatch=True)
    assert res["status"] == "stopped"
    bc = by_config(tmp_path / "root")
    core_logs = bc["espion_core"]
    assert len(core_logs) == 40
    assert {g["temperature"] for g in core_logs} == {0.7}
    assert all(g.get("reasoning") == (NONE if g["family"] == "fa" else None) for g in core_logs)
    assert {g["temperature"] for g in bc["espion_pilot"]} == {None}
    assert not any("reasoning" in g for g in bc["espion_pilot"])


def test_M3_same_settings_everywhere_runs_and_logs_them(tmp_path):
    def edit(cfg):
        fam_reasoning(cfg)
        cfg["temperature"] = 0.0
    names = ("espion_pilot", "espion_core", "espion_monitor", "espion_ethics")
    res, _ = run(tmp_path, FakeReal(), cfgdir=write_cfgdir(tmp_path, edit={n: edit for n in names}),
                 stop_after="ethics")
    assert res["status"] == "stopped"
    bc = by_config(tmp_path / "root")
    for n in names:
        assert {g["temperature"] for g in bc[n]} == {0.0}, n
        assert {json.dumps(g.get("reasoning")) for g in bc[n] if g["family"] == "fa"} == {json.dumps(NONE)}, n


def test_M3_smoke_settings_may_differ(tmp_path):
    res, _ = run(tmp_path, FakeReal(), cfgdir=write_cfgdir(tmp_path, edit={"espion_smoke": set_temp(1.0)}),
                 stop_after="pilot")
    assert res["status"] == "stopped"


def test_M3_design_mismatch_refused_even_with_override(tmp_path):
    def short(cfg):
        cfg["n_rounds"] = 10
    refused(tmp_path, {"espion_core": short}, "n_rounds", allow_settings_mismatch=True)


def test_M3_monitor_seeds_must_match_core(tmp_path):
    def fewer(cfg):
        cfg["seeds"] = [1, 2, 3]
    refused(tmp_path, {"espion_monitor": fewer}, "seeds", allow_settings_mismatch=True)


def test_M3_cli_override_flag(tmp_path, monkeypatch):
    from tools import run_all
    cfgdir = write_cfgdir(tmp_path, edit={"espion_core": set_temp(0.7)})
    monkeypatch.setattr(run_all, "default_client_factory", lambda dry, gate: (lambda cfg: FakeReal()))
    base = ["--root", str(tmp_path / "root"), "--configs-dir", str(cfgdir), "--n-draws", "20", "--stop-after", "core"]
    assert run_all.main(base) == 1
    assert run_all.main(base + ["--allow-settings-mismatch"]) == 0
