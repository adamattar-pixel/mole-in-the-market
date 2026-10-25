"""OPEN_ISSUES #26: the standalone score_detectors, sensitivity and monitor_view keep the games that the
preregistered tables exclude through run_all_deviations.json (on the real runs: 40 games incl. the 10 Haiku
pilot games, vs 30 in results/detectors.json). New --deviations option, same file and rule as
`tools.reproduce --deviations`; off by default (unchanged default behaviour).
Hand-built folder: espion_pilot A and E for families fa and fb (4 games); the deviations file drops fb.
"""
import json

from helpers3 import full_log, write_logs
from tools import monitor_view, score_detectors, sensitivity
from tools.cli_logs import deviation_ids, select_standalone_logs


def flat(pre, post, n=10, spy=5):
    return [(pre, pre) if r < spy else (post, post) for r in range(1, n + 1)]


def folder(tmp_path):
    logs = []
    for fam in ("fa", "fb"):
        for cond in ("A", "E"):
            g = full_log(cond, fam, 1, flat(10.0, 15.0))
            g["game_id"] = f"espion_pilot__{fam}__{cond}__s1"
            g["mock"] = False
            logs.append(g)
    write_logs(logs, tmp_path / "runs")
    dev = tmp_path / "dev.json"
    dev.write_text(json.dumps([{"excluded_game_ids": ["espion_pilot__fb__A__s1", "espion_pilot__fb__E__s1"]}]),
                   encoding="utf-8")
    return logs, dev


def test_issue26_deviation_ids_and_selection(tmp_path):
    logs, dev = folder(tmp_path)
    ids = deviation_ids(dev)
    assert ids == {"espion_pilot__fb__A__s1", "espion_pilot__fb__E__s1"}
    assert len(select_standalone_logs(logs)) == 4  # default unchanged
    assert sorted(g["game_id"] for g in select_standalone_logs(logs, exclude_ids=ids)) == [
        "espion_pilot__fa__A__s1", "espion_pilot__fa__E__s1"]


def test_issue26_score_detectors_cli(tmp_path):
    _, dev = folder(tmp_path)
    score_detectors.main([str(tmp_path / "runs"), str(tmp_path / "all")])
    score_detectors.main([str(tmp_path / "runs"), str(tmp_path / "dev"), "--deviations", str(dev)])
    a = json.loads((tmp_path / "all" / "detectors.json").read_text(encoding="utf-8"))
    d = json.loads((tmp_path / "dev" / "detectors.json").read_text(encoding="utf-8"))
    assert (a["n_core_games"], d["n_core_games"]) == (4, 2)
    assert "fb" in a["groups"] and "fb" not in d["groups"]


def test_issue26_sensitivity_and_monitor_view_accept_the_flag(tmp_path):
    _, dev = folder(tmp_path)
    out = tmp_path / "sens.md"
    sensitivity.main([str(tmp_path / "runs"), "--out", str(out), "--deviations", str(dev)])
    assert "fb" not in out.read_text(encoding="utf-8") and "fa" in out.read_text(encoding="utf-8")
    monitor_view.main([str(tmp_path / "runs"), "--out-dir", str(tmp_path / "mv"), "--deviations", str(dev)])
    assert "fb" not in (tmp_path / "mv" / "monitor_view.md").read_text(encoding="utf-8")
