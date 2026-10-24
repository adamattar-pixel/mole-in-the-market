"""Review M4 (docs/team-artem/REVIEW_ARTEM_DIFF.md), R30: reproduce writes the monitor and ethics tables
(defenses.json, defenses.md) from runs/, with their checksums, deterministically.

Logs come from run_all with the R36 test double (2 families x 5 seeds). Hand values, as in
test_R36_scoring_outputs: B pairs with B_MON on 10 (family, seed) keys, the frozen B text matches the pact
rule so all 10 are blocked, D_MON has 10 games and 0 false blocks, and B, B_ETH, B_MON form 10 full triples.
"""
import hashlib
import json

import pytest

from test_R36_run_all import FakeReal, no_network, run  # noqa: F401

FILES = ("defenses.json", "defenses.md")


@pytest.fixture
def runs(tmp_path):
    res, _ = run(tmp_path, FakeReal(), stop_after="ethics")
    assert res["status"] == "stopped"
    return tmp_path / "root" / "runs"


def check_values(out):
    d = json.loads((out / "defenses.json").read_text())["all"]
    assert d["monitor"]["B"]["n_pairs"] == 10 and d["monitor"]["B"]["blocked"]["k"] == 10
    assert d["monitor"]["false_blocks"]["k"] == 0 and d["monitor"]["false_blocks"]["n"] == 10
    assert d["comparison"]["n_matched"] == 10
    assert "EXPLORATORY" in (out / "defenses.md").read_text()


def test_M4_reproduce_writes_defenses(runs, tmp_path):
    from tools.reproduce import PREREG_CONFIGS, reproduce
    out = tmp_path / "out"
    reproduce(runs, out, n_draws=20, configs=PREREG_CONFIGS, include_mock=False)
    check_values(out)


def test_M4_cli_writes_defenses(runs, tmp_path):
    from tools.reproduce import main
    assert main([str(runs), str(tmp_path / "cli"), "--n-draws", "20"]) == 0
    check_values(tmp_path / "cli")


def test_M4_checksums_cover_defenses(runs, tmp_path):
    from tools.reproduce import reproduce
    out = tmp_path / "out"
    reproduce(runs, out, n_draws=20, include_mock=False)
    lines = (out / "checksums.txt").read_text().splitlines()
    for n in FILES:
        assert f"{hashlib.sha256((out / n).read_bytes()).hexdigest()}  out/{n}" in lines, n


def test_M4_defenses_deterministic(runs, tmp_path):
    from tools.reproduce import reproduce
    snaps = []
    for name in ("a", "b"):
        reproduce(runs, tmp_path / name, n_draws=20, include_mock=False)
        snaps.append({n: (tmp_path / name / n).read_bytes() for n in FILES + ("checksums.txt",)})
    assert snaps[0] == snaps[1]


def test_M4_run_all_results_checksums_cover_defenses(tmp_path):
    res, _ = run(tmp_path, FakeReal())
    assert res["status"] == "done"
    out = tmp_path / "root" / "results"
    lines = (out / "checksums.txt").read_text().splitlines()
    for n in FILES:
        assert f"{hashlib.sha256((out / n).read_bytes()).hexdigest()}  out/{n}" in lines, n
