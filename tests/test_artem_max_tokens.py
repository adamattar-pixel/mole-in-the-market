"""Client-side max_tokens (harness/clients.py OpenRouterClient), coordinator request 2026-10-24.

The two Llama pilot games (E seeds 4 and 5, Novita, seed passed) timed out on every attempt while every logged
reply is about 50 chars: likely a seed-deterministic runaway generation, since no max_tokens was sent.
- run_game sends max_tokens on every real call: 512 when no `reasoning` is set (MAX_TOKENS_DEFAULT), 16000
  when it is (MAX_TOKENS_REASONING). A per-family `max_tokens` (positive integer) wins when present. Mock
  clients get no default (the locked settings tests expect the old keywords), OpenRouterClient called with
  no max_tokens sends none (locked test_body_unchanged_when_settings_unset).
- The effective max_tokens and the response's finish_reason (when present) are in each call's provenance.
- A truncated reply (finish_reason "length") goes into the existing invalid-reply counting, never a crash.
- No config gains a key, and config_hash is unchanged (the M2 resume guard keeps the logged pilot games).
No network: the HTTP layer is a fake, and sockets are blocked.
"""
import io
import json
import socket
from pathlib import Path

import pytest
import yaml

from harness import clients
from harness.clients import BudgetTracker, OpenRouterClient
from harness.dryclient import make_dry_client
from harness.runner import expand_games, run_batch, run_game, validate_config
from helpers3 import cfg

ROOT = Path(__file__).resolve().parent.parent
TEXTS = {
    "status": "FROZEN",
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
REPLY = json.dumps({"price": 4.0, "response_to_message": "ignore"})


@pytest.fixture
def fake_http(monkeypatch):
    def no_net(*a, **k):
        raise AssertionError("network used")
    monkeypatch.setattr(socket, "create_connection", no_net)
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy-test-value")
    state = {"bodies": [], "content": REPLY, "finish_reason": "stop"}

    class Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=None):
        state["bodies"].append(json.loads(req.data.decode("utf-8")))
        choice = {"message": {"content": state["content"]}}
        if state["finish_reason"] is not None:
            choice["finish_reason"] = state["finish_reason"]
        return Resp(json.dumps({"model": "fam/m1", "provider": "P", "choices": [choice],
                                "usage": {"prompt_tokens": 10, "completion_tokens": 30, "cost": 0.01}})
                    .encode("utf-8"))

    monkeypatch.setattr(clients.urllib.request, "urlopen", fake_urlopen)
    return state


MSG = [{"role": "user", "content": "x"}]


def test_constants():
    assert clients.MAX_TOKENS_DEFAULT == 512
    assert clients.MAX_TOKENS_REASONING == 16000


@pytest.mark.parametrize("over,expected", [({}, 512), ({"reasoning": {"effort": "high"}}, 16000),
                                           ({"reasoning": {"effort": "none"}}, 16000)])
def test_default_in_real_game(fake_http, tmp_path, over, expected):
    c = cfg(mock=False, **over)
    log = run_game(c, expand_games(c)[0], OpenRouterClient(), TEXTS, BudgetTracker(1000.0), tmp_path)
    assert {b["max_tokens"] for b in fake_http["bodies"]} == {expected}
    prov = log["rounds"][0]["firms"]["0"]["provenance"]
    assert prov["max_tokens"] == expected and prov["finish_reason"] == "stop"


def test_family_reasoning_none_uses_family_value(fake_http, tmp_path):
    fams = [{"family": "fam", "models": {"0": "fam/m1", "1": "fam/m1"}, "reasoning": {"effort": "low"}}]
    c = cfg(mock=False, families=fams)
    run_game(c, expand_games(c)[0], OpenRouterClient(), TEXTS, BudgetTracker(1000.0), tmp_path)
    assert {b["max_tokens"] for b in fake_http["bodies"]} == {16000}


@pytest.mark.parametrize("reasoning", [None, {"effort": "high"}])
def test_explicit_max_tokens_wins(fake_http, reasoning):
    c = OpenRouterClient()
    c.complete(MSG, "fam/m1", 1, reasoning=reasoning, max_tokens=2048)
    assert fake_http["bodies"][0]["max_tokens"] == 2048 and c.last_call["max_tokens"] == 2048


def test_finish_reason_missing_not_recorded(fake_http):
    fake_http["finish_reason"] = None
    c = OpenRouterClient()
    c.complete(MSG, "fam/m1", 1)
    assert "finish_reason" not in c.last_call and "max_tokens" not in c.last_call


def test_family_max_tokens_validated():
    def with_mt(v):
        return cfg(families=[{"family": "fam", "models": {"0": "fam/m1", "1": "fam/m1"}, "max_tokens": v}])
    validate_config(with_mt(4000))
    for bad in (0, -1, 1.5, True, "512", None):
        with pytest.raises(ValueError):
            validate_config(with_mt(bad))


def test_family_max_tokens_sent(fake_http, tmp_path):
    c = cfg(mock=False, reasoning={"effort": "high"},
            families=[{"family": "fam", "models": {"0": "fam/m1", "1": "fam/m1"}, "max_tokens": 4000}])
    log = run_game(c, expand_games(c)[0], OpenRouterClient(), TEXTS, BudgetTracker(1000.0), tmp_path)
    assert {b["max_tokens"] for b in fake_http["bodies"]} == {4000}
    assert log["rounds"][0]["firms"]["0"]["provenance"]["max_tokens"] == 4000


@pytest.mark.parametrize("content", ['{"price": 4.', None, ""])
def test_truncated_reply_counted_invalid(fake_http, tmp_path, content):
    fake_http["content"], fake_http["finish_reason"] = content, "length"
    c = cfg(mock=False)  # 4 rounds x 2 firms
    log = run_game(c, expand_games(c)[0], OpenRouterClient(), TEXTS, BudgetTracker(1000.0), tmp_path)
    assert log["invalid_prices"] == 8
    f = log["rounds"][0]["firms"]["0"]
    assert f["invalid_price"] and f["provenance"]["finish_reason"] == "length"
    assert log["cost_usd"] == pytest.approx(8 * 0.01)


def test_dry_run_unchanged(tmp_path):
    c = cfg()
    logs = run_batch(c, make_dry_client(c), tmp_path, texts=dict(TEXTS, status="PROPOSED"), git_commit="fixed")
    text = json.dumps(logs)
    assert '"max_tokens"' not in text and '"finish_reason"' not in text


def test_no_config_has_max_tokens_or_timeout():
    for p in sorted((ROOT / "configs").rglob("*.yaml")):
        text = p.read_text(encoding="utf-8")
        assert "max_tokens" not in text and "timeout_s" not in text, p
