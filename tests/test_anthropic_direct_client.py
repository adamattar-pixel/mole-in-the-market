"""Direct Anthropic client for the Haiku family (QUESTIONS #27 proposal, OPEN_ISSUES #28). Mock only: urlopen
is replaced by a fake and sockets are blocked, so no real request can leave. The key is read at call time
from ANTHROPIC_API_KEY and is never written anywhere.

Hand values: prices of anthropic/claude-haiku-4.5 in configs/prices.yaml are 1.00 (input) and 5.00 (output)
USD per 1M tokens; a reply with 1,000 input and 200 output tokens costs (1000 x 1.00 + 200 x 5.00) / 1e6 =
0.002 USD.
"""
import io
import json
import socket
import urllib.error

import pytest

from harness import clients
from harness.clients import AnthropicClient, MissingAPIKey, MissingPrice, RoutingClient, load_prices

MODEL = "anthropic/claude-haiku-4.5"
MSGS = [{"role": "system", "content": "You are a seller."}, {"role": "user", "content": "Round 1 of 20."}]


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network used")
    monkeypatch.setattr(socket, "socket", boom)
    monkeypatch.setattr(socket, "create_connection", boom)


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def fake_urlopen(sent, body=None):
    def f(req, timeout=None):
        sent.append({"url": req.full_url, "headers": {k.lower(): v for k, v in req.header_items()},
                     "body": json.loads(req.data.decode("utf-8")), "timeout": timeout})
        data = body or {"model": "claude-haiku-4-5", "content": [{"type": "text", "text": '{"price": 1.92, "response_to_message": "accept"}'}],
                        "stop_reason": "end_turn", "usage": {"input_tokens": 1000, "output_tokens": 200}}
        return FakeResp(json.dumps(data).encode("utf-8"))
    return f


def test_request_shape_reply_and_cost(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    sent = []
    monkeypatch.setattr(clients.urllib.request, "urlopen", fake_urlopen(sent))
    c = AnthropicClient(prices=load_prices())
    assert c.is_mock is False
    text, cost = c.complete(MSGS, MODEL, 3, temperature=1.0, max_tokens=512, provider={"order": ["anthropic"]})
    assert text == '{"price": 1.92, "response_to_message": "accept"}'
    assert cost == pytest.approx(0.002)  # (1000 x 1.00 + 200 x 5.00) / 1e6
    req = sent[0]
    assert req["url"] == "https://api.anthropic.com/v1/messages"
    assert req["headers"]["x-api-key"] == "test-key-not-real"
    assert req["headers"]["anthropic-version"] == "2023-06-01"
    assert req["body"]["model"] == "claude-haiku-4-5"           # OpenRouter id mapped to the Anthropic id
    assert req["body"]["system"] == "You are a seller."          # system message moved to the top-level field
    assert req["body"]["messages"] == [{"role": "user", "content": "Round 1 of 20."}]
    assert req["body"]["max_tokens"] == 512 and req["body"]["temperature"] == 1.0
    assert "seed" not in req["body"]                              # not supported by the Messages API
    assert c.last_call["seed_sent"] is False and c.last_call["provider"] == "anthropic (direct)"
    assert c.last_call["cost_source"] == "token_price" and c.last_call["finish_reason"] == "end_turn"


def test_default_max_tokens(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    sent = []
    monkeypatch.setattr(clients.urllib.request, "urlopen", fake_urlopen(sent))
    AnthropicClient(prices=load_prices()).complete(MSGS, MODEL, 1)
    assert sent[0]["body"]["max_tokens"] == clients.MAX_TOKENS_DEFAULT


def test_missing_key_refused_before_any_request(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    sent = []
    monkeypatch.setattr(clients.urllib.request, "urlopen", fake_urlopen(sent))
    with pytest.raises(MissingAPIKey):
        AnthropicClient(prices=load_prices()).complete(MSGS, MODEL, 1)
    assert sent == []


@pytest.mark.parametrize("model,error", [("anthropic/claude-unknown-9", ValueError), ("meta-llama/llama-3.3-70b-instruct", ValueError)])
def test_unknown_model_refused_before_any_request(monkeypatch, model, error):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    sent = []
    monkeypatch.setattr(clients.urllib.request, "urlopen", fake_urlopen(sent))
    with pytest.raises(error):
        AnthropicClient(prices=load_prices()).complete(MSGS, model, 1)
    assert sent == []


def test_no_price_table_or_unpriced_model_refused(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    sent = []
    monkeypatch.setattr(clients.urllib.request, "urlopen", fake_urlopen(sent))
    with pytest.raises(MissingPrice):  # no usage cost comes back from Anthropic: spend needs the price table (R17)
        AnthropicClient(prices=None).complete(MSGS, MODEL, 1)
    with pytest.raises(MissingPrice):
        AnthropicClient(prices={"anthropic/claude-sonnet-4.5": {"input": 3.0, "output": 15.0}}).complete(MSGS, MODEL, 1)
    assert sent == []


def test_reasoning_and_foreign_provider_refused(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    sent = []
    monkeypatch.setattr(clients.urllib.request, "urlopen", fake_urlopen(sent))
    c = AnthropicClient(prices=load_prices())
    with pytest.raises(ValueError):
        c.complete(MSGS, MODEL, 1, reasoning={"effort": "low"})
    with pytest.raises(ValueError):
        c.complete(MSGS, MODEL, 1, provider={"order": ["bedrock"]})
    assert sent == []


def test_missing_token_counts_refused(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    body = {"model": "claude-haiku-4-5", "content": [{"type": "text", "text": "{}"}], "stop_reason": "end_turn", "usage": {}}
    monkeypatch.setattr(clients.urllib.request, "urlopen", fake_urlopen([], body))
    with pytest.raises(RuntimeError, match="token counts"):
        AnthropicClient(prices=load_prices()).complete(MSGS, MODEL, 1)


def test_http_error_keeps_status_and_hides_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")

    def f(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 429, "Too Many Requests", {},
                                     io.BytesIO(b'{"error": {"message": "rate limited for test-key-not-real"}}'))
    monkeypatch.setattr(clients.urllib.request, "urlopen", f)
    with pytest.raises(urllib.error.HTTPError) as e:
        AnthropicClient(prices=load_prices()).complete(MSGS, MODEL, 1)
    assert e.value.code == 429 and "test-key-not-real" not in str(e.value.reason)


def test_routing_client_dispatches_by_model():
    calls = []

    class Fake:
        is_mock = False
        prices = {"x": 1}

        def __init__(self, name):
            self.name, self.last_call, self.timeout = name, None, None

        def complete(self, messages, model, seed, **settings):
            calls.append((self.name, model))
            self.last_call = {"by": self.name}
            return "{}", 0.0

    default, direct = Fake("openrouter"), Fake("anthropic")
    r = RoutingClient(default, {MODEL: direct})
    assert r.is_mock is False and r.prices == default.prices
    r.complete(MSGS, MODEL, 1)
    assert r.last_call == {"by": "anthropic"}
    r.complete(MSGS, "meta-llama/llama-3.3-70b-instruct", 1)
    assert r.last_call == {"by": "openrouter"}
    assert calls == [("anthropic", MODEL), ("openrouter", "meta-llama/llama-3.3-70b-instruct")]
    r.timeout = 77
    assert default.timeout == 77 and direct.timeout == 77


def test_run_all_factory_routes_families_marked_anthropic(monkeypatch):
    from tools import run_all
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy-test-value")
    factory = run_all.default_client_factory(False, "pass")
    plain = {"name": "x", "families": [{"family": "anthropic", "models": {"0": MODEL, "1": MODEL}}]}
    assert factory(plain) is factory.client                                  # unchanged without the marker
    marked = {"name": "x", "families": [{"family": "anthropic", "client": "anthropic", "models": {"0": MODEL, "1": MODEL}}]}
    routed = factory(marked)
    assert isinstance(routed, RoutingClient) and isinstance(routed.routes[MODEL], AnthropicClient)


def test_run_all_accepts_anthropic_key_alone(monkeypatch):
    from tools import run_all
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    assert run_all.default_client_factory(False, "pass") is not None
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(run_all.RunAllRefused):
        run_all.default_client_factory(False, "pass")
