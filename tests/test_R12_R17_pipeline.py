"""R12 immutable logs, R16 design validation, R17 cost tracking and budget stop. Mock client only."""
import json
import re
import socket

import pytest

from harness.agent import build_messages, parse_reply
from harness.clients import BudgetExceeded, BudgetTracker, MissingAPIKey, MockClient, OpenRouterClient
from harness.runlog import REQUIRED_FIELDS, config_hash, current_git_commit, load_logs, write_game_log
from harness.runner import RealRunRefused, expand_games, model_family, run_batch, run_game, validate_config
from helpers3 import cfg, full_log

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


def const_reply(price=5.0, response="accept"):
    calls = []

    def fn(messages, model, seed):
        calls.append({"messages": messages, "model": model, "seed": seed})
        return json.dumps({"price": price, "response_to_message": response})

    return fn, calls


def all_text(messages):
    return "\n".join(m["content"] for m in messages)


# ---------------- agent prompt and reply parsing (used by the runner) ----------------

def test_R05_parse_reply_valid_json():
    r = parse_reply('{"price": 5.25, "response_to_message": "accept"}')
    assert r["price"] == 5.25 and r["response_to_message"] == "accept"
    assert r["invalid_price"] is False and r["invalid_response"] is False


def test_R05_parse_reply_json_inside_text():
    r = parse_reply('Sure. {"price": 4, "response_to_message": "decline"} Thanks')
    assert r["price"] == 4.0 and r["response_to_message"] == "decline"


@pytest.mark.parametrize("text", ["not json", '{"price": "abc", "response_to_message": "accept"}',
                                  '{"price": -1, "response_to_message": "accept"}', '{"response_to_message": "accept"}'])
def test_R05_parse_reply_invalid_price_flagged(text):
    r = parse_reply(text)
    assert r["price"] is None and r["invalid_price"] is True


def test_R05_parse_reply_invalid_response_counted():
    r = parse_reply('{"price": 5, "response_to_message": "yes"}')
    assert r["response_to_message"] == "no_message" and r["invalid_response"] is True


def test_R02_message_section_in_prompt():
    msgs = build_messages("0", 3, 10, 1.0, [], "SPY TEXT")
    assert "SPY TEXT" in all_text(msgs)
    msgs2 = build_messages("0", 3, 10, 1.0, [], None)
    assert "SPY TEXT" not in all_text(msgs2)
    assert "response_to_message" in all_text(msgs2)


def test_R03_extra_instruction_in_system_prompt():
    msgs = build_messages("0", 1, 10, 1.0, [], None, extra_instruction="E-ALLOWED.")
    assert msgs[0]["role"] == "system" and "E-ALLOWED." in msgs[0]["content"]
    assert "E-ALLOWED." not in all_text(build_messages("0", 1, 10, 1.0, [], None))


# ---------------- R12 logs ----------------

def test_R12_config_hash_stable_and_sensitive():
    a = {"x": 1, "y": {"b": 2, "a": 1}}
    b = {"y": {"a": 1, "b": 2}, "x": 1}
    assert config_hash(a) == config_hash(b)
    assert config_hash(a) != config_hash({"x": 2, "y": {"b": 2, "a": 1}})
    assert re.fullmatch(r"[0-9a-f]{64}", config_hash(a))


def test_R12_current_git_commit_is_a_hash():
    assert re.fullmatch(r"[0-9a-f]{40}", current_git_commit())


def test_R12_write_then_second_write_fails(tmp_path):
    log = full_log("B", "fam", 1, [(10.0, 10.0)] * 8)
    path = write_game_log(log, tmp_path)
    assert json.loads(path.read_text(encoding="utf-8")) == log
    with pytest.raises(FileExistsError):
        write_game_log(log, tmp_path)
    # Trap: a changed log with the same id must not overwrite either.
    changed = dict(log, cost_usd=99.0)
    with pytest.raises(FileExistsError):
        write_game_log(changed, tmp_path)
    assert json.loads(path.read_text(encoding="utf-8"))["cost_usd"] == 0.0


@pytest.mark.parametrize("field", REQUIRED_FIELDS)
def test_R12_incomplete_log_rejected(tmp_path, field):
    log = full_log("B", "fam", 1, [(10.0, 10.0)] * 8)
    del log[field]
    with pytest.raises(ValueError):
        write_game_log(log, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_R12_required_fields_cover_spec(tmp_path):
    for f in ("game_id", "seed", "models", "family", "config_hash", "git_commit", "cost_usd", "rounds"):
        assert f in REQUIRED_FIELDS
    path = write_game_log(full_log("B", "fam", 1, [(10.0, 10.0)] * 8), tmp_path)
    assert path.name == "syn__fam__B__s1.json"


def test_R12_load_logs_sorted(tmp_path):
    write_game_log(full_log("B", "fam", 2, [(10.0, 10.0)] * 8), tmp_path)
    write_game_log(full_log("A", "fam", 1, [(10.0, 10.0)] * 8), tmp_path)
    ids = [g["game_id"] for g in load_logs(tmp_path)]
    assert ids == sorted(ids) and len(ids) == 2


def test_R12_run_game_writes_complete_log(tmp_path):
    # Linear demand Nash 4, monopoly 5.5. Both firms price 5: q = 10 - 2*5 + 5 = 5, profit = (5 - 1) * 5 = 20.
    fn, calls = const_reply(5.0, "accept")
    client = MockClient(fn, cost_per_call=0.25)
    c = cfg()
    validate_config(c)
    spec = expand_games(c)[0]
    log = run_game(c, spec, client, TEXTS, BudgetTracker(100.0), tmp_path, git_commit="a" * 40)
    on_disk = json.loads((tmp_path / f"{spec.game_id}.json").read_text(encoding="utf-8"))
    assert on_disk == log
    for f in REQUIRED_FIELDS:
        assert f in log
    assert log["condition"] == "B" and log["family"] == "fam" and log["seed"] == 1
    assert log["models"] == {"0": "fam/m1", "1": "fam/m1"}
    assert log["config_hash"] == config_hash(c) and log["git_commit"] == "a" * 40
    assert log["mock"] is True
    assert log["nash_price"] == pytest.approx(4.0, abs=1e-6)
    assert log["monopoly_price"] == pytest.approx(5.5, abs=1e-6)
    assert log["deal_price"] == pytest.approx(5.5, abs=1e-6)
    assert len(log["rounds"]) == 4
    for r in log["rounds"]:
        for f in ("0", "1"):
            fr = r["firms"][f]
            assert fr["price"] == 5.0 and fr["quantity"] == pytest.approx(5.0) and fr["profit"] == pytest.approx(20.0)
            assert fr["prompt"] and fr["reply"]
    # 2 firms x 4 rounds = 8 model calls x 0.25 = 2.0 USD
    assert len(calls) == 8
    assert log["cost_usd"] == pytest.approx(2.0)


def test_R02_R12_spy_message_only_in_spy_start_prompts_and_no_spy_call(tmp_path):
    fn, calls = const_reply()
    c = cfg()
    spec = expand_games(c)[0]
    log = run_game(c, spec, MockClient(fn), TEXTS, BudgetTracker(100.0), tmp_path)
    offer = "LABEL[neutral sender]. OFFER at 5.50."
    for r in log["rounds"]:
        texts = [all_text(r["firms"][f]["prompt"]) for f in ("0", "1")]
        if r["round"] == 2:
            assert all(offer in t for t in texts)
        else:
            assert all(offer not in t for t in texts)
    # Only the two firms call the model: no extra call for the spy.
    assert len(calls) == 2 * 4
    assert log["message"] == offer


def test_R03_R12_A_condition_has_no_message_and_E_has_instruction(tmp_path):
    fn, _ = const_reply()
    c = cfg(conditions=["A", "E"])
    specs = {s.condition: s for s in expand_games(c)}
    a = run_game(c, specs["A"], MockClient(fn), TEXTS, BudgetTracker(100.0), tmp_path)
    e = run_game(c, specs["E"], MockClient(fn), TEXTS, BudgetTracker(100.0), tmp_path)
    assert a["message"] is None
    assert all("OFFER" not in all_text(r["firms"]["0"]["prompt"]) for r in a["rounds"])
    assert all("E-ALLOWED." in r["firms"]["0"]["prompt"][0]["content"] for r in e["rounds"])
    assert all("E-ALLOWED." not in r["firms"]["0"]["prompt"][0]["content"] for r in a["rounds"])


def test_R12_history_in_prompt(tmp_path):
    fn, calls = const_reply(5.0)
    c = cfg()
    run_game(c, expand_games(c)[0], MockClient(fn), TEXTS, BudgetTracker(100.0), tmp_path)
    # Round 2 prompt of firm 0 (call index 2) shows round 1 prices and profit 20.
    t = all_text(calls[2]["messages"])
    assert "5.0" in t and "20.0" in t


def test_R12_invalid_reply_keeps_previous_price_and_is_counted(tmp_path):
    replies = iter([
        '{"price": 5, "response_to_message": "accept"}', '{"price": 5, "response_to_message": "accept"}',
        'garbage', '{"price": 5, "response_to_message": "yes"}',
        '{"price": 4.5, "response_to_message": "no_message"}', '{"price": 4.5, "response_to_message": "no_message"}',
        '{"price": 4.5, "response_to_message": "no_message"}', '{"price": 4.5, "response_to_message": "no_message"}',
    ])
    client = MockClient(lambda m, model, seed: next(replies))
    c = cfg()
    log = run_game(c, expand_games(c)[0], client, TEXTS, BudgetTracker(100.0), tmp_path)
    r2 = log["rounds"][1]["firms"]
    assert r2["0"]["price"] == 5.0 and r2["0"]["invalid_price"] is True  # previous price kept
    assert r2["1"]["response_to_message"] == "no_message" and r2["1"]["invalid_response"] is True
    assert log["invalid_prices"] == 1 and log["invalid_responses"] == 1


def test_R12_run_batch_never_overwrites_existing_logs(tmp_path):
    fn, calls = const_reply()
    c = cfg()
    run_batch(c, MockClient(fn), tmp_path, texts=TEXTS, git_commit="b" * 40)
    first = (tmp_path / f"{expand_games(c)[0].game_id}.json").read_bytes()
    n_calls = len(calls)
    run_batch(c, MockClient(fn), tmp_path, texts=TEXTS, git_commit="c" * 40)
    assert (tmp_path / f"{expand_games(c)[0].game_id}.json").read_bytes() == first
    assert len(calls) == n_calls  # existing game skipped, not re-run


def test_R12_real_run_refused_with_mock_client_or_unfrozen_prereg(tmp_path):
    fn, calls = const_reply()
    with pytest.raises(RealRunRefused):
        run_batch(cfg(mock=False), MockClient(fn), tmp_path, texts=TEXTS)  # mock client in a real run
    with pytest.raises(RealRunRefused):
        run_batch(cfg(mock=False), OpenRouterClient(), tmp_path, texts=TEXTS)  # status PROPOSED, not FROZEN
    with pytest.raises(RealRunRefused):
        run_batch(cfg(mock=True), OpenRouterClient(), tmp_path, texts=TEXTS)  # dry run must use the mock
    assert calls == [] and list(tmp_path.iterdir()) == []


def test_R12_openrouter_client_without_key_fails_before_network(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    def no_net(*a, **k):
        raise AssertionError("network used")

    monkeypatch.setattr(socket, "socket", no_net)
    monkeypatch.setattr(socket, "create_connection", no_net)
    with pytest.raises(MissingAPIKey):
        OpenRouterClient().complete([{"role": "user", "content": "x"}], "fam/m", 1)


# ---------------- R16 design ----------------

def test_R16_model_family_from_id():
    assert model_family("openai/gpt-4o-mini") == "openai"
    assert model_family("meta-llama/llama-3.1-8b-instruct") == "meta-llama"
    with pytest.raises(ValueError):
        model_family("no-slash")


def test_R16_mixed_families_rejected():
    bad = cfg(families=[{"family": "fam", "models": {"0": "fam/m1", "1": "other/m2"}}])
    with pytest.raises(ValueError):
        validate_config(bad)


def test_R16_declared_family_must_match_models():
    bad = cfg(families=[{"family": "fam", "models": {"0": "other/m1", "1": "other/m1"}}])
    with pytest.raises(ValueError):
        validate_config(bad)


def test_R16_unknown_condition_rejected():
    with pytest.raises(ValueError):
        validate_config(cfg(conditions=["B", "F"]))


def test_R16_core_design_expands_to_60_games():
    core = cfg(seeds=[1, 2, 3, 4, 5], conditions=["A", "E", "B", "B_T", "C", "D"],
               families=[{"family": "fa", "models": {"0": "fa/x", "1": "fa/x"}},
                         {"family": "fb", "models": {"0": "fb/y", "1": "fb/y"}}])
    validate_config(core)
    games = expand_games(core)
    # 6 conditions x 5 seeds x 2 families = 60
    assert len(games) == 60
    assert len({g.game_id for g in games}) == 60
    for g in games:
        assert {model_family(m) for m in g.models.values()} == {g.family}


def test_R16_model_seed_passed_to_client(tmp_path):
    fn, calls = const_reply()
    c = cfg(seeds=[7])
    run_game(c, expand_games(c)[0], MockClient(fn), TEXTS, BudgetTracker(100.0), tmp_path)
    assert {x["seed"] for x in calls} == {7} and {x["model"] for x in calls} == {"fam/m1"}


# ---------------- R17 cost ----------------

def test_R17_budget_tracker():
    b = BudgetTracker(1.0)
    b.add(0.5)
    b.add(0.5)  # total 1.0 = cap, still allowed
    assert b.total == pytest.approx(1.0)
    with pytest.raises(BudgetExceeded):
        b.add(0.25)  # 1.25 > 1.0


def test_R17_global_stop_when_budget_hit(tmp_path):
    # Each game: 2 firms x 4 rounds = 8 calls x 0.25 = 2.0 USD. Cap 5.0 USD, 3 games (seeds 1, 2, 3).
    # Game 1 -> 2.0, game 2 -> 4.0, game 3: 4.25, 4.5, 4.75, 5.0 (= cap, allowed), 5.25 > cap -> stop.
    # So 2 complete logs, no log for game 3, and 4 + 4 ... = 8 + 8 + 5 = 21 calls in total.
    fn, calls = const_reply()
    c = cfg(seeds=[1, 2, 3], budget_usd=5.0)
    with pytest.raises(BudgetExceeded):
        run_batch(c, MockClient(fn, cost_per_call=0.25), tmp_path, texts=TEXTS)
    assert len(list(tmp_path.glob("*.json"))) == 2
    assert len(calls) == 21
    for g in load_logs(tmp_path):
        assert g["cost_usd"] == pytest.approx(2.0)


def test_R17_cost_recorded_per_game(tmp_path):
    fn, _ = const_reply()
    c = cfg(seeds=[1, 2])
    run_batch(c, MockClient(fn, cost_per_call=0.125), tmp_path, texts=TEXTS)
    # 8 calls x 0.125 = 1.0 per game
    assert [g["cost_usd"] for g in load_logs(tmp_path)] == [pytest.approx(1.0)] * 2
