"""R12, R16, R17 client settings (docs/team-artem/FIXES_CLIENT.md, audit finding 9).

- `temperature` (config, top level): sent in the OpenRouter request when set, recorded in the game log.
- `reasoning` (config, top level or per family; family wins): sent as OpenRouter's `reasoning` request object.
- Provenance per call: served model, provider and the raw `usage` object from the response, plus the
  reasoning token count when the response reports it.
Unset fields keep the current behaviour: nothing new is sent, and dry logs gain no key.
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
REPLY = json.dumps({"price": 5.0, "response_to_message": "no_message"})
MSGS = [{"role": "user", "content": "x"}]


@pytest.fixture
def fake_http(monkeypatch):
    """Replace urlopen with a fake that records request bodies and returns a canned response."""
    def no_net(*a, **k):
        raise AssertionError("network used")
    monkeypatch.setattr(socket, "create_connection", no_net)
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy-test-value")
    state = {"bodies": [], "response": None}

    class Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=None):
        state["bodies"].append(json.loads(req.data.decode("utf-8")))
        return Resp(json.dumps(state["response"]).encode("utf-8"))

    monkeypatch.setattr(clients.urllib.request, "urlopen", fake_urlopen)
    return state


def response(**over):
    r = {"id": "gen-1", "model": "fam/m1-2026", "provider": "ProvX",
         "choices": [{"message": {"content": REPLY}}],
         "usage": {"prompt_tokens": 10, "completion_tokens": 30, "cost": 0.0125,
                   "completion_tokens_details": {"reasoning_tokens": 20}}}
    r.update(over)
    return r


# ---------------- OpenRouter request body ----------------

def test_body_unchanged_when_settings_unset(fake_http):
    fake_http["response"] = response()
    text, cost = OpenRouterClient().complete(MSGS, "fam/m1", 3)
    assert text == REPLY and cost == pytest.approx(0.0125)
    assert fake_http["bodies"] == [{"model": "fam/m1", "messages": MSGS, "seed": 3, "usage": {"include": True}}]


def test_temperature_sent(fake_http):
    fake_http["response"] = response()
    OpenRouterClient().complete(MSGS, "fam/m1", 3, temperature=0.7)
    assert fake_http["bodies"][0]["temperature"] == 0.7
    assert "reasoning" not in fake_http["bodies"][0]


def test_temperature_zero_is_sent_not_dropped(fake_http):
    fake_http["response"] = response()
    OpenRouterClient().complete(MSGS, "fam/m1", 3, temperature=0.0)
    assert fake_http["bodies"][0]["temperature"] == 0.0


def test_reasoning_sent(fake_http):
    fake_http["response"] = response()
    OpenRouterClient().complete(MSGS, "fam/m1", 3, reasoning={"effort": "none"})
    assert fake_http["bodies"][0]["reasoning"] == {"effort": "none"}
    assert "temperature" not in fake_http["bodies"][0]


# ---------------- provenance from the response ----------------

def test_provenance_recorded_from_response(fake_http):
    fake_http["response"] = response()
    c = OpenRouterClient()
    c.complete(MSGS, "fam/m1", 3)
    assert c.last_call["served_model"] == "fam/m1-2026"
    assert c.last_call["provider"] == "ProvX"
    assert c.last_call["usage"]["cost"] == 0.0125
    assert c.last_call["reasoning_tokens"] == 20


def test_provenance_missing_fields_are_none(fake_http):
    fake_http["response"] = {"choices": [{"message": {"content": REPLY}}], "usage": {"cost": 0.001}}
    c = OpenRouterClient()
    c.complete(MSGS, "fam/m1", 3)
    assert c.last_call == {"served_model": None, "provider": None, "usage": {"cost": 0.001},
                           "reasoning_tokens": None}


def test_provenance_reset_each_call(fake_http):
    c = OpenRouterClient()
    fake_http["response"] = response()
    c.complete(MSGS, "fam/m1", 3)
    fake_http["response"] = response(provider="ProvY")
    c.complete(MSGS, "fam/m1", 3)
    assert c.last_call["provider"] == "ProvY"


# ---------------- runner: settings passed and logged ----------------

class FakeClient:
    """Mock-flagged client that records the settings it receives and reports provenance."""
    is_mock = True

    def __init__(self, provenance=True, reasoning_tokens=0):
        self.calls = []
        self.provenance = provenance
        self.reasoning_tokens = reasoning_tokens

    def complete(self, messages, model, seed, **settings):
        self.calls.append(settings)
        if self.provenance:
            self.last_call = {"served_model": model + "-x", "provider": "P", "usage": {"cost": 0.5},
                              "reasoning_tokens": self.reasoning_tokens}
        return REPLY, 0.5


class StrictClient:
    """Old client signature: fails if the runner passes any new keyword."""
    is_mock = True

    def __init__(self):
        self.n = 0

    def complete(self, messages, model, seed):
        self.n += 1
        return REPLY, 0.0


@pytest.fixture
def play_in(tmp_path):
    def _play(c, client):
        return run_game(c, expand_games(c)[0], client, TEXTS, BudgetTracker(1000.0), tmp_path)
    return _play


def test_runner_sends_nothing_new_when_unset(play_in):
    client = StrictClient()
    log = play_in(cfg(), client)
    assert client.n == 8  # 4 rounds x 2 firms, all with the old signature
    assert "temperature" not in log and "reasoning" not in log


def test_runner_passes_and_logs_temperature(play_in):
    client = FakeClient()
    log = play_in(cfg(temperature=0.7), client)
    assert len(client.calls) == 8 and all(s == {"temperature": 0.7} for s in client.calls)
    assert log["temperature"] == 0.7


def test_runner_passes_and_logs_reasoning_top_level(play_in):
    client = FakeClient()
    log = play_in(cfg(reasoning={"effort": "minimal"}), client)
    assert all(s == {"reasoning": {"effort": "minimal"}} for s in client.calls)
    assert log["reasoning"] == {"effort": "minimal"}


def test_family_reasoning_overrides_top_level(play_in):
    fams = [{"family": "fam", "models": {"0": "fam/m1", "1": "fam/m1"}, "reasoning": {"effort": "none"}}]
    client = FakeClient()
    log = play_in(cfg(families=fams, reasoning={"effort": "low"}, temperature=1.0), client)
    assert all(s == {"temperature": 1.0, "reasoning": {"effort": "none"}} for s in client.calls)
    assert log["reasoning"] == {"effort": "none"}


def test_real_config_logs_temperature_even_when_unset(play_in):
    # A real (mock: false) game always records which temperature was sent; None = not sent, provider default.
    log = play_in(cfg(mock=False), FakeClient())
    assert "temperature" in log and log["temperature"] is None


def test_per_call_provenance_and_reasoning_use_logged(play_in):
    log = play_in(cfg(), FakeClient(reasoning_tokens=7))
    for rnd in log["rounds"]:
        for f in ("0", "1"):
            p = rnd["firms"][f]["provenance"]
            assert p["served_model"] == "fam/m1-x" and p["provider"] == "P" and p["usage"]["cost"] == 0.5
    assert log["reasoning_tokens"] == 7 * 8
    assert log["reasoning_used"] is True


def test_reasoning_used_false_when_zero_tokens(play_in):
    log = play_in(cfg(), FakeClient(reasoning_tokens=0))
    assert log["reasoning_tokens"] == 0 and log["reasoning_used"] is False


def test_reasoning_used_none_when_not_reported(play_in):
    log = play_in(cfg(), FakeClient(reasoning_tokens=None))
    assert log["reasoning_tokens"] is None and log["reasoning_used"] is None


# ---------------- validation ----------------

@pytest.mark.parametrize("t", ["hot", -0.1, 2.5, True, float("nan")])
def test_bad_temperature_rejected(t):
    with pytest.raises(ValueError):
        validate_config(cfg(temperature=t))


@pytest.mark.parametrize("t", [None, 0, 0.7, 2.0])
def test_good_temperature_accepted(t):
    validate_config(cfg(temperature=t))


@pytest.mark.parametrize("r", ["none", {"effort": "turbo"}, {"colour": "red"}, {"exclude": "yes"},
                               {"max_tokens": -5}])
def test_bad_reasoning_rejected(r):
    with pytest.raises(ValueError):
        validate_config(cfg(reasoning=r))
    fams = [{"family": "fam", "models": {"0": "fam/m1", "1": "fam/m1"}, "reasoning": r}]
    with pytest.raises(ValueError):
        validate_config(cfg(families=fams))


@pytest.mark.parametrize("r", [None, {"effort": "none"}, {"effort": "minimal"}, {"effort": "low"},
                               {"exclude": True}, {"enabled": False}, {"max_tokens": 0}])
def test_good_reasoning_accepted(r):
    validate_config(cfg(reasoning=r))


# ---------------- configs and dry logs ----------------

OLD_GAME_KEYS = {"game_id", "condition", "offer_form", "trust_label", "message", "extra_instruction", "seed",
                 "models", "family", "config_hash", "git_commit", "mock", "prereg_status", "spy_start",
                 "n_rounds", "nash_price", "monopoly_price", "deal_price", "demand", "cost_usd",
                 "invalid_prices", "invalid_responses", "rounds"}
OLD_FIRM_KEYS = {"price", "response_to_message", "invalid_price", "invalid_response", "prompt", "reply",
                 "quantity", "profit"}


def test_dry_config_logs_gain_no_new_key(tmp_path):
    c = yaml.safe_load((ROOT / "configs" / "espion_dry.yaml").read_text(encoding="utf-8"))
    logs = run_batch(c, make_dry_client(c), tmp_path, texts=TEXTS, git_commit="fixed")
    assert logs
    for g in logs:
        assert set(g) == OLD_GAME_KEYS
        for rnd in g["rounds"]:
            for f in rnd["firms"].values():
                assert set(f) == OLD_FIRM_KEYS


@pytest.mark.parametrize("name", ["espion_smoke", "espion_pilot", "espion_core", "exploratory/espion_mem"])
def test_real_configs_declare_temperature(name):
    c = yaml.safe_load((ROOT / "configs" / f"{name}.yaml").read_text(encoding="utf-8"))
    # declared explicitly: null (provider default, not sent) or the owner's value in [0, 2]
    assert "temperature" in c
    t = c["temperature"]
    assert t is None or (isinstance(t, (int, float)) and not isinstance(t, bool) and 0 <= t <= 2)
    validate_config(c)
