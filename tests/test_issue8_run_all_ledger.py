"""OPEN_ISSUES #8: run_all's global "already spent" includes paid calls of dropped games (runs/_spend.jsonl).

Hand value: the ledger holds two paid calls of a dropped smoke game, 0.75 + 0.50 = 1.25 USD, and there is no
log at all. Before the ledger, run_all started from 0.00 (logs only); it must now start from 1.25.
"""
import json

from harness.runlog import LEDGER_NAME
from tools.run_all import run_pipeline


def test_issue8_run_all_starts_from_logs_plus_ledger(tmp_path):
    root = tmp_path / "root"
    (root / "runs").mkdir(parents=True)
    rows = [{"config": "espion_smoke", "cost_usd": 0.75, "game_id": "espion_smoke__fa__A__s1"},
            {"config": "espion_smoke", "cost_usd": 0.50, "game_id": "espion_smoke__fa__A__s1"},
            {"config": "not_managed", "cost_usd": 9.00, "game_id": "not_managed__fa__A__s1"}]
    (root / "runs" / LEDGER_NAME).write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    lines = []
    res = run_pipeline(root, dry=True, stop_after="smoke", log=lambda *a: lines.append(" ".join(map(str, a))))
    start = [l for l in lines if "already spent" in l]
    assert start and "already spent 1.2500 USD" in start[0]  # 0.75 + 0.50; the unmanaged config is ignored
    assert res["spent_usd"] >= 1.25
