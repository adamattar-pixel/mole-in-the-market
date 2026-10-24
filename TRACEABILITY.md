# TRACEABILITY - requirement to test to evidence
Claude updates this file at every gate. Status: TODO, RED (test written, failing), GREEN (passing), MANUAL.

| Req | Test (file::name) | Status | Evidence (command and date) |
|---|---|---|---|
| R01 | tests/test_R01_economics.py (12 tests: linear closed form, logit FOC, published values, alpha scaling, config). Cross-check vs luciasauer/algorithmic_pricing_llms (MIT, cloned read-only outside the repo, 2026-10-24, no code copied): duopoly.py uses env a=2.0, c=1.0, alpha in {1, 3.2, 10}; src/environment/pricing_market_logic_multiproduct.py uses the same logit (delta_i = (a_i - p_i/alpha)/mu, outside option a0/mu, multiplier beta; nested sigma=0 reduces to ours) and defaults a0=0, mu=0.25, beta=100 = ours. Difference: their profit is q*(p/alpha - c), ours (p - alpha*c)*q = alpha * theirs, so Nash and monopoly prices are identical, profit levels differ by the factor alpha when alpha != 1 (PROPOSED design uses alpha=1). Their benchmarks were not executed | GREEN | `python -m pytest` 99 passed, 2026-10-24, locked at 5c52047 |
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
| R12 | tests/test_R12_R17_pipeline.py::test_R12_* (26 incl. parametrized missing fields, write-once, run_game log, real-run guards) + test_R02_R12_*, test_R03_R12_* | GREEN | `python -m pytest` 179 passed, 2026-10-24, locked at c5adce2 (+ approved test(fix) cef08e3) |
| R13 | tests/test_R13_R15_analysis.py::test_R13_* (8: pass, boundary 0.25, just below, pre-offer trap, per family, CLI) | GREEN | `python -m pytest` 179 passed, 2026-10-24, locked at c5adce2 (+ approved test(fix) cef08e3) |
| R14 | tests/test_R13_R15_analysis.py::test_R14_* (2: schema and hand values incl. base rate 0.5) | GREEN | `python -m pytest` 179 passed, 2026-10-24, locked at c5adce2 (+ approved test(fix) cef08e3) |
| R15 | tests/test_R13_R15_analysis.py::test_R15_* (8: twice identical, checksums, deleted log, no key no network, runs untouched, summary values, CLI, empty) | GREEN | `python -m pytest` 179 passed, 2026-10-24, locked at c5adce2 (+ approved test(fix) cef08e3) |
| R16 | tests/test_R12_R17_pipeline.py::test_R16_* (6: family from id, mixed rejected, mislabel rejected, unknown condition, 60 games, seed passed) | GREEN | `python -m pytest` 179 passed, 2026-10-24, locked at c5adce2 (+ approved test(fix) cef08e3) |
| R17 | tests/test_R12_R17_pipeline.py::test_R17_* (3: tracker cap inclusive, global stop after 21 calls, cost per game) | GREEN | `python -m pytest` 179 passed, 2026-10-24, locked at c5adce2 (+ approved test(fix) cef08e3) |
| R18 | audit grep | TODO | |
| R19 | tests/test_R19_check_submission.py (20: word rules, 150 vs 151, abstract boundaries, LaTeX, exact appendix heading, body-text trap, authors, title, links with injected fetcher, offline NOT RUN, local links, CLI) + MANUAL page count | GREEN | `python -m pytest` 254 passed, 2026-10-24, locked at a0cd120 |
| R20 | MANUAL | TODO | |
| R21 | MANUAL | TODO | |
| R22 | tests/test_R22_R27_viz_export.py::test_R22_* (9: five files, schemas, hand values on 4-game mini-run, frozen texts, meta, data.js, deterministic) | GREEN | `python -m pytest` 179 passed, 2026-10-24, locked at c5adce2 (+ approved test(fix) cef08e3) |
| R23 | tests/test_R22_R27_viz_export.py::test_R23_* (4: consistent, altered row, outcome mismatch, row count vs runs) | GREEN | `python -m pytest` 179 passed, 2026-10-24, locked at c5adce2 (+ approved test(fix) cef08e3) |
| R24 | tests/test_R24_R25_viz_page.py::test_R24_* (tools/check_viz.py on hand-built pages and on viz/) + MANUAL review (headless Chrome screenshot inspected 2026-10-24) | GREEN (phase cut, D17) | locked at ef5bccd |
| R25 | tests/test_R24_R25_viz_page.py::test_R25_* (synthetic flag, never touches runs/ or labels, refuses real locations, schema, frozen texts, deterministic) | GREEN (phase cut, D17) | locked at ef5bccd |
| R26 | MANUAL | TODO | |
| R27 | tests/test_R22_R27_viz_export.py::test_R27_* (3: PDF without key/network, two runs same bytes, depends on games.csv) | GREEN | `python -m pytest` 179 passed, 2026-10-24, locked at c5adce2 (+ approved test(fix) cef08e3) |
| R28 | | TODO | |
| R29 | | TODO | |
| R30 | | TODO | |
| R31 | | TODO | |
| R32 | | TODO | |
| R33 | | TODO | |
| R34 | | TODO | |
| R35 | | TODO | |
| R36 | | TODO | |

Phase 4 no-API tests (configs, dry run, budget, cost per game, tbd guard): tests/test_P4_configs_dryrun.py, 22 tests, GREEN, locked at 87c3b7f. R28-R36: TODO (not started in code).
