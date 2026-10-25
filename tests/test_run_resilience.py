"""One game's error must not drop the others, HTTP errors must show the server text, a log that
appears mid-batch is kept, and paid calls that never became a log still count toward the cap.

Hand values: helpers3.cfg has 4 rounds x 2 firms = 8 calls per game.
"""
import io
import json
import urllib.error

import pytest

from harness import clients
from harness.clients import BudgetExceeded, MockClient, OpenRouterClient
from harness.concurrency import RetryingClient
from harness.runlog import LEDGER_NAME, load_logs, spend_already
from harness.runner import BatchFailed, expand_games, run_batch
from helpers3 import cfg, full_log, write_logs
from tools.reproduce import reproduce

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
REPLY = json.dumps({"price": 5.0, "response_to_message": "decline"})


class _Boom:
    """Mock client. complete raises RuntimeError when the seed is in fail_seeds."""

    is_mock = True

    def __init__(self, fail_seeds):
        self.fail_seeds = set(fail_seeds)
        self.calls = []

    def complete(self, messages, model, seed, **settings):
        self.calls.append(seed)
        if seed in self.fail_seeds:
            raise RuntimeError(f"boom in seed {seed}")
        return REPLY, 0.0


def test_sequential_failure_keeps_the_other_games(tmp_path):
    # Seeds 1, 2, 3. Seed 2 raises on its first call. Seeds 1 and 3 are 8 calls each and stay on disk.
    c = cfg(seeds=[1, 2, 3])
    client = _Boom({2})
    with pytest.raises(BatchFailed) as ei:
        run_batch(c, client, tmp_path, texts=TEXTS)
    failed = [s.game_id for s in expand_games(c) if s.seed == 2]
    assert list(ei.value.failed) == failed
    assert "boom in seed 2" in ei.value.failed[failed[0]]
    logged = sorted(p.stem for p in tmp_path.glob("*.json"))
    assert logged == [s.game_id for s in expand_games(c) if s.seed != 2]
    assert sorted(g["game_id"] for g in ei.value.done) == logged
    # The failed game is retried; the two finished games are not called again.
    again = _Boom(set())
    run_batch(c, again, tmp_path, texts=TEXTS)
    assert again.calls == [2] * 8


def test_http_error_includes_the_body_and_hides_the_key(monkeypatch):
    key = "sk-or-v1-SECRET"
    monkeypatch.setenv("OPENROUTER_API_KEY", key)
    body = json.dumps({"error": {"message": "This model is not available in your region. " + key}}).encode()

    def fake_urlopen(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", None, io.BytesIO(body))

    monkeypatch.setattr(clients.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(urllib.error.HTTPError) as ei:
        OpenRouterClient().complete([{"role": "user", "content": "x"}], "fam/m1", 1)
    assert ei.value.code == 403
    assert "not available in your region" in str(ei.value)
    assert key not in str(ei.value)


def test_region_403_is_not_retried(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-SECRET")
    body = json.dumps({"error": {"message": "This model is not available in your region."}}).encode()
    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", None, io.BytesIO(body))

    monkeypatch.setattr(clients.urllib.request, "urlopen", fake_urlopen)
    client = RetryingClient(OpenRouterClient(), sleep=lambda delay: None)
    with pytest.raises(urllib.error.HTTPError) as ei:
        client.complete([{"role": "user", "content": "x"}], "fam/m1", 1)
    assert ei.value.code == 403 and calls["n"] == 1


def test_log_that_appears_mid_batch_is_kept(tmp_path):
    # During seed 1, a complete log for seed 2 shows up. Seed 2 must not be called, and its file stays.
    c = cfg(seeds=[1, 2])
    planted = full_log("B", "fam", 2, [(4.0, 4.0)] * 4)
    planted["game_id"] = "t__fam__B__s2"
    calls = []

    def reply(messages, model, seed, **settings):
        calls.append(seed)
        if seed == 1 and calls.count(1) == 1:
            write_logs([planted], tmp_path)
        return REPLY, 0.0

    class Client:
        is_mock = True

        def complete(self, messages, model, seed, **settings):
            return reply(messages, model, seed)

    done = run_batch(c, Client(), tmp_path, texts=TEXTS)
    assert 2 not in calls
    assert (tmp_path / "t__fam__B__s2.json").read_text(encoding="utf-8") == json.dumps(planted, sort_keys=True)
    assert any(g["game_id"] == "t__fam__B__s2" for g in done)


def test_dropped_calls_count_toward_the_next_cap(tmp_path):
    # 2 paid calls of 0.25, then the game raises. No log, but both calls are in the ledger (spend_already 0.50).
    # Adjusted on wip/phase-4-final (2026-10-25): the per-config cap of run_batch keeps the locked R17 rule
    # (start from logged spend, tests/test_review_M1_budget_resume.py, locked e232bb4), so a rerun with cap
    # 0.50 is NOT refused by run_batch. The ledger is counted by run_all's global "already spent"
    # (tests/test_issue8_run_all_ledger.py). Counting it in run_batch needs the owner's test(fix) (QUESTIONS #29).
    class Partial:
        is_mock = True

        def __init__(self):
            self.n = 0

        def complete(self, messages, model, seed, **settings):
            self.n += 1
            if self.n > 2:
                raise RuntimeError("drop")
            return REPLY, 0.25

    first = Partial()
    with pytest.raises(BatchFailed):
        run_batch(cfg(seeds=[1], budget_usd=10.0), first, tmp_path, texts=TEXTS)
    assert first.n == 3 and list(tmp_path.glob("*.json")) == []
    assert spend_already(tmp_path, ["t"]) == pytest.approx(0.50)
    second = Partial()
    with pytest.raises(BatchFailed):  # not refused up front: logged spend is 0.0 < cap 0.50 (locked M1 rule)
        run_batch(cfg(seeds=[1], budget_usd=0.50), second, tmp_path, texts=TEXTS)
    assert second.n == 3
    assert spend_already(tmp_path, ["t"]) == pytest.approx(1.00)  # 2 + 2 paid calls of 0.25 in the ledger


def test_finished_game_is_not_counted_twice(tmp_path):
    # 8 calls x 0.25 = 2.0. That 2.0 is in the log and in the ledger, and the cap sees 2.0 once.
    def fn(messages, model, seed):
        return REPLY

    run_batch(cfg(seeds=[1], budget_usd=10.0), MockClient(fn, cost_per_call=0.25), tmp_path, texts=TEXTS)
    lines = [json.loads(line) for line in (tmp_path / LEDGER_NAME).read_text(encoding="utf-8").splitlines()]
    assert sum(row["cost_usd"] for row in lines) == pytest.approx(2.0)
    assert sum(g["cost_usd"] for g in load_logs(tmp_path)) == pytest.approx(2.0)
    assert spend_already(tmp_path, ["t"]) == pytest.approx(2.0)


def test_other_config_ledger_does_not_count(tmp_path):
    (tmp_path / LEDGER_NAME).write_text(
        json.dumps({"config": "other", "cost_usd": 9.0, "game_id": "other__fam__B__s1"}) + "\n",
        encoding="utf-8")
    assert spend_already(tmp_path, ["t"]) == pytest.approx(0.0)


def test_old_log_without_a_ledger_still_counts(tmp_path):
    old = full_log("B", "fam", 1, [(4.0, 4.0)] * 4)
    old.update(game_id="t__fam__B__s1", cost_usd=2.0)
    write_logs([old], tmp_path)
    assert spend_already(tmp_path, ["t"]) == pytest.approx(2.0)
    assert [g["game_id"] for g in load_logs(tmp_path)] == ["t__fam__B__s1"]


def test_reproduce_ignores_the_ledger(tmp_path):
    def fn(messages, model, seed):
        return REPLY

    run_batch(cfg(seeds=[1]), MockClient(fn), tmp_path / "runs", texts=TEXTS)
    ledger = tmp_path / "runs" / LEDGER_NAME
    assert ledger.is_file()
    reproduce(tmp_path / "runs", tmp_path / "out", n_draws=20)
    text = (tmp_path / "out" / "checksums.txt").read_text(encoding="utf-8")
    assert LEDGER_NAME not in text
    assert "t__fam__B__s1.json" in text
