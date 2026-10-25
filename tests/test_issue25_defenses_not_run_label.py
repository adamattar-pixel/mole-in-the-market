"""OPEN_ISSUES #25: results/defenses.md showed "Collusion removed: 0" for the monitor and no "not run" mark,
although no monitor or ethics game was ever run (credit cap, ops/STATE.md). An empty cell must read as
"not run", never as zero. The JSON values (asserted by the locked R31-R35 tests) do not change.
"""
from helpers3 import full_log
from tools.score_defenses import score_defenses, tables_md


def flat(pre, post, n=10, spy=5):
    return [(pre, pre) if r < spy else (post, post) for r in range(1, n + 1)]


def core_only_logs():
    # core B, C, D games only: no B_MON, C_MON, D_MON, B_ETH game -> monitor and ethics were not run
    return [full_log(c, "fx", 1, flat(10.0, 20.0)) for c in ("B", "C", "D")]


def test_issue25_not_run_banner_and_na_cells():
    md = tables_md(score_defenses(core_only_logs()))
    assert "NOT RUN" in md
    rows = [l for l in md.splitlines() if l.startswith("| B |") or l.startswith("| C |") or l.startswith("| D |")]
    assert rows
    # last cell = collusion removed: n/a when there is no matched pair, never 0
    assert all(r.rstrip(" |").split("|")[-1].strip() == "n/a" for r in rows)


def test_issue25_json_values_unchanged():
    s = score_defenses(core_only_logs())
    assert s["all"]["monitor"]["B"]["collusion_removed"] == 0 and s["all"]["monitor"]["B"]["n_pairs"] == 0
