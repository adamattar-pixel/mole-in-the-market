"""Review M2 (docs/team-artem/REVIEW_ARTEM_DIFF.md), R12: resume must not mix games run with other settings.

A partial run (2 of 3 games logged, then a budget stop) is resumed with an edited config. The resume is
refused, before any call, when a logged game of the same config differs in config_hash, models,
temperature or reasoning; the error names the field. Raising only budget_usd (the documented way to go
on after a cap stop) still resumes.
Hand values: helpers3.cfg has 4 rounds x 2 firms = 8 calls per game; 0.25 USD per call = 2.0 USD per game,
so cap 5.0 with seeds 1, 2, 3 logs games 1 and 2 and drops game 3.
"""
import json

import pytest

from harness.clients import BudgetExceeded, MockClient
from harness.runlog import load_logs
from harness.runner import RealRunRefused, run_batch
from helpers3 import cfg
from test_review_M1_budget_resume import TEXTS


def client():
    calls = []

    def fn(messages, model, seed):
        calls.append(model)
        return json.dumps({"price": 5.0, "response_to_message": "accept"})

    return MockClient(fn, cost_per_call=0.25), calls


def partial(tmp_path, **over):
    c = cfg(seeds=[1, 2, 3], budget_usd=5.0, **over)
    with pytest.raises(BudgetExceeded):
        run_batch(c, client()[0], tmp_path, texts=TEXTS)
    assert len(load_logs(tmp_path)) == 2
    return c


def refused(tmp_path, c, field):
    m, calls = client()
    with pytest.raises(RealRunRefused, match=field):
        run_batch(c, m, tmp_path, texts=TEXTS)
    assert calls == [] and len(load_logs(tmp_path)) == 2


def test_M2_temperature_change_refused(tmp_path):
    c = partial(tmp_path, temperature=0.0)
    refused(tmp_path, dict(c, temperature=1.0, budget_usd=100.0), "temperature")


def test_M2_models_change_refused(tmp_path):
    c = partial(tmp_path)
    fams = [{"family": "fam", "models": {"0": "fam/m2", "1": "fam/m2"}}]
    refused(tmp_path, dict(c, families=fams, budget_usd=100.0), "models")


def test_M2_family_reasoning_change_refused(tmp_path):
    c = partial(tmp_path)
    fams = [{"family": "fam", "models": {"0": "fam/m1", "1": "fam/m1"}, "reasoning": {"effort": "none"}}]
    refused(tmp_path, dict(c, families=fams, budget_usd=100.0), "reasoning")


def test_M2_top_level_reasoning_change_refused(tmp_path):
    c = partial(tmp_path, reasoning={"effort": "low"})
    refused(tmp_path, dict(c, reasoning={"effort": "high"}, budget_usd=100.0), "reasoning")


def test_M2_family_dropped_from_config_refused(tmp_path):
    c = partial(tmp_path)
    fams = [{"family": "other", "models": {"0": "other/m", "1": "other/m"}}]
    refused(tmp_path, dict(c, families=fams, budget_usd=100.0), "family")


def test_M2_any_other_config_change_refused_by_config_hash(tmp_path):
    c = partial(tmp_path)
    refused(tmp_path, dict(c, spy_start=3, budget_usd=100.0), "config_hash")


def test_M2_raising_only_the_cap_resumes(tmp_path):
    c = partial(tmp_path)
    m, calls = client()
    new = run_batch(dict(c, budget_usd=100.0), m, tmp_path, texts=TEXTS)
    assert [g["seed"] for g in new] == [3] and len(calls) == 8
    assert len(load_logs(tmp_path)) == 3


def test_M2_unchanged_rerun_is_fine(tmp_path):
    c = cfg(seeds=[1, 2])
    run_batch(c, client()[0], tmp_path, texts=TEXTS)
    m, calls = client()
    assert run_batch(c, m, tmp_path, texts=TEXTS) == [] and calls == []
