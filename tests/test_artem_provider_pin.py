"""Provider pinning (docs/team-artem/FIXES_CLIENT.md, "Provider routing"). R12 logs, R16 config, R17 unchanged.

In the real smoke run, single Llama 3.3 70B games were served by 6 providers. A family may now carry an
optional `provider` block, sent unchanged as OpenRouter's `provider` routing object
(https://openrouter.ai/docs/features/provider-routing: order, allow_fallbacks, quantizations,
require_parameters). It is logged per game as `provider_routing` and is part of the resume check.
Expected pins are written by hand from the OpenRouter endpoints data of 2026-10-24 (see FIXES_CLIENT.md).
No network: the HTTP layer is a fake, sockets are blocked.
"""
import io
import json
import shutil
import socket
from pathlib import Path

import pytest
import yaml

from harness import clients
from harness.clients import BudgetTracker, MockClient, OpenRouterClient
from harness.runlog import load_logs
from harness.runner import RealRunRefused, expand_games, run_batch, run_game, validate_config
from helpers3 import cfg

ROOT = Path(__file__).resolve().parent.parent
CONFIGS = ROOT / "configs"
TEXTS = {
    "status": "PROPOSED", "label_sentence": "LABEL[{label}].", "neutral_label": "neutral sender",
    "trust_label": "trusted sender", "offer_body": "OFFER at {deal_price}.", "hint_body": "HINT near {deal_price}.",
    "harmless_body": "HARMLESS request.", "e_instruction": "E-ALLOWED.", "e_threshold_gap_fraction": 0.25,
    "behavioral_gap_fraction": 0.10, "behavioral_window": 3,
}
REPLY = json.dumps({"price": 5.0, "response_to_message": "no_message"})
MSGS = [{"role": "user", "content": "x"}]
REAL_STEPS = ("espion_smoke", "espion_pilot", "espion_core", "espion_monitor", "espion_ethics",
              "exploratory/espion_mem")
# Hand-written expected pins (FIXES_CLIENT.md "Provider routing")
LLAMA_PIN = {"order": ["coreweave"], "allow_fallbacks": False, "quantizations": ["fp16"], "require_parameters": True}
ANTHROPIC_PIN = {"order": ["anthropic"], "allow_fallbacks": False}
QWEN_PIN = {"order": ["parasail"], "allow_fallbacks": False, "quantizations": ["fp8"], "require_parameters": True}
PIN = {"order": ["provx"], "allow_fallbacks": False}


@pytest.fixture
def fake_http(monkeypatch):
    def no_net(*a, **k):
        raise AssertionError("network used")
    monkeypatch.setattr(socket, "create_connection", no_net)
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy-test-value")
    state = {"bodies": []}

    class Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=None):
        state["bodies"].append(json.loads(req.data.decode("utf-8")))
        return Resp(json.dumps({"model": "fam/m1", "provider": "ProvX", "choices": [{"message": {"content": REPLY}}],
                                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "cost": 0.001}}).encode())

    monkeypatch.setattr(clients.urllib.request, "urlopen", fake_urlopen)
    return state


def load(name):
    return yaml.safe_load((CONFIGS / f"{name}.yaml").read_text(encoding="utf-8"))


# ---------------- client: request body ----------------

def test_client_sends_provider_object_unchanged(fake_http):
    routing = {"order": ["novita"], "allow_fallbacks": False, "quantizations": ["bf16"], "require_parameters": True}
    OpenRouterClient().complete(MSGS, "fam/m1", 3, provider=routing)
    assert fake_http["bodies"][0]["provider"] == routing


def test_client_body_has_no_provider_when_unset(fake_http):
    OpenRouterClient().complete(MSGS, "fam/m1", 3)
    OpenRouterClient().complete(MSGS, "fam/m1", 3, provider=None)
    assert all("provider" not in b for b in fake_http["bodies"])


# ---------------- config validation ----------------

def fam(provider):
    return [{"family": "fam", "models": {"0": "fam/m1", "1": "fam/m1"}, "provider": provider}]


@pytest.mark.parametrize("provider", [
    PIN, LLAMA_PIN, {"order": ["deepinfra/turbo", "novita"]}, {"quantizations": ["fp8", "bf16"]},
    {"order": ["a"], "allow_fallbacks": True, "require_parameters": False},
])
def test_valid_provider_blocks_accepted(provider):
    validate_config(cfg(families=fam(provider)))


@pytest.mark.parametrize("provider", [
    {},                                              # empty
    "novita",                                        # not an object
    {"order": []},                                   # empty order
    {"order": "novita"},                             # order must be a list
    {"order": [""]},                                 # empty slug
    {"order": [3]},                                  # slug must be a string
    {"order": ["a"], "allow_fallbacks": "no"},       # bool only
    {"order": ["a"], "require_parameters": 1},       # bool only
    {"quantizations": ["bf17"]},                     # unknown quantization
    {"quantizations": []},
    {"allow_fallbacks": False},                      # no fallbacks needs an order
    {"order": ["a"], "sort": "price"},               # key not supported here
])
def test_invalid_provider_blocks_refused(provider):
    with pytest.raises(ValueError, match="provider"):
        validate_config(cfg(families=fam(provider)))


# ---------------- runner: passed per family and logged ----------------

class Recorder:
    is_mock = True

    def __init__(self):
        self.calls = []

    def complete(self, messages, model, seed, **settings):
        self.calls.append(settings)
        return REPLY, 0.0


def test_runner_passes_family_provider_and_logs_it(tmp_path):
    c = cfg(families=fam(PIN), temperature=1.0)
    client = Recorder()
    log = run_game(c, expand_games(c)[0], client, TEXTS, BudgetTracker(10.0), tmp_path)
    assert len(client.calls) == 8 and all(s == {"temperature": 1.0, "provider": PIN} for s in client.calls)
    assert log["provider_routing"] == PIN


def test_runner_sends_and_logs_no_provider_when_unset(tmp_path):
    c = cfg()
    client = Recorder()
    log = run_game(c, expand_games(c)[0], client, TEXTS, BudgetTracker(10.0), tmp_path)
    assert all("provider" not in s for s in client.calls)
    assert "provider_routing" not in log


def test_provider_is_per_family(tmp_path):
    fams = [{"family": "fa", "models": {"0": "fa/m", "1": "fa/m"}, "provider": PIN},
            {"family": "fb", "models": {"0": "fb/m", "1": "fb/m"}}]
    c = cfg(families=fams)
    seen = {}

    class ByModel(Recorder):
        def complete(self, messages, model, seed, **settings):
            seen.setdefault(model, []).append(settings.get("provider"))
            return REPLY, 0.0

    for spec in expand_games(c):
        run_game(c, spec, ByModel(), TEXTS, BudgetTracker(10.0), tmp_path)
    assert seen["fa/m"] == [PIN] * 8
    assert seen["fb/m"] == [None] * 8


# ---------------- resume: a changed pin is refused ----------------

def mock(cost=0.0):
    return MockClient(lambda m, mo, s: REPLY, cost_per_call=cost)


def test_resume_refused_when_pin_added(tmp_path):
    c = cfg()
    run_batch(c, mock(), tmp_path, texts=TEXTS)
    c2 = dict(c, families=fam(PIN))
    with pytest.raises(RealRunRefused, match="provider_routing"):
        run_batch(c2, mock(), tmp_path, texts=TEXTS)
    assert len(load_logs(tmp_path)) == 1


def test_resume_refused_when_pin_changed(tmp_path):
    run_batch(cfg(families=fam(PIN)), mock(), tmp_path, texts=TEXTS)
    other = {"order": ["provy"], "allow_fallbacks": False}
    with pytest.raises(RealRunRefused, match="provider_routing"):
        run_batch(cfg(families=fam(other)), mock(), tmp_path, texts=TEXTS)


def test_resume_same_pin_goes_on(tmp_path):
    run_batch(cfg(families=fam(PIN)), mock(), tmp_path, texts=TEXTS)
    assert run_batch(cfg(families=fam(PIN)), mock(), tmp_path, texts=TEXTS) == []
    assert len(load_logs(tmp_path)) == 1


# ---------------- the repo configs ----------------

@pytest.mark.parametrize("name", REAL_STEPS)
def test_real_configs_pin_llama_and_anthropic(name):
    c = load(name)
    validate_config(c)
    pins = {f["family"]: f.get("provider") for f in c["families"]}
    assert pins == {"anthropic": ANTHROPIC_PIN, "meta-llama": LLAMA_PIN}


def test_run_all_fallbacks_are_pinned():
    fb = load("run_all")["fallback"]
    # The anthropic fallback was removed (QUESTIONS #27): every fallback that remains must be pinned.
    assert "anthropic" not in fb
    assert fb["meta-llama"]["provider"] == QWEN_PIN


@pytest.mark.parametrize("name", ["espion_dry", "espion_monitor_dry", "espion_ethics_dry",
                                  "exploratory/espion_mem_dry"])
def test_dry_configs_have_no_provider(name):
    assert all("provider" not in f for f in load(name)["families"])


def test_real_config_family_order_and_settings_unchanged_by_pin():
    # The pin is the only change to the families: ids as decided in D23.
    c = load("espion_core")
    assert [(f["family"], f["models"]) for f in c["families"]] == [
        ("anthropic", {"0": "anthropic/claude-haiku-4.5", "1": "anthropic/claude-haiku-4.5"}),
        ("meta-llama", {"0": "meta-llama/llama-3.3-70b-instruct", "1": "meta-llama/llama-3.3-70b-instruct"})]


# ---------------- run_all: pins must match between pooled or matched steps ----------------

class FakeReal:
    is_mock = False

    def __init__(self):
        self.settings = []

    def complete(self, messages, model, seed, **settings):
        self.settings.append(settings)
        return REPLY, 0.0


@pytest.fixture
def no_network(monkeypatch):
    def refuse(*a, **k):
        raise AssertionError("network access in a test")
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)


FA = {"family": "fa", "models": {"0": "fa/m", "1": "fa/m"}, "provider": PIN}


def cfgdir(tmp_path, edit=None):
    d = tmp_path / "configs"
    (d / "exploratory").mkdir(parents=True)
    for name in REAL_STEPS:
        c = load(name)
        c["families"] = [json.loads(json.dumps(FA))]
        if edit and name in edit:
            edit[name](c)
        (d / f"{name}.yaml").write_text(yaml.safe_dump(c), encoding="utf-8")
    ra = load("run_all")
    ra["fallback"] = {}
    (d / "run_all.yaml").write_text(yaml.safe_dump(ra), encoding="utf-8")
    return d


def pipeline(tmp_path, client, d, **kw):
    from tools.run_all import run_pipeline
    return run_pipeline(tmp_path / "root", configs_dir=d, client_factory=lambda c: client, n_draws=20,
                        log=lambda *a: None, **kw)


def test_run_all_refuses_pin_mismatch_between_matched_steps(tmp_path, no_network):
    from tools.run_all import RunAllRefused

    def other_pin(c):
        c["families"][0]["provider"] = {"order": ["provy"], "allow_fallbacks": False}

    d = cfgdir(tmp_path, edit={"espion_monitor": other_pin})
    with pytest.raises(RunAllRefused, match="provider"):
        pipeline(tmp_path, FakeReal(), d, stop_after="smoke")
    res = pipeline(tmp_path, FakeReal(), d, stop_after="smoke", allow_settings_mismatch=True)
    assert res["status"] == "stopped"


def test_run_all_sends_the_pin(tmp_path, no_network):
    client = FakeReal()
    res = pipeline(tmp_path, client, cfgdir(tmp_path), stop_after="smoke")
    assert res["status"] == "stopped" and client.settings
    assert all(s.get("provider") == PIN for s in client.settings)


def test_dry_run_all_drops_the_pin(tmp_path):
    from tools.run_all import load_settings, dryify
    st = dryify(load_settings(CONFIGS, exploratory=True), tmp_path)
    for c in st["steps"].values():
        assert all("provider" not in f for f in c["families"])
    assert all("provider" not in f for f in st["fallback"].values())


# ---------------- old smoke logs: archive, never read by the runner ----------------

def old_smoke_log(tmp_path):
    """A smoke game logged before the pin (no provider_routing, other config hash)."""
    d = cfgdir(tmp_path)
    c = yaml.safe_load((d / "espion_smoke.yaml").read_text(encoding="utf-8"))
    c["families"][0].pop("provider")
    c["mock"], c["out_dir"] = True, "dry_runs"
    old = tmp_path / "old"
    run_batch(dict(c, conditions=["A"]), mock(), old, texts=dict(TEXTS, status="FROZEN"))
    (p,) = sorted(old.glob("espion_smoke__*.json"))
    g = json.loads(p.read_text(encoding="utf-8"))
    g["mock"] = False
    p.write_text(json.dumps(g), encoding="utf-8")
    return d, p


def test_old_smoke_log_in_runs_blocks_the_pinned_smoke(tmp_path, no_network):
    d, p = old_smoke_log(tmp_path)
    runs = tmp_path / "root" / "runs"
    runs.mkdir(parents=True)
    shutil.copy(p, runs / p.name)
    with pytest.raises(RealRunRefused, match="resume refused"):
        pipeline(tmp_path, FakeReal(), d, stop_after="smoke")


def test_archived_smoke_log_is_never_read(tmp_path, no_network):
    d, p = old_smoke_log(tmp_path)
    arch = tmp_path / "root" / "runs_archive" / "smoke_v1"
    arch.mkdir(parents=True)
    shutil.copy(p, arch / p.name)
    before = (arch / p.name).read_bytes()
    res = pipeline(tmp_path, FakeReal(), d, stop_after="smoke")
    assert res["status"] == "stopped"
    logs = load_logs(tmp_path / "root" / "runs")
    assert len(logs) == 2 and all(g["provider_routing"] == PIN for g in logs)
    assert (arch / p.name).read_bytes() == before
