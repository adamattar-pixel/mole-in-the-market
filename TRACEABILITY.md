# TRACEABILITY - requirement to test to evidence
Claude updates this file at every gate. Status: TODO, RED (test written, failing), GREEN (passing), MANUAL.

| Req | Test (file::name) | Status | Evidence (command and date) |
|---|---|---|---|
| R01 | tests/test_R01_economics.py (12 tests: linear closed form, logit FOC, published values, alpha scaling, config). Cross-check vs luciasauer duopoly.py: not run (repo not available, QUESTIONS #8) | GREEN | `python -m pytest` 99 passed, 2026-10-24, locked at 5c52047 |
| R02 | tests/test_R02_spy.py (8 tests) | GREEN | `python -m pytest` 99 passed, 2026-10-24, locked at 5c52047 |
| R03 | tests/test_R03_R04_conditions.py::test_R03_* (10 tests) | GREEN | `python -m pytest` 99 passed, 2026-10-24, locked at 5c52047 |
| R04 | tests/test_R03_R04_conditions.py::test_R04_placeholder_B_BT_differ_only_by_label, test_R04_real_prereg_B_BT_differ_only_by_label | GREEN | `python -m pytest` 99 passed, 2026-10-24, locked at 5c52047 |
| R05 | tests/test_R05_response.py (15 cases) | GREEN | `python -m pytest` 99 passed, 2026-10-24, locked at 5c52047 |
| R06 | tests/test_R06_R09_definitions.py::test_R06_* (8 tests) | GREEN | `python -m pytest` 99 passed, 2026-10-24, locked at 5c52047 |
| R07 | tests/test_R06_R09_definitions.py::test_R07_* (18 tests incl. boundaries, traps, off-by-one window) | GREEN | `python -m pytest` 99 passed, 2026-10-24, locked at 5c52047 |
| R08 | tests/test_R06_R09_definitions.py::test_R08_* (4 tests) | GREEN | `python -m pytest` 99 passed, 2026-10-24, locked at 5c52047 |
| R09 | tests/test_R06_R09_definitions.py::test_R09_* (4 tests) | GREEN | `python -m pytest` 99 passed, 2026-10-24, locked at 5c52047 |
| R10 | tests/test_R10_R11_stats.py::test_R10_* (9 tests incl. known rate 7/17) | GREEN | `python -m pytest` 99 passed, 2026-10-24, locked at 5c52047 |
| R11 | tests/test_R10_R11_stats.py::test_R11_* (6 tests, hand-computed values) | GREEN | `python -m pytest` 99 passed, 2026-10-24, locked at 5c52047 |
| R12 | | TODO | |
| R13 | | TODO | |
| R14 | | TODO | |
| R15 | | TODO | |
| R16 | | TODO | |
| R17 | | TODO | |
| R18 | audit grep | TODO | |
| R19 | tools/check_submission.py | TODO | |
| R20 | MANUAL | TODO | |
| R21 | MANUAL | TODO | |
| R22 | | TODO | |
| R23 | | TODO | |
| R24 | tools/check_viz.py + MANUAL | TODO | |
| R25 | | TODO | |
| R26 | MANUAL | TODO | |
| R27 | | TODO | |
