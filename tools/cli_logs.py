"""Which logs the standalone sensitivity, monitor_view and score_detectors commands keep.

A folder of hand-built logs (no game id starting with espion_) is left unchanged, so the locked CLI
tests still see every game they wrote. A run folder (espion_* game ids) keeps the preregistered
configs only (espion_pilot and espion_core). Smoke and O1 are not pooled with the pilot.
Mock logs in that folder are dropped only when a real game is also there. An all-mock dry folder
keeps its mock pilot and core games.
"""
from tools.reproduce import PREREG_CONFIGS, config_name


def select_standalone_logs(logs):
    names = {config_name(g) for g in logs}
    if not any(name.startswith("espion_") for name in names):
        return list(logs)
    kept = [g for g in logs if config_name(g) in PREREG_CONFIGS]
    if any(g.get("mock") is False for g in kept):
        kept = [g for g in kept if g.get("mock") is False]
    return kept
