"""Game loop and batch runner. R12 logs, R16 design validation, R17 budget stop."""
import json
import math
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from harness.agent import build_messages, parse_reply
from harness.clients import DEFAULT_TIMEOUT_S, MAX_TOKENS_DEFAULT, MAX_TOKENS_REASONING, BudgetExceeded
from harness.concurrency import ConcurrentBudget, GuardedClient, RetryingClient, fork_client
from harness.conditions import CONDITIONS, build_condition, load_prereg_texts
from harness.config import GameConfig
from harness.defenses import ADDENDUM_CONDITIONS, addendum_is_frozen, load_addendum
from harness.runlog import REQUIRED_FIELDS, append_spend, config_hash, current_git_commit, spend_already, write_game_log
from harness.spy import ScriptedSpy

FIRMS = ("0", "1")
# OpenRouter `reasoning` request object (docs/team-artem/FIXES_CLIENT.md).
REASONING_EFFORTS = ("none", "minimal", "low", "medium", "high", "xhigh", "max")
# OpenRouter `provider` routing object, the subset used here (docs/team-artem/FIXES_CLIENT.md, provider routing).
PROVIDER_KEYS = ("order", "allow_fallbacks", "quantizations", "require_parameters")
QUANTIZATIONS = ("int4", "int8", "fp4", "mxfp4", "nvfp4", "fp6", "fp8", "mxfp8", "fp16", "bf16", "fp32", "unknown")


class RealRunRefused(RuntimeError):
    pass


class BatchFailed(RuntimeError):
    """Some games of a concurrent batch raised: they have no log (rerun to retry them), the others are logged.
    failed: {game id: error text}; done: the logs written, sorted by game id."""

    def __init__(self, failed, done):
        self.failed, self.done = dict(sorted(failed.items())), done
        super().__init__(f"{len(failed)} game(s) failed, not logged: " +
                         "; ".join(f"{k}: {v}" for k, v in self.failed.items()))


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
    if "effort" in r and "max_tokens" in r:
        raise ValueError("reasoning sets effort or max_tokens, not both (OpenRouter docs)")
    if "effort" in r and r["effort"] not in REASONING_EFFORTS:
        raise ValueError(f"reasoning effort must be one of {REASONING_EFFORTS}: {r['effort']!r}")
    for k in ("exclude", "enabled"):
        if k in r and not isinstance(r[k], bool):
            raise ValueError(f"reasoning {k} must be true or false")
    if "max_tokens" in r:
        m = r["max_tokens"]
        if isinstance(m, bool) or not isinstance(m, int) or m < 0:
            raise ValueError("reasoning max_tokens must be an integer >= 0")


def _check_provider(p):
    if p is None:
        return
    if not isinstance(p, dict) or not p or set(p) - set(PROVIDER_KEYS):
        raise ValueError(f"provider must be null or an object with {PROVIDER_KEYS}: {p!r}")
    if "order" in p:
        o = p["order"]
        if not isinstance(o, list) or not o or not all(isinstance(s, str) and s for s in o):
            raise ValueError(f"provider order must be a non-empty list of provider slugs: {o!r}")
    if "quantizations" in p:
        q = p["quantizations"]
        if not isinstance(q, list) or not q or any(x not in QUANTIZATIONS for x in q):
            raise ValueError(f"provider quantizations must be a non-empty list from {QUANTIZATIONS}: {q!r}")
    for k in ("allow_fallbacks", "require_parameters"):
        if k in p and not isinstance(p[k], bool):
            raise ValueError(f"provider {k} must be true or false")
    if p.get("allow_fallbacks") is False and "order" not in p:
        raise ValueError("provider allow_fallbacks false needs an order (the providers allowed)")


def family_provider(cfg, family):
    """The family's OpenRouter provider routing object. None = not sent (OpenRouter load-balances)."""
    for fam in cfg["families"]:
        if fam["family"] == family:
            return fam.get("provider")
    return None


def family_max_tokens(cfg, family, real=True):
    """max_tokens sent for the family: its own max_tokens if set, else (real client only: a mock generates no
    tokens) MAX_TOKENS_REASONING when reasoning is set, else MAX_TOKENS_DEFAULT. None = not sent.
    Not a game log field, so the resume guard and config_hash are unchanged."""
    for fam in cfg["families"]:
        if fam["family"] == family and "max_tokens" in fam:
            return fam["max_tokens"]
    if not real:
        return None
    return MAX_TOKENS_REASONING if family_reasoning(cfg, family) is not None else MAX_TOKENS_DEFAULT


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
    if "timeout_s" in cfg:
        t = cfg["timeout_s"]
        if isinstance(t, bool) or not isinstance(t, (int, float)) or not math.isfinite(t) or t <= 0:
            raise ValueError(f"timeout_s must be a positive number of seconds: {t!r}")
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
        if "max_tokens" in fam:
            mt = fam["max_tokens"]
            if isinstance(mt, bool) or not isinstance(mt, int) or mt < 1:
                raise ValueError(f"family {fam['family']}: max_tokens must be an integer >= 1: {mt!r}")
        families = {model_family(m) for m in models.values()}
        # A fallback family may be labelled "<provider>-fb", so its logs never pool with the primary's.
        if len(families) != 1 or fam["family"] not in {p + s for p in families for s in ("", "-fb")}:
            raise ValueError(f"family {fam['family']!r} mixes or mislabels model families: {sorted(families)}")
    _check_temperature(cfg.get("temperature"))
    _check_reasoning(cfg.get("reasoning"))
    for fam in cfg["families"]:
        _check_reasoning(fam.get("reasoning"))
        _check_provider(fam.get("provider"))
    if float(cfg["budget_usd"]) <= 0:
        raise ValueError("budget_usd must be > 0")
    if not isinstance(cfg.get("memory", False), bool):
        raise ValueError("memory must be true or false")
    if not isinstance(cfg.get("think", False), bool):
        raise ValueError("think must be true or false")
    if cfg.get("memory", False) and cfg.get("think", False):
        raise ValueError("one exploratory arm per config: memory and think are not both set")
    arm = cfg.get("memory", False) or cfg.get("think", False)
    if "out_dir" in cfg:
        out = str(cfg["out_dir"]).replace("\\", "/").strip("/")
        in_runs = out == "runs" or out.startswith("runs/")
        in_exploratory = out.startswith("runs_exploratory/")
        if cfg["mock"] and (in_runs or in_exploratory):
            raise ValueError("a mock (dry) config must never write to runs/")
        if not cfg["mock"] and arm and not in_exploratory:
            raise ValueError("an exploratory memory or think config writes to runs_exploratory/<arm>, never "
                             "to runs/")
        if not cfg["mock"] and not arm and out != "runs":
            raise ValueError("a real config writes to runs/")


def expand_games(cfg):
    games = []
    for fam in cfg["families"]:
        for cond in cfg["conditions"]:
            for seed in cfg["seeds"]:
                gid = f"{cfg['name']}__{fam['family']}__{cond}__s{seed}"
                games.append(GameSpec(gid, cond, seed, fam["family"], dict(fam["models"])))
    return games


def _complete_log(runs_dir, game_id):
    """A log already on disk for this game, or None when the file is missing or not a complete log."""
    path = Path(runs_dir) / f"{game_id}.json"
    if not path.is_file():
        return None
    try:
        log = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(log, dict) or log.get("game_id") != game_id:
        return None
    if any(f not in log for f in REQUIRED_FIELDS):
        return None
    return log


def run_game(cfg, spec, client, texts, budget, runs_dir, git_commit="test", addendum=None):
    found = _complete_log(runs_dir, spec.game_id)
    if found is not None:
        return found
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
    provider = family_provider(cfg, spec.family)
    max_tokens = family_max_tokens(cfg, spec.family, real=not getattr(client, "is_mock", True))
    settings = {k: v for k, v in (("temperature", temperature), ("reasoning", reasoning), ("provider", provider),
                                  ("max_tokens", max_tokens)) if v is not None}
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
            retries = getattr(client, "last_retries", 0)
            if provenance is not None and retries:
                provenance = dict(provenance, retries=retries)
            cost += call_cost
            # The call is already paid. Record it before the cap check, so a dropped game still counts.
            append_spend(runs_dir, cfg["name"], spec.game_id, call_cost)
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
    if cfg.get("think", False):
        log["think"] = True  # EXPLORATORY THINK arm (docs/team-artem/THINK_ARM.md)
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
    if provider is not None:
        log["provider_routing"] = provider
    if reasoning_counts:
        known = [n for n in reasoning_counts if n is not None]
        log["reasoning_tokens"] = sum(known) if known else None
        log["reasoning_used"] = (log["reasoning_tokens"] > 0) if known else None
    try:
        write_game_log(log, runs_dir)
    except FileExistsError:
        found = _complete_log(runs_dir, spec.game_id)
        if found is not None:
            return found
        raise
    return log


def existing_logs(cfg, runs_dir):
    """Logs already written for this config (game ids "<config name>__...")."""
    paths = sorted(Path(runs_dir).glob(f"{cfg['name']}__*.json"))
    return [json.loads(p.read_text(encoding="utf-8")) for p in paths]


def _budgets_path(cfg, runs_dir):
    return Path(runs_dir) / "_budgets" / f"{cfg['name']}.json"


def read_budgets(cfg, runs_dir):
    """Every budget_usd this config ran with (not a game log: kept out of load_logs and the checksums)."""
    p = _budgets_path(cfg, runs_dir)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def record_budget(cfg, runs_dir):
    seen = read_budgets(cfg, runs_dir)
    if cfg["budget_usd"] not in seen:
        p = _budgets_path(cfg, runs_dir)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(seen + [cfg["budget_usd"]]) + "\n", encoding="utf-8")


class ResumeMismatch(RealRunRefused):
    pass


def check_resume(cfg, existing, runs_dir):
    """Refuse to add games to a config whose logged games were run with other settings (review M2)."""
    fams = {f["family"]: f for f in cfg["families"]}
    # budget_usd is in config_hash, but raising it is how a run goes on after a cap stop (R17).
    hashes = {config_hash(cfg)} | {config_hash(dict(cfg, budget_usd=b)) for b in read_budgets(cfg, runs_dir)}
    for g in existing:
        where = f"resume refused: {g['game_id']} was logged with"
        fam = fams.get(g["family"])
        if fam is None:
            raise ResumeMismatch(f"{where} family {g['family']!r}, which the current config no longer has")
        current = {"models": dict(fam["models"]), "temperature": cfg.get("temperature"),
                   "reasoning": family_reasoning(cfg, g["family"]),
                   "provider_routing": family_provider(cfg, g["family"])}
        for field, now in current.items():
            if g.get(field) != now:
                raise ResumeMismatch(f"{where} {field} {g.get(field)!r}, the current config has {now!r}. "
                                     "Restore the setting or run it under a new config name.")
        if g["config_hash"] not in hashes:
            raise ResumeMismatch(f"{where} another config_hash: the config changed since (only budget_usd may "
                                 "change on a resume). Restore it or run it under a new config name.")


def check_workers(workers):
    if isinstance(workers, bool) or not isinstance(workers, int) or workers < 1:
        raise ValueError(f"workers must be an integer >= 1: {workers!r}")


def run_batch(cfg, client, runs_dir, texts=None, prereg_path=None, git_commit=None, addendum_path=None,
              workers=1):
    """Run every game of the config. Existing logs are skipped (never overwritten).

    workers=1: one game after the other, in expand_games order. workers>1: the games run in a thread pool
    (games are independent, so the logs are byte-identical) and the logs come back sorted by game id; the
    budget bound is in harness/concurrency.py. Both modes retry HTTP 429 and 5xx (RetryingClient).
    A game that raises is reported in BatchFailed and the other games of the batch are kept.
    A log that appears for a game before it is saved is kept and not overwritten."""
    check_workers(workers)
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
        if not cfg["mock"] and not addendum_is_frozen(addendum_path):
            raise RealRunRefused("real run refused: PREREGISTRATION_ADDENDUM.md status is not FROZEN (R35)")
        addendum = load_addendum(addendum_path)
    if not cfg["mock"] and hasattr(client, "timeout"):
        client.timeout = cfg.get("timeout_s", DEFAULT_TIMEOUT_S)
    git_commit = git_commit or current_git_commit()
    runs_dir = Path(runs_dir)
    existing = existing_logs(cfg, runs_dir)
    check_resume(cfg, existing, runs_dir)
    # The cap bounds the config's total spend across reruns: logged games, plus paid calls that
    # never became a log (_spend.jsonl). A game that is in both is counted once.
    budget = ConcurrentBudget(cfg["budget_usd"])
    budget.total = spend_already(runs_dir, [cfg["name"]])
    todo = [s for s in expand_games(cfg) if not (runs_dir / f"{s.game_id}.json").exists()]
    if todo and budget.total >= budget.cap:
        raise BudgetExceeded(f"{cfg['name']}: {budget.total:.4f} USD already logged >= cap {budget.cap:.4f} USD, "
                             f"{len(todo)} games left")
    if todo:
        record_budget(cfg, runs_dir)
    if workers == 1:
        client = RetryingClient(client)
        done, failed = [], {}
        for spec in todo:
            found = _complete_log(runs_dir, spec.game_id)
            if found is not None:
                done.append(found)
                continue
            try:
                done.append(run_game(cfg, spec, client, texts, budget, runs_dir, git_commit=git_commit,
                                     addendum=addendum))
            except BudgetExceeded:
                raise
            except Exception as exc:  # one game's error does not drop the games that follow
                failed[spec.game_id] = f"{type(exc).__name__}: {exc}"
        if failed:
            raise BatchFailed(failed, done)
        return done
    return _run_concurrent(cfg, todo, client, texts, budget, runs_dir, git_commit, addendum, workers)


def _run_concurrent(cfg, todo, client, texts, budget, runs_dir, git_commit, addendum, workers):
    stop = threading.Event()

    def one(spec):
        if stop.is_set():
            raise BudgetExceeded("batch stopped before this game started")
        own = RetryingClient(GuardedClient(fork_client(client), [budget], stop))
        try:
            return run_game(cfg, spec, own, texts, budget, runs_dir, git_commit=git_commit, addendum=addendum)
        except BudgetExceeded:
            stop.set()
            raise

    done, failed, over = [], {}, []
    pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="game")
    try:
        futures = [(spec, pool.submit(one, spec)) for spec in todo]
        for spec, fut in futures:
            try:
                done.append(fut.result())
            except BudgetExceeded as exc:
                over.append((spec.game_id, exc))
            except Exception as exc:  # one game's error never stops or corrupts the others
                failed[spec.game_id] = f"{type(exc).__name__}: {exc}"
    except BaseException:
        stop.set()  # Ctrl-C: no new call; games already in a call finish or are dropped
        raise
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
    done.sort(key=lambda g: g["game_id"])
    if over:
        first = sorted(over, key=lambda x: x[0])[0][1]
        extra = f"; {len(failed)} other game(s) failed: {sorted(failed)}" if failed else ""
        raise BudgetExceeded(f"{first} ({len(over)} game(s) dropped, {len(done)} logged in this batch{extra})")
    if failed:
        raise BatchFailed(failed, done)
    return done
