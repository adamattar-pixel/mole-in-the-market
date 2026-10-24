"""R12: complete, immutable game logs in runs/."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

REQUIRED_FIELDS = ("game_id", "condition", "seed", "models", "family", "config_hash", "git_commit",
                   "cost_usd", "mock", "spy_start", "n_rounds", "nash_price", "monopoly_price",
                   "deal_price", "rounds")

_SAFE_ID = re.compile(r"^[A-Za-z0-9_.\-]+$")


def config_hash(cfg):
    # timeout_s is operational (how long to wait), not part of the experiment: left out, so adding it to a
    # config keeps its hash and the resume guard (review M2).
    cfg = {k: v for k, v in cfg.items() if k != "timeout_s"}
    canonical = json.dumps(cfg, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def current_git_commit():
    root = Path(__file__).resolve().parent.parent
    out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True)
    return out.stdout.strip()


def write_game_log(log, runs_dir):
    """Write a log once. A second write with the same game id raises FileExistsError."""
    missing = [f for f in REQUIRED_FIELDS if f not in log]
    if missing:
        raise ValueError(f"incomplete log, missing: {missing}")
    if not _SAFE_ID.match(str(log["game_id"])):
        raise ValueError(f"unsafe game id: {log['game_id']!r}")
    runs_dir = Path(runs_dir)
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / f"{log['game_id']}.json"
    with path.open("x", encoding="utf-8") as fh:  # "x" mode: never overwrite
        json.dump(log, fh, sort_keys=True, indent=1)
    return path


def load_logs(runs_dir):
    logs = [json.loads(p.read_text(encoding="utf-8")) for p in Path(runs_dir).glob("*.json")]
    return sorted(logs, key=lambda g: g["game_id"])
