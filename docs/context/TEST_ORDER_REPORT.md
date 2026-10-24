# TEST ORDER REPORT - was "tests first" respected in Phases 0 to 3?
Written 2026-10-24 from `git log` and `git diff` only. Nothing in the locked tests was modified to write this report.

## 1. Locked test commit vs first implementation commit
Times are the commit times of 2026-10-24 (+0800).

| Phase | Locked tests | First implementation | Order |
|---|---|---|---|
| 0 | none (scaffolding only) | 2a4469c 14:39:53 adds `harness/__init__.py` (a docstring) and `tests/test_smoke.py` in the SAME commit | Not tests first. The tests-first rule (D1) arrived after Phase 0. The only "code" is a package docstring, no logic |
| 1 | none (documents only, PREREGISTRATION.md) | none | Not applicable |
| 2 (R01-R11) | 5c52047 14:46:39 `test(R01-R11): add failing tests from spec (locked)`, 98 tests red, all `NotImplementedError` | 1fa981c 14:47:41 `feat(R01)` | Tests first. Skeletons (signatures + `raise NotImplementedError`) were committed with the tests; the only constants in skeletons were `BEHAVIORAL_GAP_FRACTION = 0.10`, `BEHAVIORAL_WINDOW = 3`, `CONDITIONS`, `VALID_RESPONSES` (taken from SPEC/PREREGISTRATION) |
| 3 (R12-R17, R22, R23, R27) | c5adce2 15:00:29 `test(R12-R17,R22-R23,R27): add failing tests from spec (locked)`, 80 new tests red (79 `NotImplementedError`, 1 assertion on a missing constant) | c3ddaad 15:04:10 `feat(R12)` | Tests first. Before the lock, skeletons got two empty exception classes (`RealRunRefused`, `MissingAPIKey`) so that 2 tests could not pass by accident on `NotImplementedError` (a `RuntimeError` subclass) |

No implementation commit precedes its locked test commit.
Before each lock, tests that passed without any implementation were rewritten (Phase 2: 4 tests, Phase 3: 3 tests) so that they need the real behavior. This happened BEFORE the lock, never after.

## 2. Test files changed since each lock
- `git diff 5c52047 HEAD --stat -- tests/`: only ADDED files (helpers3.py, test_R12_R17_pipeline.py, test_R13_R15_analysis.py, test_R22_R27_viz_export.py, test_gaps_phase0_3.py). The 7 Phase 2 files (helpers.py, conftest.py, test_R01 to test_R10_R11) are unchanged.
- `git diff c5adce2 HEAD --stat -- tests/`: `tests/test_R12_R17_pipeline.py | 2 +-` (one line) plus the added gap file. The line is the owner-approved fix (H4, D3, commit cef08e3): expected `invalid_responses` 1 -> 2.
- `tests/test_gaps_phase0_3.py` is a NEW file (commit after cef08e3), not a change to a locked file.

## 3. Coverage per requirement (count = collected tests whose name starts with the id)
Classes: covered = normal case + limit cases + a case that must fail or be rejected + a trap case. Partial = something missing (said). MANUAL = not automated by design.

| Req | Tests | Class | Notes |
|---|---|---|---|
| R01 | 12 | covered | normal (linear, logit), limits (second case, alpha scaling, equal prices), rejected (bad parameters, unknown type, bad rounds), trap (FOC check independent of the solver, published values). Cross-check vs luciasauer done (TRACEABILITY) |
| R02 | 10 + 1 + 2 gap | covered | normal, limits (spy_start 1, rounds around spy_start), rejected (spy_start < 1, gap test), trap (text not rewritten, no client, no network import) |
| R03 | 11 + 1 | covered | normal, rejected (unknown condition, missing text), trap (edited prereg file changes the text) |
| R04 | 2 | partial | label-only difference checked on placeholder and real texts. No negative case: both texts come from one shared template, so a non-label difference cannot be built without changing the code |
| R05 | 22 | covered | valid, normalized case/spaces, invalid mapped and counted, trap ("accepted", "I accept" not mapped to accept), JSON parsing |
| R06 | 8 | covered | normal, limits (spy_start - 1, last round, spy_start = 1, 0 rounds), trap (decline then accept) |
| R07 | 19 | covered | normal, limits (exactly 10% above and below, just inside, just outside), rejected (2 of 3 rounds, incomplete window, 0 and 1 round), traps (says yes but no move, silent but at deal, halfway price, window off by one in both directions) |
| R08 | 4 + 1 gap | covered | normal, negative, trap (accept in B is not a false positive), rate over D only; gap: accept before spy_start counts (literal frozen definition "any accept in D") |
| R09 | 4 | covered | trap (2 firms = 1 game), several games, per-firm secondary, empty list |
| R10 | 9 | covered | same seed, different seed, known rate 7/17, all 0, all 1, rejected (non A/D, empty, too short), p-value |
| R11 | 6 | covered | hand values (5/10, 0/10, 10/10, 1/1), independent formula, rejected inputs |
| R12 | 26 + 2 | covered | write once, overwrite trap, each missing field rejected, run_game log contents, invalid reply, skip existing, real-run guards, no key before network |
| R13 | 8 | covered | pass, exactly at threshold, just below, trap (pre-offer rounds ignored), per family, missing A or E, CLI |
| R14 | 2 + 2 gap | covered | schema and hand values (base rate 0.5), sorting; gaps: unknown condition rejected, no logs |
| R15 | 8 + 1 gap | covered | twice identical, checksums, deleted log, no key/no network, runs untouched, summary values, CLI, empty; gap: corrupted log stops reproduce |
| R16 | 6 | covered | family from id, mixed rejected, mislabel rejected, unknown condition, 60 games, seed passed |
| R17 | 3 + 2 gap | covered | cap inclusive, global stop (21 calls, 2 logs), cost per game; gap: cap <= 0 rejected |
| R18 | 0 | not covered | audit grep + review (AUDIT.md), no automated test |
| R19 | 0 | not covered | Phase 7 tool tools/check_submission.py, next in Bloc 6 |
| R20 | 0 | MANUAL | |
| R21 | 0 | MANUAL | |
| R22 | 9 | covered | five files, exact schemas, hand values on a 4-game mini-run, frozen texts, meta checksums, data.js, deterministic |
| R23 | 4 | covered | consistent, altered row, outcome mismatch, row count vs runs |
| R24 | 0 | not covered | Phase 8 (tools/check_viz.py) |
| R25 | 0 | not covered | Phase 8 (tools/make_demo_data.py) |
| R26 | 0 | MANUAL | |
| R27 | 3 | partial | PDF produced without key, same bytes twice, depends on games.csv. The colors and layout of the PDF are not checked automatically (visual review) |

## 4. Expected values: hand derivation present or not
Automatic scan of every test function (numeric literal in an assert, comment or docstring in or right above the function), 2026-10-24: 29 tests with a numeric expected value AND a derivation comment, 18 with a numeric expected value but no comment in the function itself, 102 without numeric expected values (structure, strings, exceptions).

The 18 tests with a number but no local comment, and where the number comes from:
- test_R01_deal_price_is_joint_monopoly_price, test_R01_make_demand_from_config, test_R01_game_config_from_dict: 4.0 and 5.5 = linear Nash and monopoly derived by hand in the comment above test_R01_linear_known_answer (same file).
- test_R07_definition_constants_match_preregistration: 0.10 and 3 = the frozen definition values in PREREGISTRATION.md.
- test_R09_two_firms_accepting_count_as_one_game, test_R09_behavioral_game_rate, test_R09_empty_list: counts of hand-built games (1/1, 1/2, 2/4, 0/0), readable from the logs built in the test.
- test_R10_same_seed_same_distribution: 200 = n_draws passed in the test.
- test_R11_wilson_k10_n10_symmetric: 1 - 0.277542, the 0/10 upper bound derived in test_R11_wilson_k0_n10 (symmetry).
- test_R05_parse_reply_valid_json, test_R05_parse_reply_json_inside_text: the number is the one written in the input JSON.
- test_R12_load_logs_sorted, test_R14_rows_sorted_one_per_game, test_R15_empty_runs_dir, test_R15_cli: counts of logs written in the test (2, 5, 0) or exit code 0.
- test_R13_other_conditions_ignored: 0.30 = (15 - 12) / 10, derived in test_R13_pass_when_effect_above_threshold.
- test_R22_games_csv_schema_and_values, test_R22_data_js_has_the_same_content: 10, 20, 5, 10 rounds, 4 games and outcomes from the mini-run table in the module docstring.
None of the expected values was copied from the code's output. The locked files are not edited to add comments (rule D1).

## 5. Gap tests added (separate commit, no locked file touched)
`tests/test_gaps_phase0_3.py` (commit "test(R02,R08,R14,R15,R17): add gap tests from test order report"): 8 tests. The R02 test was red first (spy accepted spy_start 0), then `feat(R02): reject spy_start below 1`. The other gap tests passed on existing code; each one was checked by a deliberate break (FP limited to rounds >= spy_start, unknown condition accepted, corrupted log skipped, cap 0 accepted): each break made exactly 1 gap test red, then the code was restored. Full suite after: 187 passed.
