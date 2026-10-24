"""Retry of transient network errors (harness/concurrency.py RetryingClient), owner request 2026-10-24.

Real runs failed with `TimeoutError: The read operation timed out` from urllib inside OpenRouterClient.complete,
sometimes wrapped as urllib.error.URLError(reason=timeout). RetryingClient already retries HTTP 429 and 5xx; it
also retries, with the same bounded backoff: TimeoutError / socket.timeout, URLError whose reason is a timeout,
a connection reset or a refused connection, ConnectionResetError, http.client.RemoteDisconnected and
http.client.IncompleteRead. 4xx other than 429 is still never retried.
- Cost is added only on a successful response: a call that times out twice and then succeeds is charged once.
- The retry count of a call (RetryingClient.last_retries) goes into its logged provenance (`retries`) only when
  it was retried: dry logs unchanged, and last_call itself is not changed (locked test_artem_workers).
- The client read timeout default is DEFAULT_TIMEOUT_S (raised from 60 s to 120 s), set per config by
  `timeout_s` (a positive number) for real runs. timeout_s is operational: it is left out of config_hash, so
  adding it to a config does not break the resume guard (review M2) and existing hashes do not change.
No network: the HTTP layer is a fake, and sockets are blocked.
"""
import http.client
import io
import json
import socket
import urllib.error

import pytest

from harness import clients
from harness.clients import BudgetTracker, OpenRouterClient
from harness.concurrency import RetryingClient
from harness.dryclient import make_dry_client
from harness.runlog import config_hash
from harness.runner import expand_games, run_batch, run_game, validate_config
from helpers3 import cfg

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


class Raising:
    """Fake real client: raises the queued errors in order, then succeeds at 0.25 USD per call."""
    is_mock = False

    def __init__(self, errors, cost=0.25):
        self.errors, self.cost, self.calls, self.last_call = list(errors), cost, 0, None

    def complete(self, messages, model, seed, **settings):
        self.calls += 1
        self.last_call = None
        if self.errors:
            raise self.errors.pop(0)
        self.last_call = {"served_model": model}
        return REPLY, self.cost


TRANSIENT = [
    TimeoutError("The read operation timed out"),
    socket.timeout("timed out"),
    urllib.error.URLError(TimeoutError("The read operation timed out")),
    urllib.error.URLError(socket.timeout("timed out")),
    urllib.error.URLError(ConnectionResetError(54, "Connection reset by peer")),
    urllib.error.URLError(ConnectionRefusedError(61, "Connection refused")),
    ConnectionResetError(54, "Connection reset by peer"),
    http.client.RemoteDisconnected("Remote end closed connection without response"),
    http.client.IncompleteRead(b"partial", 100),
]


def http_error(code):
    return urllib.error.HTTPError("https://example.invalid", code, "err", {}, io.BytesIO(b""))


@pytest.mark.parametrize("exc", TRANSIENT, ids=lambda e: type(e).__name__ + ":" + str(getattr(e, "reason", "")))
def test_transient_error_is_retried(exc):
    sleeps = []
    inner = Raising([exc])
    r = RetryingClient(inner, attempts=5, base_delay=1.0, max_delay=30.0, sleep=sleeps.append)
    assert r.complete([], "m", 1) == (REPLY, 0.25)
    assert inner.calls == 2 and sleeps == [1.0]


def test_mixed_transient_errors_same_backoff():
    sleeps = []
    inner = Raising([TimeoutError("t"), http_error(503), ConnectionResetError(), http_error(429)])
    r = RetryingClient(inner, attempts=5, base_delay=1.0, max_delay=30.0, sleep=sleeps.append)
    r.complete([], "m", 1)
    assert inner.calls == 5 and sleeps == [1.0, 2.0, 4.0, 8.0]


def test_timeout_retry_is_bounded():
    sleeps = []
    inner = Raising([TimeoutError("t")] * 10)
    r = RetryingClient(inner, attempts=3, base_delay=1.0, max_delay=30.0, sleep=sleeps.append)
    with pytest.raises(TimeoutError):
        r.complete([], "m", 1)
    assert inner.calls == 3 and sleeps == [1.0, 2.0]


@pytest.mark.parametrize("exc", [
    http_error(400), http_error(401), http_error(402), http_error(403), http_error(404), http_error(422),
    urllib.error.URLError("unknown url type"),
    urllib.error.URLError(socket.gaierror(8, "nodename nor servname provided")),
    ValueError("bad"), RuntimeError("OpenRouter response has no usage cost"), KeyError("choices"),
])
def test_not_retried(exc):
    sleeps = []
    inner = Raising([exc])
    with pytest.raises(type(exc)):
        RetryingClient(inner, attempts=5, sleep=sleeps.append).complete([], "m", 1)
    assert inner.calls == 1 and sleeps == []


def test_retry_count_in_provenance_only_when_retried():
    inner = Raising([TimeoutError("t"), TimeoutError("t")])
    r = RetryingClient(inner, attempts=5, sleep=lambda s: None)
    r.complete([], "m", 1)
    assert r.last_retries == 2 and r.last_call == {"served_model": "m"}
    r.complete([], "m", 1)
    assert r.last_retries == 0


def test_timeout_twice_then_success_charged_once_in_game(tmp_path):
    c = cfg(mock=False)  # 4 rounds x 2 firms = 8 calls at 0.25 USD
    inner = Raising([TimeoutError("t"), TimeoutError("t")])
    budget = BudgetTracker(1000.0)
    log = run_game(c, expand_games(c)[0], RetryingClient(inner, sleep=lambda s: None), TEXTS, budget, tmp_path)
    assert inner.calls == 10
    assert budget.total == pytest.approx(8 * 0.25)
    assert log["cost_usd"] == pytest.approx(8 * 0.25)
    first = log["rounds"][0]["firms"]["0"]["provenance"]
    assert first["retries"] == 2
    assert "retries" not in log["rounds"][0]["firms"]["1"]["provenance"]


@pytest.fixture
def flaky_http(monkeypatch):
    """urlopen fake: raises the queued errors, then returns a canned OpenRouter response."""
    def no_net(*a, **k):
        raise AssertionError("network used")
    monkeypatch.setattr(socket, "create_connection", no_net)
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy-test-value")
    state = {"errors": [], "timeouts": [], "calls": 0}

    class Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=None):
        state["calls"] += 1
        state["timeouts"].append(timeout)
        if state["errors"]:
            raise state["errors"].pop(0)
        return Resp(json.dumps({"model": "fam/m1", "provider": "P", "choices": [{"message": {"content": REPLY}}],
                                "usage": {"prompt_tokens": 10, "completion_tokens": 30, "cost": 0.0125}})
                    .encode("utf-8"))

    monkeypatch.setattr(clients.urllib.request, "urlopen", fake_urlopen)
    return state


def test_openrouter_timeout_twice_then_success(flaky_http):
    flaky_http["errors"] = [TimeoutError("The read operation timed out"),
                            urllib.error.URLError(TimeoutError("The read operation timed out"))]
    r = RetryingClient(OpenRouterClient(), sleep=lambda s: None)
    text, cost = r.complete([{"role": "user", "content": "x"}], "fam/m1", 1)
    assert text == REPLY and cost == pytest.approx(0.0125)
    assert flaky_http["calls"] == 3
    assert r.last_retries == 2 and r.last_call["served_model"] == "fam/m1"


def test_default_timeout_raised():
    assert clients.DEFAULT_TIMEOUT_S == 120
    assert OpenRouterClient().timeout == 120


def test_timeout_s_config_validated():
    validate_config(cfg(timeout_s=300))
    validate_config(cfg(timeout_s=90.5))
    for bad in (0, -5, True, "300", float("inf"), float("nan"), None):
        with pytest.raises(ValueError):
            validate_config(cfg(timeout_s=bad))


@pytest.mark.parametrize("over,expected", [({"timeout_s": 300}, 300), ({}, 120)])
def test_timeout_s_applied_to_real_client(flaky_http, tmp_path, over, expected):
    c = cfg(mock=False, **over)
    client = OpenRouterClient(timeout=7)
    run_batch(c, client, tmp_path, texts=TEXTS, git_commit="fixed")
    assert set(flaky_http["timeouts"]) == {expected}


def test_dry_logs_have_no_retries_key(tmp_path):
    c = cfg()
    logs = run_batch(c, make_dry_client(c), tmp_path, texts=dict(TEXTS, status="PROPOSED"), git_commit="fixed")
    text = json.dumps(logs)
    assert '"retries"' not in text


def test_timeout_s_not_in_config_hash():
    assert config_hash(cfg(timeout_s=300)) == config_hash(cfg())
    assert config_hash(cfg(budget_usd=5.0)) != config_hash(cfg())
