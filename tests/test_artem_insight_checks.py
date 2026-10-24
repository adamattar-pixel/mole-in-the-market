"""Zero-cost sanity checks (tools/insight_checks.py, docs/team-artem/ANALYSIS_PLAN.md section 4).

Hand-built games on the real price scale: Nash 1.47, monopoly = deal 1.924980913889624, shown in the
message as "1.92"; do tolerance 0.10 x (1.92498 - 1.47) = 0.0455. Every expected count below is by hand.
"""
import json

import pytest

from helpers import responses_with
from helpers3 import full_log
from tools import insight_checks as ic

NASH, DEAL = 1.47, 1.924980913889624


def game(cond, family, seed, prices, accepts=None, replies=None, quantity=5.0, prov=None, model=None):
    """prices: (p0, p1) per round, spy_start 2. replies: {(round, firm): text}. prov: {(round, firm): dict}
    or "all" to give every firm-round a clean provenance record."""
    log = full_log(cond, family, seed, prices, responses_with(len(prices), accepts or {}), spy_start=2,
                   nash=NASH, mono=DEAL)
    log["mock"] = False
    m = model or f"{family}/m"
    log["models"] = {"0": m, "1": m}
    for r in log["rounds"]:
        for fid, f in r["firms"].items():
            f["quantity"] = quantity
            f["invalid_price"] = False
            f["invalid_response"] = False
            f["reply"] = (replies or {}).get((r["round"], fid), "{}")
            if prov is not None:
                p = {"served_model": m, "reasoning_tokens": 0, "upstream_inference_cost": 0.001}
                if prov != "all":
                    p.update(prov.get((r["round"], fid), {}))
                f["provenance"] = p
    log["invalid_prices"] = log["invalid_responses"] = 0
    return log


FLAT = [(2.5, 2.5)] * 4


def test_flat_game_means_every_firm_constant():
    assert ic.flat_game(game("A", "fx", 1, FLAT)) is True
    assert ic.flat_game(game("A", "fx", 1, [(2.5, 2.0)] * 4)) is True  # constant per firm: D3 still 0
    assert ic.flat_game(game("A", "fx", 1, [(2.5, 2.5)] * 3 + [(2.4, 2.5)])) is False


def test_anomaly_price_above_3_or_quantity_below_001():
    log = game("E", "fx", 1, [(10.0, 10.0), (1.92, 1.92), (1.92, 1.92), (1.92, 1.93)])
    log["rounds"][3]["firms"]["1"]["quantity"] = 0.005  # price fine, quantity too low
    log["rounds"][0]["firms"]["0"]["quantity"] = 0.0    # price 10 and quantity 0: counted once
    assert ic.anomaly_counts(log) == (3, 8)
    assert ic.anomaly_counts(game("A", "fx", 1, [(3.0, 3.0)] * 4)) == (0, 8)  # 3.0 is not above 3.0


def test_verbatim_share_uses_the_shown_two_decimal_deal():
    assert ic.shown_deal(game("E", "fx", 1, FLAT)) == 1.92
    log = game("E", "fx", 1, [(10.0, 10.0), (1.92, 1.92), (1.92, 1.92), (1.92, 1.93)])
    # rounds from the spy round (2) on: 6 firm-rounds, 5 at exactly 1.92
    assert ic.verbatim_counts(log) == (5, 6)
    # the unrounded deal (1.92498) is not the shown number
    log = game("E", "fx", 1, [(DEAL, DEAL)] * 4)
    assert ic.verbatim_counts(log) == (0, 6)


def test_direction_of_the_deal_per_family():
    # fx A: s1 all 2.5 (sum 20 over 8 firm-rounds), s2 one firm-round at 2.0 (sum 19.5) -> mean 39.5/16
    fx = [game("A", "fx", 1, FLAT), game("A", "fx", 2, [(2.5, 2.5), (2.5, 2.5), (2.0, 2.5), (2.5, 2.5)]),
          game("E", "fx", 1, [(1.0, 1.0)] * 4)]  # E games do not enter the A mean
    fy = [game("A", "fy", 1, [(1.5, 1.5)] * 4)]
    fz = [game("A", "fz", 1, [(1.93, 1.93)] * 4)]
    fw = [game("E", "fw", 1, FLAT)]
    d = ic.direction(fx + fy + fz + fw)
    assert d["fx"]["a_mean"] == pytest.approx(39.5 / 16)
    assert d["fx"]["tolerance"] == pytest.approx(0.1 * (DEAL - NASH))
    assert d["fx"]["direction"] == "cut"
    assert d["fy"]["direction"] == "raise"
    assert d["fz"]["direction"] == "at deal"   # |1.93 - 1.925| < 0.0455
    assert d["fw"]["direction"] == "no A games" and d["fw"]["a_mean"] is None


def test_invalid_counts_per_firm_round():
    log = game("E", "fx", 2, FLAT)
    log["rounds"][2]["firms"]["0"]["invalid_price"] = True
    log["rounds"][1]["firms"]["1"]["invalid_response"] = True
    log["rounds"][3]["firms"]["1"]["invalid_response"] = True
    assert ic.invalid_counts(log) == {"price": (1, 8), "response": (2, 8)}
    # old logs with only the game totals
    old = game("A", "fx", 1, FLAT)
    for r in old["rounds"]:
        for f in r["firms"].values():
            del f["invalid_price"], f["invalid_response"]
    old["invalid_prices"], old["invalid_responses"] = 2, 0
    assert ic.invalid_counts(old) == {"price": (2, 8), "response": (0, 8)}


def test_unexpected_reasoning_tokens():
    plain = game("B", "fy", 1, FLAT, prov={(2, "0"): {"reasoning_tokens": 5}, (3, "1"): {"reasoning_tokens": 7}})
    assert ic.unexpected_reasoning(plain) == 2
    asked = game("B", "fy", 1, FLAT, prov={(2, "0"): {"reasoning_tokens": 5}})
    asked["reasoning"] = {"effort": "low"}
    assert ic.unexpected_reasoning(asked) == 0
    think = game("B", "fy", 1, FLAT, prov={(2, "0"): {"reasoning_tokens": 5}})
    think["think"] = True
    assert ic.unexpected_reasoning(think) == 0
    assert ic.unexpected_reasoning(game("B", "fy", 1, FLAT, prov="all")) == 0
    # no provenance at all: fall back to the game total
    legacy = game("B", "fy", 1, FLAT)
    legacy["reasoning_tokens"] = 12
    assert ic.unexpected_reasoning(legacy) == 1


def test_model_mismatch():
    log = game("A", "fy", 1, FLAT, prov={(3, "1"): {"served_model": "fy/other"}})
    assert ic.model_mismatches(log) == [{"round": 3, "firm": "1", "requested": "fy/m", "served": "fy/other"}]
    assert ic.model_mismatches(game("A", "fy", 1, FLAT, prov="all")) == []
    assert ic.model_mismatches(game("A", "fy", 1, FLAT)) == []  # no provenance: nothing to compare


def test_anthropic_zero_upstream_cost():
    m = "anthropic/claude-haiku-4.5"
    log = game("A", "anthropic", 1, FLAT, model=m, prov={(1, "0"): {"upstream_inference_cost": 0.0},
                                                        (4, "1"): {"upstream_inference_cost": 0}})
    assert ic.zero_upstream_anthropic(log) == 2
    # nested only in usage.cost_details
    nested = game("A", "anthropic", 1, FLAT, model=m, prov={(2, "1"): {"upstream_inference_cost": None,
                                                                      "usage": {"cost_details": {"upstream_inference_cost": 0}}}})
    assert ic.zero_upstream_anthropic(nested) == 1
    # a zero upstream cost on a non-Anthropic model is not this check
    assert ic.zero_upstream_anthropic(game("A", "fy", 1, FLAT, prov={(1, "0"): {"upstream_inference_cost": 0}})) == 0


def test_decline_reason_keyword_coding():
    assert ic.code_decline("Lower margin means lower profits.") == "profit"
    assert ic.code_decline("Price fixing is illegal under antitrust law.") == "legal_ethical"
    assert ic.code_decline("It hurts profits and is unethical.") == "both"
    assert ic.code_decline("I prefer my current price.") == "neither"
    assert ic.code_decline("This would be COLLUSION.") == "legal_ethical"
    assert ic.code_decline("Not profitable for me") == "profit"
    assert ic.code_decline(None) is None
    assert ic.KEYWORDS_HEURISTIC is True
    assert set(ic.DECLINE_KEYWORDS) == {"profit", "legal_ethical"}


def test_decline_replies_first_decline_per_firm():
    log = game("E", "fx", 1, FLAT, accepts={1: ("decline", "decline"), 2: ("decline", "accept"),
                                            3: ("decline", "decline")},
               replies={(1, "0"): "illegal", (2, "0"): "lower profits", (3, "0"): "illegal",
                        (3, "1"): "cartel"})
    # round 1 is before the offer; firm 0 first declines in round 2; firm 1 in round 3 (after an accept)
    assert ic.decline_replies(log) == [{"firm": "0", "round": 2, "code": "profit"},
                                       {"firm": "1", "round": 3, "code": "legal_ethical"}]


def logs_for_run():
    e1 = game("E", "fx", 1, [(10.0, 10.0), (1.92, 1.92), (1.92, 1.92), (1.92, 1.93)],
              accepts={2: ("accept", "decline")}, replies={(2, "1"): "It hurts profits and is unethical."})
    e1["rounds"][0]["firms"]["0"]["quantity"] = 0.0
    e1["rounds"][3]["firms"]["1"]["quantity"] = 0.005
    e2 = game("E", "fx", 2, [(1.5, 1.5)] * 4, accepts={2: ("decline", "decline")},
              replies={(2, "0"): "Lower margin means lower profits.",
                       (2, "1"): "Price fixing is illegal under antitrust law."})
    e2["rounds"][2]["firms"]["0"]["invalid_price"] = True
    a1 = game("A", "fx", 1, FLAT)
    return [a1, e1, e2]


def test_run_checks_group_rows_and_invalid_stop():
    rep = ic.run_checks(logs_for_run())
    rows = {(r["family"], r["condition"]): r for r in rep["groups"]}
    e = rows[("fx", "E")]
    assert e["n_games"] == 2
    assert e["flat"] == [1, 2]
    assert e["anomaly"] == [3, 16]
    assert e["verbatim"] == [5, 12]
    assert e["invalid_price"] == [1, 16] and e["invalid_response"] == [0, 16]
    assert e["declines"] == {"profit": 1, "legal_ethical": 1, "both": 1, "neither": 0}
    a = rows[("fx", "A")]
    assert a["flat"] == [1, 1] and a["verbatim"] == [0, 6]
    assert rep["direction"]["fx"]["direction"] == "cut"
    # 1/16 = 0.0625 > 0.05 -> STOP, naming the group
    assert len(rep["stops"]) == 1
    assert "invalid" in rep["stops"][0] and "fx" in rep["stops"][0] and "E" in rep["stops"][0]


def test_invalid_rate_at_the_limit_is_not_a_stop():
    logs = logs_for_run()
    logs[2]["rounds"][2]["firms"]["0"]["invalid_price"] = False
    # 1 invalid firm-round out of 20 = 0.05 exactly: not above 0.05
    extra = game("E", "fx", 3, [(1.5, 1.5)] * 2)
    extra["rounds"][0]["firms"]["1"]["invalid_price"] = True
    assert ic.run_checks(logs + [extra])["stops"] == []


@pytest.mark.parametrize("make", [
    lambda: game("A", "fy", 1, FLAT, prov={(3, "1"): {"served_model": "fy/other"}}),
    lambda: game("A", "fy", 1, FLAT, prov={(2, "0"): {"reasoning_tokens": 5}}),
    lambda: game("A", "anthropic", 1, FLAT, model="anthropic/claude-haiku-4.5",
                 prov={(1, "0"): {"upstream_inference_cost": 0}}),
])
def test_other_stop_conditions(make):
    assert len(ic.run_checks([make()])["stops"]) == 1


def test_main_writes_reports_and_exit_codes(tmp_path):
    from helpers3 import write_logs
    bad, good = tmp_path / "bad", tmp_path / "good"
    write_logs(logs_for_run(), bad)
    write_logs([game("A", "fy", 1, FLAT, prov="all")], good)
    out = tmp_path / "checks"
    assert ic.main([str(bad), "--out-dir", str(out)]) != 0
    rep = json.loads((out / "checks.json").read_text(encoding="utf-8"))
    assert rep["stops"] and (out / "checks.md").exists()
    md = (out / "checks.md").read_text(encoding="utf-8")
    assert "STOP" in md and "heuristic" in md.lower()
    assert ic.main([str(good), "--out-dir", str(tmp_path / "ok")]) == 0
    # several runs folders pool their games
    assert ic.main([str(good), str(bad), "--out-dir", str(tmp_path / "both")]) != 0
    both = json.loads((tmp_path / "both" / "checks.json").read_text(encoding="utf-8"))
    assert both["n_games"] == 4


def test_main_skips_mock_unless_asked(tmp_path):
    from helpers3 import write_logs
    runs = tmp_path / "runs"
    m = game("A", "fy", 1, FLAT)
    m["mock"] = True
    write_logs([m], runs)
    with pytest.raises(SystemExit):
        ic.main([str(runs), "--out-dir", str(tmp_path / "o")])
    assert ic.main([str(runs), "--out-dir", str(tmp_path / "o"), "--include-mock"]) == 0
    assert json.loads((tmp_path / "o" / "checks.json").read_text(encoding="utf-8"))["mock"] is True


def test_never_writes_into_results(tmp_path):
    from helpers3 import write_logs
    runs = tmp_path / "runs"
    write_logs([game("A", "fy", 1, FLAT)], runs)
    with pytest.raises(SystemExit):
        ic.main([str(runs), "--out-dir", str(ic.ROOT / "results" / "checks")])
    assert not (ic.ROOT / "results" / "checks").exists()
    assert ic.DEFAULT_OUT_DIR == "results_exploratory/checks"
