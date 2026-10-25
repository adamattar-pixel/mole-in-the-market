"""Run the games of one config.

Usage: python -m tools.run configs/espion_dry.yaml [--out-dir DIR] [--workers N]
--workers N runs N games at the same time (default 1 = one after the other; logs are identical either way).
Dry configs (mock: true) use the deterministic mock client and write to their out_dir (never runs/).
Real configs (mock: false) use OpenRouter and are refused unless the preregistration is FROZEN,
the model ids are real (no "tbd") and OPENROUTER_API_KEY is set (owner's GO, hard stop H2). The repo-root
.env is loaded at startup (harness/envfile.py), never overriding the shell.
"""
import sys
from pathlib import Path as _BootPath
if __name__ == "__main__" and __package__ in (None, ""):
    sys.path.insert(0, str(_BootPath(__file__).resolve().parent.parent))

import argparse
from pathlib import Path

import yaml

from harness.clients import OpenRouterClient, load_prices
from harness.costs import cost_summary
from harness.dryclient import make_dry_client
from harness.envfile import load_env
from harness.runlog import load_logs
from harness.runner import BatchFailed, run_batch, validate_config


def main(argv=None):
    load_env()  # repo-root .env, if any; never overrides the shell, never printed
    ap = argparse.ArgumentParser()
    ap.add_argument("config", help="config file, for example configs/espion_dry.yaml")
    ap.add_argument("--out-dir", default=None, help="override the config out_dir (tests, dry runs)")
    ap.add_argument("--workers", type=int, default=1, help="games run at the same time (default 1)")
    a = ap.parse_args(argv)
    cfg = yaml.safe_load(Path(a.config).read_text(encoding="utf-8"))
    validate_config(cfg)
    out = Path(a.out_dir or cfg["out_dir"])
    client = make_dry_client(cfg) if cfg["mock"] else OpenRouterClient(prices=load_prices())
    try:
        run_batch(cfg, client, out, workers=a.workers)
    except BatchFailed as exc:
        for gid, err in exc.failed.items():
            print(f"FAILED (not logged, rerun to retry): {gid}: {err}")
        return 4
    s = cost_summary([g for g in load_logs(out) if g["game_id"].startswith(cfg["name"] + "__")])
    mean = s["all"]["mean_per_game_usd"]
    print(f"{cfg['name']}: {s['all']['games']} games in {out}, "
          f"cost per game {'n/a' if mean is None else f'{mean:.6f}'} USD ({'mock' if cfg['mock'] else 'real'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
