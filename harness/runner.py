"""Game loop and batch runner. R12 logs, R16 design validation, R17 budget stop."""
from dataclasses import dataclass
from pathlib import Path

from harness.agent import build_messages, parse_reply
from harness.clients import BudgetTracker
from harness.conditions import CONDITIONS, build_condition, load_prereg_texts
from harness.config import GameConfig
from harness.runlog import config_hash, current_git_commit, write_game_log
from harness.spy import ScriptedSpy

FIRMS = ("0", "1")


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


def validate_config(cfg):
    for key in ("name", "mock", "n_rounds", "spy_start", "demand", "seeds", "conditions", "families", "budget_usd"):
        if key not in cfg:
            raise ValueError(f"config is missing {key!r}")
    GameConfig.from_dict(cfg)
    if not isinstance(cfg["mock"], bool):
        raise ValueError("mock must be true or false")
    bad = [c for c in cfg["conditions"] if c not in CONDITIONS]
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
    if float(cfg["budget_usd"]) <= 0:
        raise ValueError("budget_usd must be > 0")


def expand_games(cfg):
    games = []
    for fam in cfg["families"]:
        for cond in cfg["conditions"]:
            for seed in cfg["seeds"]:
                gid = f"{cfg['name']}__{fam['family']}__{cond}__s{seed}"
                games.append(GameSpec(gid, cond, seed, fam["family"], dict(fam["models"])))
    return games


def run_game(cfg, spec, client, texts, budget, runs_dir, git_commit="test"):
    gc = GameConfig.from_dict(cfg)
    demand = gc.demand()
    cond = build_condition(spec.condition, texts, gc.deal_price)
    spy = ScriptedSpy(cond.message, gc.spy_start, firm_ids=FIRMS)
    history = {f: [] for f in FIRMS}
    prev_price = {f: None for f in FIRMS}
    rounds, cost = [], 0.0
    invalid_prices = invalid_responses = 0
    for r in range(1, gc.n_rounds + 1):
        msgs = spy.messages_for_round(r)
        firms = {}
        for f in FIRMS:
            prompt = build_messages(f, r, gc.n_rounds, demand.unit_cost, history[f], msgs[f],
                                    cond.extra_instruction)
            text, call_cost = client.complete(prompt, spec.models[f], spec.seed)
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
        q = demand.quantities(firms["0"]["price"], firms["1"]["price"])
        pi = demand.profits(firms["0"]["price"], firms["1"]["price"])
        for i, f in enumerate(FIRMS):
            other = FIRMS[1 - i]
            firms[f]["quantity"], firms[f]["profit"] = q[i], pi[i]
            history[f].append({"round": r, "own_price": firms[f]["price"], "rival_price": firms[other]["price"],
                               "own_quantity": q[i], "own_profit": pi[i]})
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
    write_game_log(log, runs_dir)
    return log


def run_batch(cfg, client, runs_dir, texts=None, prereg_path=None, git_commit=None):
    """Run every game of the config. Existing logs are skipped (never overwritten)."""
    validate_config(cfg)
    if cfg["mock"] and not getattr(client, "is_mock", False):
        raise RealRunRefused("dry run (mock: true) must use the mock client")
    if not cfg["mock"] and getattr(client, "is_mock", True):
        raise RealRunRefused("real run (mock: false) must use the real client")
    texts = texts if texts is not None else load_prereg_texts(prereg_path)
    if not cfg["mock"] and texts.get("status") != "FROZEN":
        raise RealRunRefused("real run refused: preregistration texts are not FROZEN")
    git_commit = git_commit or current_git_commit()
    budget = BudgetTracker(cfg["budget_usd"])
    runs_dir = Path(runs_dir)
    done = []
    for spec in expand_games(cfg):
        if (runs_dir / f"{spec.game_id}.json").exists():
            continue
        done.append(run_game(cfg, spec, client, texts, budget, runs_dir, git_commit=git_commit))
    return done
