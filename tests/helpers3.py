"""Phase 3 test helpers: complete synthetic logs and a small config (test code only)."""
import copy
import json

from helpers import make_log


def full_log(condition, family, seed, prices, responses=None, spy_start=5, nash=10.0, mono=20.0):
    log = make_log(condition, spy_start, nash, mono, prices, responses)
    log.update({
        "game_id": f"syn__{family}__{condition}__s{seed}",
        "seed": seed,
        "family": family,
        "models": {"0": f"{family}/m", "1": f"{family}/m"},
        "config_hash": "0" * 64,
        "git_commit": "0" * 40,
        "cost_usd": 0.0,
        "mock": True,
    })
    for r in log["rounds"]:
        for f in r["firms"].values():
            f.setdefault("prompt", [{"role": "user", "content": "p"}])
            f.setdefault("reply", "{}")
    return log


def write_logs(logs, runs_dir):
    runs_dir.mkdir(parents=True, exist_ok=True)
    for g in logs:
        (runs_dir / f"{g['game_id']}.json").write_text(json.dumps(g, sort_keys=True), encoding="utf-8")


BASE_CFG = {
    "name": "t",
    "mock": True,
    "n_rounds": 4,
    "spy_start": 2,
    # linear demand: Nash 4.0, monopoly 5.5 (derived by hand in test_R01_economics.py)
    "demand": {"type": "linear", "a": 10, "b": 2, "d": 1, "c": 1},
    "seeds": [1],
    "conditions": ["B"],
    "families": [{"family": "fam", "models": {"0": "fam/m1", "1": "fam/m1"}}],
    "budget_usd": 100.0,
}


def cfg(**over):
    c = copy.deepcopy(BASE_CFG)
    c.update(over)
    return c
