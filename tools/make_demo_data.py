"""R25: invented data for the replay page, written ONLY in viz/demo/ with meta.synthetic = true.

Usage: python -m tools.make_demo_data [--out viz/demo] [--seed 1]
The games go through the real pipeline (runner, metrics, labels, viz export) with a scripted mock client.
Each mock seller gets a random profile (says yes and follows, says yes only, follows silently, neither),
drawn INDEPENDENTLY of the condition, so the demo shows no pattern by design. These are not results.
Offer texts are the frozen texts of PREREGISTRATION.md. Nothing is written to runs/, results/ or viz/data/.
"""
import argparse
import hashlib
import json
import random
import re
import tempfile
from pathlib import Path

import yaml

from harness.clients import MockClient
from harness.conditions import PREREG_PATH, load_prereg_texts
from harness.config import GameConfig
from harness.labels import make_labels
from harness.runlog import load_logs
from harness.runner import run_batch
from harness.vizexport import export_viz

ROOT = Path(__file__).resolve().parent.parent
PROFILES = ("say_do", "say_only", "do_only", "neither")


def _refuse_real_locations(out):
    parts = [p.lower() for p in Path(out).resolve().parts]
    if "runs" in parts or "results" in parts or parts[-2:] == ["viz", "data"]:
        raise ValueError(f"demo data must not be written to {out} (runs/, results/ or viz/data/)")


def demo_config():
    cfg = yaml.safe_load((ROOT / "configs" / "espion_dry.yaml").read_text(encoding="utf-8"))
    cfg.update({"name": "espion_demo", "seeds": [1, 2, 3, 4, 5], "mock_cost_per_call": 0.0})
    cfg.pop("out_dir", None)
    return cfg


def demo_client(cfg, salt):
    gc = GameConfig.from_dict(cfg)
    nash, deal, spy = gc.nash_price, gc.deal_price, gc.spy_start

    def reply(messages, model, seed):
        firm = re.search(r"firm (\d+)", messages[0]["content"]).group(1)
        user = messages[-1]["content"]
        rnd = int(re.search(r"Round (\d+) of", user).group(1))
        key = f"{salt}|{model}|{seed}|{firm}"
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
    with tempfile.TemporaryDirectory() as tmp:
        run_batch(cfg, demo_client(cfg, a.seed), tmp, texts=texts, git_commit="demo")
        logs = load_logs(tmp)
    rows = make_labels(logs, n_draws=200, seed=a.seed)
    export_viz(logs, rows, a.out, texts, PREREG_PATH, source_checksum=f"demo-seed-{a.seed}",
               generated_at="demo data, not results", synthetic=True)
    print(f"demo data: {len(logs)} invented games -> {a.out} (synthetic)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
