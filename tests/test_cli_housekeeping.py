"""Open issues 9, 10, 11 and 21. Hand values, not copied from the tools.

Issue 9: an espion_* folder with 1 pilot game and 1 smoke game keeps 1 game.
A folder with only hand-built syn__ logs keeps both. A real game plus a mock game of the same
preregistered config keeps the real game only. An all-mock dry folder keeps the mock pilot game.
Issue 21: demo output is allowed only when the folder is named viz/demo*.
"""
import subprocess
import sys
from pathlib import Path

import pytest

from helpers3 import full_log, write_logs
from tools import make_demo_data, price_paths, score_detectors, sensitivity
from tools.cli_logs import select_standalone_logs

ROOT = Path(__file__).resolve().parent.parent
PRICES = [(4.0, 4.0)] * 8


def game(config, seed, mock):
    g = full_log("A", "fx", seed, PRICES, spy_start=2)
    g["game_id"] = f"{config}__fx__A__s{seed}"
    g["mock"] = mock
    return g


def test_run_folder_drops_smoke_and_keeps_a_dry_pilot():
    logs = [game("espion_pilot", 1, True), game("espion_smoke", 1, True)]
    kept = select_standalone_logs(logs)
    assert [g["game_id"] for g in kept] == ["espion_pilot__fx__A__s1"]


def test_hand_built_logs_are_not_filtered():
    a = full_log("A", "fx", 1, PRICES, spy_start=2)
    b = full_log("B", "fx", 2, PRICES, spy_start=2)
    assert select_standalone_logs([a, b]) == [a, b]


def test_real_game_drops_a_mock_copy_but_a_dry_folder_keeps_mock():
    real, mock = game("espion_pilot", 1, False), game("espion_pilot", 2, True)
    assert [g["game_id"] for g in select_standalone_logs([real, mock])] == ["espion_pilot__fx__A__s1"]
    assert len(select_standalone_logs([game("espion_pilot", 1, True), game("espion_core", 1, True)])) == 2


def test_sensitivity_cli_on_a_run_folder_counts_the_pilot_only(tmp_path, capsys):
    write_logs([game("espion_pilot", 1, True), game("espion_smoke", 1, True)], tmp_path)
    assert sensitivity.main([str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "0.10 (prereg) | 3 | 1 |" in out
    assert "0.10 (prereg) | 3 | 2 |" not in out


def test_score_detectors_cli_on_a_run_folder_skips_smoke(tmp_path):
    write_logs([game("espion_core", 1, False), game("espion_smoke", 1, False)], tmp_path)
    assert score_detectors.main([str(tmp_path), str(tmp_path / "out"), "--n-draws", "5"]) == 0
    import json
    s = json.loads((tmp_path / "out" / "detectors.json").read_text(encoding="utf-8"))
    assert s["n_core_games"] == 1


def test_price_paths_help_describes_the_options():
    proc = subprocess.run([sys.executable, "-m", "tools.price_paths", "--help"], cwd=ROOT,
                          capture_output=True, text=True)
    assert proc.returncode == 0
    for flag, words in (("--out-dir", "price_paths.pdf"), ("--memory-runs", "memory"),
                        ("--game-id", "excerpt"), ("--layout", "grid"),
                        ("--include-mock", "mock"), ("--all-configs", "smoke")):
        assert flag in proc.stdout and words in proc.stdout


def test_tool_script_finds_harness_without_python_m():
    proc = subprocess.run([sys.executable, str(ROOT / "tools" / "sensitivity.py"), "--help"],
                          cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "ModuleNotFoundError" not in proc.stderr
    assert "sensitivity" in proc.stdout.lower() or "tolerance" in proc.stdout.lower()


@pytest.mark.parametrize("name", ["figures", "report", "viz", "runs", "results"])
def test_demo_allowlist_refuses_other_folders(tmp_path, name):
    with pytest.raises(ValueError):
        make_demo_data.main(["--out", str(tmp_path / name)])
