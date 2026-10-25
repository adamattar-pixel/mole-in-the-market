"""R12: complete, immutable game logs in runs/."""
import hashlib
import json
import re
import subprocess
import threading
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


# One JSON line per paid call. Not a game log: load_logs and reproduce only read *.json.
LEDGER_NAME = "_spend.jsonl"
_LEDGER_LOCK = threading.Lock()


def append_spend(runs_dir, config, game_id, cost_usd):
    """Record a call that was already paid, before the game log exists."""
    runs_dir = Path(runs_dir)
    runs_dir.mkdir(parents=True, exist_ok=True)
    line = json.dumps({"config": str(config), "cost_usd": float(cost_usd), "game_id": str(game_id)},
                      sort_keys=True, separators=(",", ":"))
    with _LEDGER_LOCK:
        with (runs_dir / LEDGER_NAME).open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")


def _ledger_by_game(runs_dir, config_names):
    path = Path(runs_dir) / LEDGER_NAME
    by_game = {}
    if not path.is_file():
        return by_game
    names = set(config_names)
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("config") not in names:
            continue
        gid = str(row["game_id"])
        by_game[gid] = by_game.get(gid, 0.0) + float(row["cost_usd"])
    return by_game


def spend_already(runs_dir, config_names, mock=None):
    """Spend of these configs so far.

    A finished game counts once: the larger of its log cost and its ledger lines.
    A dropped game has no log, so its ledger lines count.
    A log with no ledger lines (runs from before the ledger) still counts.
    mock True or False keeps only logs of that kind (same rule as the pipeline). None keeps every log.
    """
    names = set(config_names)
    by_game = _ledger_by_game(runs_dir, names)
    total = 0.0
    seen = set()
    if Path(runs_dir).is_dir():
        for g in load_logs(runs_dir):
            gid = str(g.get("game_id", ""))
            if gid.split("__", 1)[0] not in names:
                continue
            if mock is not None and bool(g.get("mock", True)) != bool(mock):
                continue
            total += max(float(g.get("cost_usd") or 0.0), by_game.get(gid, 0.0))
            seen.add(gid)
    for gid, cost in by_game.items():
        if gid not in seen:
            total += cost
    return total
