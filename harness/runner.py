"""Game loop and batch runner. R12 logs, R16 design validation, R17 budget stop."""
import math
from dataclasses import dataclass
from pathlib import Path

from harness.agent import build_messages, parse_reply
from harness.clients import BudgetTracker
from harness.conditions import CONDITIONS, build_condition, load_prereg_texts
from harness.config import GameConfig
from harness.defenses import ADDENDUM_CONDITIONS, load_addendum
from harness.runlog import config_hash, current_git_commit, write_game_log
from harness.spy import ScriptedSpy

FIRMS = ("0", "1")
# OpenRouter `reasoning` request object (docs/team-artem/FIXES_CLIENT.md).
REASONING_EFFORTS = ("none", "minimal", "low", "medium", "high", "xhigh")


class RealRunRefused(RuntimeError):
    pass


@dataclass(frozen=True)
class GameSpec:
    game_id: str
    condition: str
    seed: int
    family: str
    models: dict


def model_family(model_id):
    """OpenRouter ids are "provider/model": the family is the provider."""
    parts = str(model_id).split("/", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"model id must look like 'family/model': {model_id!r}")
    return parts[0]


def _check_temperature(t):
    if t is None:
        return
    if isinstance(t, bool) or not isinstance(t, (int, float)) or not math.isfinite(t) or not 0 <= t <= 2:
        raise ValueError(f"temperature must be null or a number in [0, 2]: {t!r}")


def _check_reasoning(r):
    if r is None:
        return
    if not isinstance(r, dict) or not r or set(r) - {"effort", "max_tokens", "exclude", "enabled"}:
        raise ValueError(f"reasoning must be null or an object with effort, max_tokens, exclude, enabled: {r!r}")
    if "effort" in r and r["effort"] not in REASONING_EFFORTS:
        raise ValueError(f"reasoning effort must be one of {REASONING_EFFORTS}: {r['effort']!r}")
    for k in ("exclude", "enabled"):
        if k in r and not isinstance(r[k], bool):
            raise ValueError(f"reasoning {k} must be true or false")
    if "max_tokens" in r:
        m = r["max_tokens"]
        if isinstance(m, bool) or not isinstance(m, int) or m < 0:
            raise ValueError("reasoning max_tokens must be an integer >= 0")


def family_reasoning(cfg, family):
    """Per-family reasoning wins over the top-level one. None = not sent."""
    for fam in cfg["families"]:
        if fam["family"] == family and "reasoning" in fam:
            return fam["reasoning"]
    return cfg.get("reasoning")


def validate_config(cfg):
    for key in ("name", "mock", "n_rounds", "spy_start", "demand", "seeds", "conditions", "families", "budget_usd"):
        if key not in cfg:
            raise ValueError(f"config is missing {key!r}")
    GameConfig.from_dict(cfg)
    if not isinstance(cfg["mock"], bool):
        raise ValueError("mock must be true or false")
    bad = [c for c in cfg["conditions"] if c not in CONDITIONS + ADDENDUM_CONDITIONS]
    if bad or not cfg["conditions"]:
        raise ValueError(f"unknown or empty conditions: {bad}")
    if not cfg["seeds"] or not all(isinstance(s, int) for s in cfg["seeds"]):
        raise ValueError("seeds must be a non-empty list of integers")
    if not cfg["families"]:
        raise ValueError("no model family")
    for fam in cfg["families"]:
        models = fam["models"]
        if set(models) != set(FIRMS):
            raise ValueError(f"family {fam['family']}: need one model per firm {FIRMS}")
        families = {model_family(m) for m in models.values()}
        if families != {fam["family"]}:
            raise ValueError(f"family {fam['family']!r} mixes or mislabels model families: {sorted(families)}")
    _check_temperature(cfg.get("temperature"))
    _check_reasoning(cfg.get("reasoning"))
    for fam in cfg["families"]:
        _check_reasoning(fam.get("reasoning"))
    if float(cfg["budget_usd"]) <= 0:
        raise ValueError("budget_usd must be > 0")
    if not isinstance(cfg.get("memory", False), bool):
        raise ValueError("memory must be true or false")
    if "out_dir" in cfg:
        out = str(cfg["out_dir"]).replace("\\", "/").strip("/")
        in_runs = out == "runs" or out.startswith("runs/")
        in_exploratory = out.startswith("runs_exploratory/")
        if cfg["mock"] and (in_runs or in_exploratory):
            raise ValueError("a mock (dry) config must never write to runs/")
        if not cfg["mock"] and cfg.get("memory", False) and not in_exploratory:
            raise ValueError("an exploratory memory config writes to runs_exploratory/<arm>, never to runs/")
        if not cfg["mock"] and not cfg.get("memory", False) and out != "runs":
            raise ValueError("a real config writes to runs/")


def expand_games(cfg):
    games = []
    for fam in cfg["families"]:
        for cond in cfg["conditions"]:
            for seed in cfg["seeds"]:
                gid = f"{cfg['name']}__{fam['family']}__{cond}__s{seed}"
                games.append(GameSpec(gid, cond, seed, fam["family"], dict(fam["models"])))
    return games


def run_game(cfg, spec, client, texts, budget, runs_dir, git_commit="test", addendum=None):
    gc = GameConfig.from_dict(cfg)
    demand = gc.demand()
    if addendum is None and spec.condition in ADDENDUM_CONDITIONS:
        addendum = load_addendum()
    cond = build_condition(spec.condition, texts, gc.deal_price, addendum)
    spy = ScriptedSpy(cond.message, gc.spy_start, firm_ids=FIRMS)
    history = {f: [] for f in FIRMS}
    memory = bool(cfg.get("memory", False))  # EXPLORATORY arm, off in every frozen config
    past_messages = {f: [] for f in FIRMS}
    prev_price = {f: None for f in FIRMS}
    temperature = cfg.get("temperature")
    reasoning = family_reasoning(cfg, spec.family)
    settings = {k: v for k, v in (("temperature", temperature), ("reasoning", reasoning)) if v is not None}
    reasoning_counts = []
    rounds, cost = [], 0.0
    invalid_prices = invalid_responses = 0
    for r in range(1, gc.n_rounds + 1):
        msgs = spy.messages_for_round(r)
        firms = {}
        for f in FIRMS:
            prompt = build_messages(f, r, gc.n_rounds, demand.unit_cost, history[f], msgs[f],
                                    cond.extra_instruction, past_messages[f] if memory else None)
            text, call_cost = client.complete(prompt, spec.models[f], spec.seed, **settings)
            provenance = getattr(client, "last_call", None)
            cost += call_cost
            budget.add(call_cost)  # raises BudgetExceeded: the game is dropped, no log written
            parsed = parse_reply(text)
            price = parsed["price"]
            if price is None:
                # Invalid price: keep the firm's previous price (Nash price in round 1), and count it.
                price = prev_price[f] if prev_price[f] is not None else gc.nash_price
            invalid_prices += parsed["invalid_price"]
            invalid_responses += parsed["invalid_response"]
            firms[f] = {"price": price, "response_to_message": parsed["response_to_message"],
                        "invalid_price": parsed["invalid_price"], "invalid_response": parsed["invalid_response"],
                        "prompt": prompt, "reply": text}
            if provenance is not None:
                firms[f]["provenance"] = provenance
                reasoning_counts.append(provenance.get("reasoning_tokens"))
        q = demand.quantities(firms["0"]["price"], firms["1"]["price"])
        pi = demand.profits(firms["0"]["price"], firms["1"]["price"])
        for i, f in enumerate(FIRMS):
            other = FIRMS[1 - i]
            firms[f]["quantity"], firms[f]["profit"] = q[i], pi[i]
            history[f].append({"round": r, "own_price": firms[f]["price"], "rival_price": firms[other]["price"],
                               "own_quantity": q[i], "own_profit": pi[i]})
            past_messages[f].append({"round": r, "message": msgs[f], "response": firms[f]["response_to_message"]})
            prev_price[f] = firms[f]["price"]
        rounds.append({"round": r, "firms": firms})
    log = {
        "game_id": spec.game_id, "condition": spec.condition, "offer_form": cond.offer_form,
        "trust_label": cond.trust_label, "message": cond.message, "extra_instruction": cond.extra_instruction,
        "seed": spec.seed, "models": spec.models, "family": spec.family,
        "config_hash": config_hash(cfg), "git_commit": git_commit, "mock": bool(cfg["mock"]),
        "prereg_status": texts.get("status"), "spy_start": gc.spy_start, "n_rounds": gc.n_rounds,
        "nash_price": gc.nash_price, "monopoly_price": gc.monopoly_price, "deal_price": gc.deal_price,
        "demand": gc.demand_params, "cost_usd": cost, "invalid_prices": invalid_prices,
        "invalid_responses": invalid_responses, "rounds": rounds,
    }
    if memory:
        log["memory"] = True
    if cond.base_condition is not None:
        log["base_condition"] = cond.base_condition
        log["addendum_status"] = addendum.get("status")
    if cond.blocked is not None:
        # R31: the monitor read the spy message at spy_start; when blocked, the firms got no message.
        log["monitor"] = {"round": gc.spy_start, "blocked": cond.blocked, "spy_message": cond.spy_message,
                          "rule": "pact_pattern"}
    # New keys only when set, so dry logs stay byte-identical; a real game always records its temperature.
    if "temperature" in cfg or not cfg["mock"]:
        log["temperature"] = temperature
    if reasoning is not None:
        log["reasoning"] = reasoning
    if reasoning_counts:
        known = [n for n in reasoning_counts if n is not None]
        log["reasoning_tokens"] = sum(known) if known else None
        log["reasoning_used"] = (log["reasoning_tokens"] > 0) if known else None
    write_game_log(log, runs_dir)
    return log


def run_batch(cfg, client, runs_dir, texts=None, prereg_path=None, git_commit=None, addendum_path=None):
    """Run every game of the config. Existing logs are skipped (never overwritten)."""
    validate_config(cfg)
    if cfg["mock"] and not getattr(client, "is_mock", False):
        raise RealRunRefused("dry run (mock: true) must use the mock client")
    if not cfg["mock"] and getattr(client, "is_mock", True):
        raise RealRunRefused("real run (mock: false) must use the real client")
    texts = texts if texts is not None else load_prereg_texts(prereg_path)
    if not cfg["mock"] and texts.get("status") != "FROZEN":
        raise RealRunRefused("real run refused: preregistration texts are not FROZEN")
    if not cfg["mock"] and any("tbd" in m.lower() for fam in cfg["families"] for m in fam["models"].values()):
        raise RealRunRefused("real run refused: model ids are placeholders (tbd), the owner has not given the models")
    addendum = None
    if any(c in ADDENDUM_CONDITIONS for c in cfg["conditions"]):
        addendum = load_addendum(addendum_path)
    git_commit = git_commit or current_git_commit()
    budget = BudgetTracker(cfg["budget_usd"])
    runs_dir = Path(runs_dir)
    done = []
    for spec in expand_games(cfg):
        if (runs_dir / f"{spec.game_id}.json").exists():
            continue
        done.append(run_game(cfg, spec, client, texts, budget, runs_dir, git_commit=git_commit, addendum=addendum))
    return done
