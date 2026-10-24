"""R17 cost under OpenRouter BYOK (docs/team-artem/MODEL_AND_COST.md, "Final choice"; FIXES_CLIENT.md).

With BYOK, OpenRouter's `usage.cost` is what OpenRouter charges (its BYOK fee, or 0 inside the free
allowance), not the provider's charge on the owner's own key. So every real call is charged
max(usage.cost, prompt_tokens x input price + completion_tokens x output price), with the per-model prices
of configs/prices.yaml (USD per 1M tokens). Both values and the one used are logged per call.
Also: a fallback family may be labelled "<provider>-fb" (configs/run_all.yaml: anthropic-fb).
No network: the HTTP layer is a fake, and sockets are blocked. Expected values are computed by hand.
"""
import io
import json
import socket
from pathlib import Path

import pytest
import yaml

from harness import clients
from harness.clients import BudgetExceeded, BudgetTracker, MissingPrice, OpenRouterClient, load_prices
from harness.runner import expand_games, run_game, validate_config
from helpers3 import cfg

ROOT = Path(__file__).resolve().parent.parent
CONFIGS = ROOT / "configs"
REAL_STEPS = ("espion_smoke", "espion_pilot", "espion_core", "espion_monitor", "espion_ethics",
              "exploratory/espion_mem")
TEXTS = {
    "status": "PROPOSED", "label_sentence": "LABEL[{label}].", "neutral_label": "neutral sender",
    "trust_label": "trusted sender", "offer_body": "OFFER at {deal_price}.", "hint_body": "HINT near {deal_price}.",
    "harmless_body": "HARMLESS request.", "e_instruction": "E-ALLOWED.", "e_threshold_gap_fraction": 0.25,
    "behavioral_gap_fraction": 0.10, "behavioral_window": 3,
}
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


def response(cost, prompt_tokens=1000, completion_tokens=200):
    return {"model": "fam/m1-2026", "provider": "Anthropic", "choices": [{"message": {"content": REPLY}}],
            "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "cost": cost}}


# ---------------- charged cost = max(usage.cost, tokens x price) ----------------

def test_byok_fee_below_token_cost_charges_token_cost(fake_http):
    # 1000 x 1.00 / 1e6 + 200 x 5.00 / 1e6 = 0.001 + 0.001 = 0.002 USD; BYOK fee reported 0.0001
    fake_http["response"] = response(0.0001)
    c = OpenRouterClient(prices=PRICES)
    text, cost = c.complete(MSGS, "fam/m1", 1)
    assert text == REPLY and cost == pytest.approx(0.002)
    assert c.last_call["cost_reported"] == pytest.approx(0.0001)
    assert c.last_call["cost_computed"] == pytest.approx(0.002)
    assert c.last_call["cost_charged"] == pytest.approx(0.002)
    assert c.last_call["cost_source"] == "token_price"


def test_byok_zero_cost_charges_token_cost(fake_http):
    # inside the BYOK free allowance OpenRouter can report 0
    fake_http["response"] = response(0.0, prompt_tokens=2000, completion_tokens=0)
    c = OpenRouterClient(prices=PRICES)
    _, cost = c.complete(MSGS, "fam/m1", 1)
    assert cost == pytest.approx(0.002)  # 2000 x 1.00 / 1e6
    assert c.last_call["cost_source"] == "token_price"


def test_usage_cost_above_token_cost_is_kept(fake_http):
    # a pricier provider endpoint: OpenRouter's own charge 0.0125 > 0.002 from the table
    fake_http["response"] = response(0.0125)
    c = OpenRouterClient(prices=PRICES)
    _, cost = c.complete(MSGS, "fam/m1", 1)
    assert cost == pytest.approx(0.0125)
    assert c.last_call["cost_reported"] == pytest.approx(0.0125)
    assert c.last_call["cost_computed"] == pytest.approx(0.002)
    assert c.last_call["cost_source"] == "usage_cost"


def test_provenance_keeps_raw_usage_with_cost_fields(fake_http):
    fake_http["response"] = response(0.0001)
    c = OpenRouterClient(prices=PRICES)
    c.complete(MSGS, "fam/m1", 1)
    assert c.last_call["usage"]["cost"] == 0.0001 and c.last_call["provider"] == "Anthropic"


def test_unpriced_model_refused_before_any_request(fake_http):
    fake_http["response"] = response(0.0001)
    with pytest.raises(MissingPrice):
        OpenRouterClient(prices=PRICES).complete(MSGS, "fam/other", 1)
    assert fake_http["bodies"] == []  # nothing sent, nothing spent


def test_missing_token_counts_refused(fake_http):
    fake_http["response"] = {"choices": [{"message": {"content": REPLY}}], "usage": {"cost": 0.0001}}
    with pytest.raises(RuntimeError):
        OpenRouterClient(prices=PRICES).complete(MSGS, "fam/m1", 1)


def test_missing_usage_cost_still_refused(fake_http):
    fake_http["response"] = {"choices": [{"message": {"content": REPLY}}],
                             "usage": {"prompt_tokens": 10, "completion_tokens": 10}}
    with pytest.raises(RuntimeError):
        OpenRouterClient(prices=PRICES).complete(MSGS, "fam/m1", 1)


# ---------------- the per-config cap now triggers under BYOK ----------------

def test_config_cap_triggers_on_token_cost_under_byok(fake_http, tmp_path):
    # each call: fee 0.0001 reported, 0.002 charged; cap 0.003 -> the 2nd call goes over (0.004 > 0.003)
    fake_http["response"] = response(0.0001)
    c = cfg(mock=False)
    with pytest.raises(BudgetExceeded):
        run_game(c, expand_games(c)[0], OpenRouterClient(prices=PRICES), TEXTS, BudgetTracker(0.003), tmp_path)
    assert len(fake_http["bodies"]) == 2
    assert list(tmp_path.glob("*.json")) == []  # dropped game, no log


def test_game_log_records_charged_cost_and_both_values(fake_http, tmp_path):
    fake_http["response"] = response(0.0001)
    c = cfg(mock=False)  # 4 rounds x 2 firms = 8 calls
    log = run_game(c, expand_games(c)[0], OpenRouterClient(prices=PRICES), TEXTS, BudgetTracker(100.0), tmp_path)
    assert log["cost_usd"] == pytest.approx(8 * 0.002)
    prov = log["rounds"][0]["firms"]["0"]["provenance"]
    assert (prov["cost_reported"], prov["cost_computed"], prov["cost_source"]) == (
        pytest.approx(0.0001), pytest.approx(0.002), "token_price")


def test_global_cap_counts_token_cost(fake_http):
    from tools.run_all import _Budgeted
    fake_http["response"] = response(0.0001)
    tracker = BudgetTracker(0.003)
    b = _Budgeted(OpenRouterClient(prices=PRICES), tracker)
    b.complete(MSGS, "fam/m1", 1)
    assert tracker.total == pytest.approx(0.002)
    with pytest.raises(BudgetExceeded):
        b.complete(MSGS, "fam/m1", 1)


# ---------------- the price table ----------------

def write_prices(tmp_path, models):
    p = tmp_path / "prices.yaml"
    p.write_text(yaml.safe_dump({"fetched": "2026-10-24", "models": models}), encoding="utf-8")
    return p


def test_load_prices_reads_the_table(tmp_path):
    p = write_prices(tmp_path, {"fam/m1": {"input": 1.0, "output": 5.0}})
    assert load_prices(p) == {"fam/m1": {"input": 1.0, "output": 5.0}}


@pytest.mark.parametrize("entry", [{"input": 1.0}, {"output": 5.0}, {"input": 0, "output": 5.0},
                                   {"input": 1.0, "output": -1.0}, {"input": "1", "output": 5.0},
                                   {"input": True, "output": 5.0}, {"input": float("nan"), "output": 5.0}])
def test_load_prices_rejects_bad_entries(tmp_path, entry):
    with pytest.raises(ValueError):
        load_prices(write_prices(tmp_path, {"fam/m1": entry}))


def test_repo_price_table_hand_values():
    # https://openrouter.ai/api/v1/models, fetched 2026-10-24 11:36 UTC, pricing x 1e6
    p = load_prices()
    assert p["anthropic/claude-haiku-4.5"] == {"input": 1.00, "output": 5.00}
    assert p["anthropic/claude-sonnet-4.5"] == {"input": 3.00, "output": 15.00}
    assert p["meta-llama/llama-3.3-70b-instruct"] == {"input": 0.10, "output": 0.32}
    assert p["qwen/qwen3-235b-a22b-2507"] == {"input": 0.09, "output": 0.55}
    assert "2026-10-24" in (CONFIGS / "prices.yaml").read_text(encoding="utf-8")


def test_every_real_model_and_fallback_has_a_price():
    prices = load_prices()
    ids = set()
    for name in REAL_STEPS:
        c = yaml.safe_load((CONFIGS / f"{name}.yaml").read_text(encoding="utf-8"))
        ids |= {m for f in c["families"] for m in f["models"].values()}
    ra = yaml.safe_load((CONFIGS / "run_all.yaml").read_text(encoding="utf-8"))
    ids |= {m for f in ra["fallback"].values() for m in f["models"].values()}
    assert ids and ids <= set(prices)


# ---------------- real entry points use the table ----------------

def test_run_all_real_factory_uses_prices_and_refuses_unpriced(monkeypatch):
    from tools import run_all
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy-test-value")
    factory = run_all.default_client_factory(False, "pass")
    client = factory(cfg(mock=False))
    assert client.prices == load_prices()
    factory.check_models(["anthropic/claude-haiku-4.5", "meta-llama/llama-3.3-70b-instruct"])
    with pytest.raises(run_all.RunAllRefused, match="price"):
        factory.check_models(["anthropic/claude-haiku-4.5", "anthropic/claude-unpriced-9"])


def test_run_all_refuses_unpriced_fallback_before_any_call(monkeypatch, tmp_path):
    from tools import run_all
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy-test-value")
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: (_ for _ in ()).throw(AssertionError("net")))
    d = tmp_path / "configs"
    (d / "exploratory").mkdir(parents=True)
    for name in REAL_STEPS:
        (d / f"{name}.yaml").write_text((CONFIGS / f"{name}.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    ra = yaml.safe_load((CONFIGS / "run_all.yaml").read_text(encoding="utf-8"))
    ra["fallback"]["anthropic"]["models"] = {"0": "anthropic/claude-unpriced-9", "1": "anthropic/claude-unpriced-9"}
    (d / "run_all.yaml").write_text(yaml.safe_dump(ra), encoding="utf-8")
    with pytest.raises(run_all.RunAllRefused, match="price"):
        run_all.run_pipeline(tmp_path / "root", configs_dir=d, log=lambda *a: None)
    assert not (tmp_path / "root" / "runs").exists()


def test_tools_run_real_client_uses_prices(monkeypatch, tmp_path):
    from tools import run as run_tool
    seen = {}

    class Stop(Exception):
        pass

    def fake_batch(c, client, out, **k):
        seen["client"] = client
        raise Stop

    monkeypatch.setattr(run_tool, "run_batch", fake_batch)
    with pytest.raises(Stop):
        run_tool.main([str(CONFIGS / "espion_smoke.yaml"), "--out-dir", str(tmp_path)])
    assert isinstance(seen["client"], OpenRouterClient) and seen["client"].prices == load_prices()


# ---------------- fallback label "<provider>-fb" ----------------

def test_fb_label_accepted_for_its_provider():
    validate_config(cfg(families=[{"family": "fam-fb", "models": {"0": "fam/m1", "1": "fam/m1"}}]))


@pytest.mark.parametrize("label", ["fam-x", "other-fb", "fam-fb-fb", "-fb"])
def test_other_suffixed_labels_still_rejected(label):
    with pytest.raises(ValueError):
        validate_config(cfg(families=[{"family": label, "models": {"0": "fam/m1", "1": "fam/m1"}}]))


def test_repo_fallback_pilot_config_is_valid():
    from tools.run_all import FALLBACK_PILOT, _derived, load_settings
    st = load_settings(CONFIGS, False)
    validate_config(_derived(st, FALLBACK_PILOT, list(st["fallback"].values())))
