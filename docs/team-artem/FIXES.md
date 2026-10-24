# Fixes (team Artem)

## R15: reproduce excludes mock and non-core games, reports exclusions

- Audit: docs/team-artem/AUDIT_PASS_1_2.md, finding 3 (MAJOR).
- Problem: `python -m tools.reproduce` pooled every log in the runs folder. Smoke (A and E, seed 1) and
  pilot (A and E, seeds 1-5) both write to `runs/`, so A and E got n=6 per family with seed 1 counted
  twice. It also never checked the `mock` field, so dry-run logs in the folder would reach the tables.
- Signals used (no new log field):
  - Mock: the `mock` field, already a required log field (`harness/runlog.py::REQUIRED_FIELDS`) and set
    from the config by the runner, whose guards tie it to the client type. A log without `mock: false`
    counts as mock (conservative).
  - Config: the game id prefix. `harness/runner.py::expand_games` writes
    `<config name>__<family>__<condition>__s<seed>`, so `game_id.split("__")[0]` is the config name.
- Change (`tools/reproduce.py`, `harness/vizexport.py`):
  - `PREREG_CONFIGS = ("espion_pilot", "espion_core")`: the preregistered 60 games are A and E from the
    pilot plus B, B_T, C, D from the core. Smoke is excluded by default.
  - CLI default keeps only real games from those configs. Diagnostics: `--all-configs`,
    `--include-mock`, or `--configs a,b`.
  - `summary.json` gets `excluded` (`mock` count, `non_core_config` counts per config name) and
    `included_configs`; `tables.md` prints an "Excluded games: ..." line; the CLI prints both counts.
  - `checksums.txt` still lists every input file, excluded or not.
  - `check_consistency` takes `n_excluded` so the R23 row-count check compares against runs/ minus the
    excluded games.
  - The Python function `reproduce()` keeps its old default (no filter) so the locked R15/R22/R23 tests,
    which use mock synthetic logs, are unchanged. Only the CLI (what the report uses) filters by default.
- Doc follow-up: the memory-arm commands in MEMORY_ARM.md now pass `--configs espion_mem` (and
  `--configs espion_mem_dry --include-mock` for the dry run), otherwise they would report 0 games.
- Evidence:
  - Locked tests: `tests/test_artem_reproduce_filter.py` (13 tests), commit
    `test(R15-filter): add failing tests (locked)`: 11 red before the fix (2 are regression guards that
    already passed: checksums cover every input, run twice identical).
  - After the fix: `python3 -m pytest -q` -> 254 passed, 21 failed + 4 errors, all in
    `tests/test_R24_R25_viz_page.py` (locked phase 8, unchanged from baseline).
  - Mutations (each restored): filter result ignored -> 7 red; mock check off -> 8 red; missing `mock`
    treated as real -> 1 red; config check off -> 8 red; smoke added to PREREG_CONFIGS -> 6 red.
  - Dry run (`configs/espion_dry.yaml`, mock, no key): default reproduce -> 0 games, "Excluded games: 24
    (mock 24)"; with `--all-configs --include-mock --viz-dir` -> 24 games, viz consistency check passes.
