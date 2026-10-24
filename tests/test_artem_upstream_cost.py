"""BYOK provenance (D22): log OpenRouter's `usage.cost_details.upstream_inference_cost` when present.

Under BYOK, usage.cost is only OpenRouter's fee (about 0) and the provider bills the owner's own key. OpenRouter
reports that upstream bill in usage.cost_details.upstream_inference_cost. It is logged per call (provenance)
and summed per family in the smoke report, so the owner can compare it with the charged cost. It never lowers
the charged cost: that stays max(usage.cost, tokens x price).
No network: the HTTP layer is a fake, and sockets are blocked. Expected values are computed by hand.
"""
import io
import json
import socket

import pytest

from harness import clients
from harness.clients import OpenRouterClient

REPLY = json.dumps({"price": 5.0, "response_to_message": "no_message"})
MSGS = [{"role": "user", "content": "x"}]
# 1.00 USD in, 5.00 USD out per 1M tokens
PRICES = {"fam/m1": {"input": 1.0, "output": 5.0}}


@pytest.fixture
def fake_http(monkeypatch):
    def no_net(*a, **k):
        raise AssertionError("network used")
    monkeypatch.setattr(socket, "create_connection", no_net)
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy-test-value")
    state = {"response": None}

    class Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(clients.urllib.request, "urlopen",
                        lambda req, timeout=None: Resp(json.dumps(state["response"]).encode("utf-8")))
    return state


def response(cost, cost_details=None):
    usage = {"prompt_tokens": 1000, "completion_tokens": 200, "cost": cost}
    if cost_details is not None:
        usage["cost_details"] = cost_details
    return {"model": "fam/m1-2026", "provider": "Anthropic", "choices": [{"message": {"content": REPLY}}],
            "usage": usage}


@pytest.mark.parametrize("prices", [PRICES, None])
def test_upstream_inference_cost_logged_when_present(fake_http, prices):
    fake_http["response"] = response(0.0, {"upstream_inference_cost": 0.0021})
    c = OpenRouterClient(prices=prices)
    c.complete(MSGS, "fam/m1", 1)
    assert c.last_call["upstream_inference_cost"] == pytest.approx(0.0021)


@pytest.mark.parametrize("details", [None, {}, {"upstream_inference_cost": None}])
def test_upstream_inference_cost_is_none_when_absent(fake_http, details):
    fake_http["response"] = response(0.0001, details)
    c = OpenRouterClient(prices=PRICES)
    c.complete(MSGS, "fam/m1", 1)
    assert "upstream_inference_cost" in c.last_call and c.last_call["upstream_inference_cost"] is None


def test_upstream_cost_never_lowers_the_charged_cost(fake_http):
    # tokens x price = 1000 x 1.00 / 1e6 + 200 x 5.00 / 1e6 = 0.002; upstream 0.0005 and fee 0 are both lower
    fake_http["response"] = response(0.0, {"upstream_inference_cost": 0.0005})
    c = OpenRouterClient(prices=PRICES)
    _, cost = c.complete(MSGS, "fam/m1", 1)
    assert cost == pytest.approx(0.002) and c.last_call["cost_charged"] == pytest.approx(0.002)
    assert c.last_call["cost_source"] == "token_price"


def test_smoke_report_sums_upstream_cost_per_family():
    from tools.run_all import smoke_report

    def g(fam, upstream):
        firm = {"provenance": {"served_model": f"{fam}/m", "provider": "P", "reasoning_tokens": 0,
                               "upstream_inference_cost": upstream}}
        return {"game_id": f"espion_smoke__{fam}__A__s1", "family": fam, "cost_usd": 0.1, "n_rounds": 20,
                "invalid_prices": 0, "invalid_responses": 0, "reasoning_tokens": 0,
                "rounds": [{"round": 1, "firms": {"0": firm, "1": firm}}]}
    rep = smoke_report([g("fa", 0.001), g("fa", 0.003), g("fb", None)])
    # fa: 2 games x 2 firm calls: 2 x 0.001 + 2 x 0.003 = 0.008
    assert rep["fa"]["upstream_inference_cost_usd"] == pytest.approx(0.008)
    assert rep["fb"]["upstream_inference_cost_usd"] is None
