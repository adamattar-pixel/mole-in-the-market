"""Review M1 (docs/team-artem/REVIEW_ARTEM_DIFF.md), R17: a rerun must not reset the per-config budget cap.

The spend counter of a config starts from the spend already logged for that config (game ids
"<config name>__..."), so the cap bounds the total spend of the config across reruns.
Hand values: helpers3.cfg has 4 rounds x 2 firms = 8 calls per game; at 0.25 USD per call a game costs 2.0 USD.
"""
import json

import pytest

from harness.clients import BudgetExceeded, MockClient
from harness.runlog import load_logs
from harness.runner import run_batch
from helpers3 import cfg, full_log, write_logs

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


def client():
    calls = []

    def fn(messages, model, seed):
        calls.append(model)
        return json.dumps({"price": 5.0, "response_to_message": "accept"})

    return MockClient(fn, cost_per_call=0.25), calls


def test_M1_rerun_keeps_the_cap(tmp_path):
    # Cap 5.0, 4 seeds. Run 1: games 1, 2 logged (4.0), game 3 dropped on its 5th call (5.25 > 5.0).
    c = cfg(seeds=[1, 2, 3, 4], budget_usd=5.0)
    m, calls = client()
    with pytest.raises(BudgetExceeded):
        run_batch(c, m, tmp_path, texts=TEXTS)
    assert len(load_logs(tmp_path)) == 2 and len(calls) == 21
    # Run 2, same config: the counter starts at the logged 4.0, so game 3 stops again after 4 calls
    # (4.25, 4.5, 4.75, 5.0 allowed, 5.25 > cap on the 5th call). No new log, logged spend stays 4.0.
    m, calls = client()
    with pytest.raises(BudgetExceeded):
        run_batch(c, m, tmp_path, texts=TEXTS)
    assert len(calls) == 5
    logs = load_logs(tmp_path)
    assert len(logs) == 2
    assert sum(g["cost_usd"] for g in logs) == pytest.approx(4.0)


def test_M1_refuses_to_start_when_logged_spend_reaches_the_cap(tmp_path):
    # Cap 4.0: run 1 logs games 1 and 2 (4.0 = cap, allowed) and stops in game 3.
    c = cfg(seeds=[1, 2, 3], budget_usd=4.0)
    with pytest.raises(BudgetExceeded):
        run_batch(c, client()[0], tmp_path, texts=TEXTS)
    m, calls = client()
    with pytest.raises(BudgetExceeded):
        run_batch(c, m, tmp_path, texts=TEXTS)
    assert calls == []  # refused before any call


def test_M1_finished_config_at_the_cap_is_not_an_error(tmp_path):
    # 2 games x 2.0 = 4.0 = cap: every game is done, a rerun has nothing to run and must not raise.
    c = cfg(seeds=[1, 2], budget_usd=4.0)
    run_batch(c, client()[0], tmp_path, texts=TEXTS)
    m, calls = client()
    assert run_batch(c, m, tmp_path, texts=TEXTS) == [] and calls == []


def test_M1_spend_of_other_configs_does_not_count(tmp_path):
    # 3 USD logged by another config in the same folder: the cap of config "t" (2.5) is its own.
    other = full_log("A", "fam", 1, [(4.0, 4.0)] * 4, spy_start=2, nash=4.0, mono=5.5)
    other.update(game_id="other__fam__A__s1", cost_usd=3.0)
    write_logs([other], tmp_path)
    m, calls = client()
    run_batch(cfg(seeds=[1], budget_usd=2.5), m, tmp_path, texts=TEXTS)
    assert len(calls) == 8
