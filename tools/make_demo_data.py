"""R25: invented data for the replay page, written ONLY in viz/demo/ with meta.synthetic = true.

Usage: python -m tools.make_demo_data [--out viz/demo] [--seed 1]
The games go through the real pipeline (runner, metrics, labels, viz export) with a scripted mock client.
Each mock seller of each game gets a random profile (says yes and follows, says yes only, follows silently, neither),
drawn INDEPENDENTLY of the condition, so the demo shows no pattern by design. These are not results.
Offer texts are the frozen texts of PREREGISTRATION.md. Nothing is written to runs/, results/ or viz/data/.
"""
import sys
from pathlib import Path as _BootPath
if __name__ == "__main__" and __package__ in (None, ""):
    sys.path.insert(0, str(_BootPath(__file__).resolve().parent.parent))

import argparse
import hashlib
import json
import random
import re
import tempfile
from pathlib import Path

import yaml

from harness.clients import BudgetTracker, MockClient
from harness.conditions import PREREG_PATH, load_prereg_texts
from harness.config import GameConfig
from harness.labels import make_labels
from harness.runlog import load_logs
from harness.runner import expand_games, run_game, validate_config
from harness.vizexport import export_viz

ROOT = Path(__file__).resolve().parent.parent
PROFILES = ("say_do", "say_only", "do_only", "neither")


def _refuse_real_locations(out):
    """Allow only a viz/demo* folder. runs/, results/, figures/, report/ and viz/data/ are refused."""
    path = Path(out).resolve()
    if path.parent.name.lower() == "viz" and path.name.lower().startswith("demo"):
        return
    raise ValueError(f"demo data can only be written to a viz/demo folder, not {out}")


def demo_config():
    cfg = yaml.safe_load((ROOT / "configs" / "espion_dry.yaml").read_text(encoding="utf-8"))
    cfg.update({"name": "espion_demo", "seeds": [1, 2, 3, 4, 5], "mock_cost_per_call": 0.0})
    cfg.pop("out_dir", None)
    return cfg


def demo_client(cfg, salt, game_id):
    gc = GameConfig.from_dict(cfg)
    nash, deal, spy = gc.nash_price, gc.deal_price, gc.spy_start

    def reply(messages, model, seed):
        firm = re.search(r"firm (\d+)", messages[0]["content"]).group(1)
        user = messages[-1]["content"]
        rnd = int(re.search(r"Round (\d+) of", user).group(1))
        key = f"{salt}|{game_id}|{firm}"
        profile = PROFILES[int(hashlib.sha256(key.encode()).hexdigest(), 16) % 4]
        rng = random.Random(f"{key}|{rnd}")
        moves = profile in ("say_do", "do_only") and rnd > spy
        price = deal + rng.uniform(-0.02, 0.02) if moves else nash + rng.uniform(-0.03, 0.05)
        if "Message received this round" in user:
            response = "accept" if profile in ("say_do", "say_only") else "decline"
        else:
            response = "no_message"
        return json.dumps({"price": round(price, 4), "response_to_message": response})

    return MockClient(reply)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "viz" / "demo"))
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args(argv)
    _refuse_real_locations(a.out)
    cfg = demo_config()
    texts = load_prereg_texts()
    validate_config(cfg)
    with tempfile.TemporaryDirectory() as tmp:
        budget = BudgetTracker(cfg["budget_usd"])
        for spec in expand_games(cfg):  # one client per game: profiles vary game by game, not by condition
            run_game(cfg, spec, demo_client(cfg, a.seed, spec.game_id), texts, budget, tmp, git_commit="demo")
        logs = load_logs(tmp)
    rows = make_labels(logs, n_draws=200, seed=a.seed)
    export_viz(logs, rows, a.out, texts, PREREG_PATH, source_checksum=f"demo-seed-{a.seed}",
               generated_at="demo data, not results", synthetic=True)
    print(f"demo data: {len(logs)} invented games -> {a.out} (synthetic)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
