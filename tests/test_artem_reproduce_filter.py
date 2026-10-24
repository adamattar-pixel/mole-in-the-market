"""R15 filter (audit pass 1-2, finding 3): the preregistered tables use only real games from the core
configs. Mock (dry) games and non-core configs (smoke) are excluded by default and counted, never dropped
silently. An explicit CLI option brings them back for diagnostics.

Signals (docs/team-artem/FIXES.md): `mock` is a required log field (harness/runlog.py) and is True for
dry runs; the config name is the game id prefix written by harness/runner.py::expand_games,
"<config name>__<family>__<condition>__s<seed>".
Prices as in test_R13_R15_analysis.py: Nash 10, deal 20, spy_start 5, 10 rounds.
"""
import csv
import json

import pytest

from helpers import responses_with
from helpers3 import full_log, write_logs
from tools import reproduce as rep

N = 10
AT_DEAL = [(10.0, 10.0) if r < 5 else (20.0, 20.0) for r in range(1, N + 1)]
AT_NASH = [(10.0, 10.0)] * N


def game(config, condition, seed, prices=AT_NASH, mock=False, responses=None):
    g = full_log(condition, "fx", seed, prices, responses)
    g["game_id"] = f"{config}__fx__{condition}__s{seed}"
    g["mock"] = mock
    return g


def real_runs():
    """Smoke A s1 (at deal), pilot A s1-s2 (at Nash), core B s1-s2, plus one mock core game B s3 (at deal)."""
    acc = responses_with(N, {5: ("accept", "accept")})
    return [
        game("espion_smoke", "A", 1, AT_DEAL),
        game("espion_pilot", "A", 1), game("espion_pilot", "A", 2),
        game("espion_core", "B", 1), game("espion_core", "B", 2),
        game("espion_core", "B", 3, AT_DEAL, mock=True, responses=acc),
    ]


def run_cli(tmp_path, *extra, logs=None):
    write_logs(real_runs() if logs is None else logs, tmp_path / "runs")
    assert rep.main([str(tmp_path / "runs"), str(tmp_path / "out"), *extra]) == 0
    return json.loads((tmp_path / "out" / "summary.json").read_text(encoding="utf-8"))


def test_R15_filter_cli_default_excludes_mock_and_smoke(tmp_path):
    s = run_cli(tmp_path)
    # kept: pilot A s1, s2 and core B s1, s2
    assert s["n_games"] == 4
    assert s["rates"]["fx"]["A"]["n"] == 2  # seed 1 counted once (pilot only), not smoke + pilot
    assert s["rates"]["fx"]["B"]["n"] == 2
    # the mock B game was accept + at deal: excluding it leaves say 0/2, do 0/2
    assert (s["rates"]["fx"]["B"]["say"]["k"], s["rates"]["fx"]["B"]["do"]["k"]) == (0, 0)


def test_R15_filter_reports_excluded_counts(tmp_path):
    s = run_cli(tmp_path)
    assert s["excluded"] == {"mock": 1, "non_core_config": {"espion_smoke": 1}}
    assert s["included_configs"] == {"espion_core": 2, "espion_pilot": 2}
    tables = (tmp_path / "out" / "tables.md").read_text(encoding="utf-8")
    assert "Excluded games: 2 (mock 1, non-core config espion_smoke 1)" in tables


def test_R15_filter_labels_only_kept_games(tmp_path):
    run_cli(tmp_path)
    with (tmp_path / "out" / "labels.csv").open(encoding="utf-8", newline="") as fh:
        ids = sorted(r["game_id"] for r in csv.DictReader(fh))
    assert ids == ["espion_core__fx__B__s1", "espion_core__fx__B__s2",
                   "espion_pilot__fx__A__s1", "espion_pilot__fx__A__s2"]


def test_R15_filter_all_configs_option_brings_smoke_back(tmp_path):
    s = run_cli(tmp_path, "--all-configs")
    assert s["rates"]["fx"]["A"]["n"] == 3
    assert s["excluded"] == {"mock": 1, "non_core_config": {}}


def test_R15_filter_include_mock_option_brings_mock_back(tmp_path):
    s = run_cli(tmp_path, "--include-mock")
    assert s["rates"]["fx"]["B"]["n"] == 3
    assert (s["rates"]["fx"]["B"]["say"]["k"], s["rates"]["fx"]["B"]["do"]["k"]) == (1, 1)
    assert s["excluded"] == {"mock": 0, "non_core_config": {"espion_smoke": 1}}


def test_R15_filter_explicit_configs_option(tmp_path):
    s = run_cli(tmp_path, "--configs", "espion_smoke")
    assert s["n_games"] == 1 and s["rates"]["fx"]["A"]["n"] == 1
    assert s["excluded"] == {"mock": 1, "non_core_config": {"espion_core": 2, "espion_pilot": 2}}


def test_R15_filter_missing_mock_field_or_unknown_config_is_excluded(tmp_path):
    no_flag = game("espion_core", "B", 4)
    del no_flag["mock"]
    no_prefix = full_log("B", "fx", 5, AT_NASH)  # game id "syn__..." -> config "syn"
    no_prefix["mock"] = False
    s = run_cli(tmp_path, logs=[game("espion_core", "B", 1), no_flag, no_prefix])
    assert s["n_games"] == 1
    assert s["excluded"] == {"mock": 1, "non_core_config": {"syn": 1}}


def test_R15_filter_function_api(tmp_path):
    write_logs(real_runs(), tmp_path / "runs")
    s = rep.reproduce(tmp_path / "runs", tmp_path / "out", configs=("espion_core",), include_mock=False)
    assert s["n_games"] == 2
    assert s["excluded"] == {"mock": 1, "non_core_config": {"espion_pilot": 2, "espion_smoke": 1}}


def test_R15_filter_default_core_configs_are_pilot_and_core():
    # Preregistered 60 games: A and E come from espion_pilot, B, B_T, C, D from espion_core.
    assert tuple(sorted(rep.PREREG_CONFIGS)) == ("espion_core", "espion_pilot")


def test_R15_filter_viz_export_consistent_with_exclusions(tmp_path):
    write_logs(real_runs(), tmp_path / "runs")
    assert rep.main([str(tmp_path / "runs"), str(tmp_path / "out"), "--viz-dir", str(tmp_path / "viz")]) == 0
    with (tmp_path / "viz" / "games.csv").open(encoding="utf-8", newline="") as fh:
        assert len(list(csv.DictReader(fh))) == 4


def test_R15_filter_checksums_still_cover_every_input_file(tmp_path):
    run_cli(tmp_path)
    lines = (tmp_path / "out" / "checksums.txt").read_text(encoding="utf-8")
    for g in real_runs():
        assert f"runs/{g['game_id']}.json" in lines


@pytest.mark.parametrize("extra", [(), ("--all-configs", "--include-mock")])
def test_R15_filter_run_twice_identical(tmp_path, extra):
    write_logs(real_runs(), tmp_path / "runs")
    for out in ("o1", "o2"):
        assert rep.main([str(tmp_path / "runs"), str(tmp_path / out), *extra]) == 0
    read = lambda d: {p.name: p.read_bytes() for p in sorted((tmp_path / d).iterdir())}
    assert read("o1") == read("o2")
