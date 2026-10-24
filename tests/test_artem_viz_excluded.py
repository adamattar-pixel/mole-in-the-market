"""Viz export of families dropped at the E gate: the page must show why a family is missing.

reproduce --deviations run_all_deviations.json excludes the listed game ids (as run_all's scoring step does) and
writes meta.excluded_families (game count, model ids, gate result) into viz/data. Prices as in
test_artem_reproduce_filter.py: Nash 10, deal 20, spy_start 5, 10 rounds.
"""
import json

from helpers3 import full_log, write_logs
from tools import reproduce as rep

N = 10
AT_NASH = [(10.0, 10.0)] * N


def game(family, condition, seed):
    g = full_log(condition, family, seed, AT_NASH)
    g["game_id"] = f"espion_pilot__{family}__{condition}__s{seed}"
    g["mock"] = False
    g["models"] = {"0": f"{family}/m", "1": f"{family}/m"}
    return g


def run(tmp_path, deviations):
    logs = [game(f, c, s) for f in ("fa", "fb") for c in ("A", "E") for s in (1, 2)]
    write_logs(logs, tmp_path / "runs")
    argv = [str(tmp_path / "runs"), str(tmp_path / "out"), "--viz-dir", str(tmp_path / "viz")]
    if deviations is not None:
        (tmp_path / "dev.json").write_text(json.dumps(deviations), encoding="utf-8")
        argv += ["--deviations", str(tmp_path / "dev.json")]
    assert rep.main(argv) == 0
    s = json.loads((tmp_path / "out" / "summary.json").read_text(encoding="utf-8"))
    meta = json.loads((tmp_path / "viz" / "meta.json").read_text(encoding="utf-8"))
    return s, meta


def test_deviations_exclude_ids_and_export_gate_of_dropped_family(tmp_path):
    ids = [f"espion_pilot__fb__{c}__s{s}" for c in ("A", "E") for s in (1, 2)]
    s, meta = run(tmp_path, [{"excluded_game_ids": ids}])
    assert s["n_games"] == 4 and s["excluded"]["superseded"] == 4
    fb = meta["excluded_families"]["fb"]
    assert fb["n_games"] == 4 and fb["models"] == ["fb/m"]
    assert fb["e_validation"]["pass"] is False and fb["e_validation"]["n_E"] == 2
    assert set(meta["excluded_families"]) == {"fb"}


def test_no_deviations_no_excluded_families_key(tmp_path):
    s, meta = run(tmp_path, None)
    assert s["n_games"] == 8 and "excluded_families" not in meta
