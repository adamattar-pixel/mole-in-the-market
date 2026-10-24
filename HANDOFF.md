# HANDOFF - Claude (wip/phase-4) to Artem (branch `artem`)
Date: 2026-10-24. Tag of this checkpoint: `handoff-artem-1` (the commit that adds this file, on `wip/phase-4`).

## 1. Exact state
- Branch `wip/phase-4`, checkpoint commit = tag `handoff-artem-1`. Last code-green commit before the docs: 378f1dd.
- `python -m pytest`: **254 passed, 0 failed**. No red locked-test commit is kept local: every locked test commit below is implemented and green.
- `main` = gate-3 + preregistration freeze (tag `prereg-frozen`). Everything after that is on `wip/phase-4` only.

### Done (tests green)
- Phases 0-3: R01-R17, R22, R23, R27 (game, spy, conditions, say/do definitions, base rate, Wilson, write-once logs, budget stop, runner, E validation, labels.csv, `reproduce`, viz export, game grid figure).
- Gap tests for phases 0-3 (docs/context/TEST_ORDER_REPORT.md).
- Preregistration FROZEN (d5e7ebc, hash in e95853a, tag `prereg-frozen`).
- Phase 4 without API: configs `espion_dry|smoke|pilot|core.yaml`, dry mock client, `tools/run.py`, cost per game, guards (mock never writes to runs/, real run refused while model ids contain `tbd`).
- R19 `tools/check_submission.py`.
- R24-R25 replay page + demo data (Phase 8 is now CUT, D17: code kept, no more work).
- Plan, SPEC "Post-freeze additions" R28-R36, DECISIONS D16-D21, QUESTIONS #12.
- PREREGISTRATION_ADDENDUM.md written and FROZEN (8b7b5a1, hash in 378f1dd, tag `addendum-frozen`), see section 7.

### Half done
- Phase 4 gate: OPEN. It needs the real smoke and pilot runs (hard stop H2: API key, GO, and the 2 model families that replace the `tbd` placeholders in configs).
- R28-R36: SPEC text and addendum exist, NO code and NO tests in the repo. A draft test file was written by Claude but NOT committed (moved out of the repo); the detector part is reserved for Artem.

### Not started
- R28-R30 detectors and scoring (Artem). R31-R36 monitor, B_ETH, defenses comparison, addendum guard, `tools/run_all`, RUNBOOK_REAL_RUNS.md (Claude). Report skeleton (D21). README/THIRD_PARTY idea credits update. Optional mixed families and O1.

## 2. Ownership and conflict rules
| Owner | Files |
|---|---|
| Claude, branch `wip/phase-4` | harness/ (existing modules), tools/reproduce.py, tools/validate_e.py, tools/run_all (future), tools/run.py, tools/check_submission.py, tools/check_viz.py, tools/make_demo_data.py, configs/, all existing tests, PREREGISTRATION_ADDENDUM.md, RUNBOOK_REAL_RUNS.md (future) |
| Artem, branch `artem` (NEW files only) | harness/detectors.py, tools/score_detectors.py, tests/test_detectors*.py, docs/artem/ (including docs/artem/DETECTORS_SPEC.md), PROGRESS_ARTEM.md |
| Shared docs, edited only by Claude on `wip/phase-4` | PROGRESS.md, TRACEABILITY.md, SPEC.md, PLAN.md, README.md, THIRD_PARTY.md |

- Artem logs in PROGRESS_ARTEM.md and docs/artem/; he requests shared-doc changes in this file (section 8) or in QUESTIONS.md.
- Nobody edits another owner's files. Wiring the detectors into tools/reproduce.py happens only after `artem` is merged, by the owner.
- No force push. No rebase of pushed branches. Only the owner merges.
- Commits under your own git identity (author = committer = you), no AI trailer, no secrets (CONTRIBUTING.md).

## 3. Frozen items: nobody edits them
- PREREGISTRATION.md (frozen at d5e7ebc, tag `prereg-frozen`). Any change = hard stop H6, owner only.
- PREREGISTRATION_ADDENDUM.md (frozen at 8b7b5a1, tag `addendum-frozen`). Changes only through its "Deviations" section with the owner's approval.
- Locked test commits (rule D1: never edited to pass; a gap = a new test in a separate commit): 5c52047 (R01-R11), c5adce2 (R12-R17, R22, R23, R27) + owner-approved fix cef08e3, 87c3b7f (Phase 4), a0cd120 (R19), ef5bccd (R24-R25). Gap tests: fc7ebeb.
- Rule D1 applies to Artem too: write tests/test_detectors*.py first from the spec, show them red, commit `test(R28-R29): add failing tests from spec (locked)`, then implement.

## 4. Commands
```
pip install -r requirements.txt
python -m pytest                                   # expect 254 passed at handoff-artem-1
python -m tools.reproduce runs results --viz-dir viz/data --figures-dir figures   # tables from runs/, no key
python -m tools.validate_e runs                    # E PASS/FAIL per family
python -m tools.run configs/espion_dry.yaml        # dry run with the mock client, writes dry_runs/ (never runs/)
python -m tools.check_submission report/<file>.md --title "<exact title>" --offline
```

## 5. Open questions and defaults taken
| # | Question | Default taken |
|---|---|---|
| 7 | Which 2 model families | `tbd` placeholders; real runs refused until the owner gives them |
| 10 | Invalid price in a reply | previous price kept (Nash in round 1), counted in the log |
| 11 | Budget caps | smoke 1, pilot 5, core 10 USD |
| 12 | Report prose vs D14 | skeleton with notes and [RESULT: ...] placeholders, no finished prose |
| 13 | Addendum already frozen with D1-D3 definitions, while docs/artem/DETECTORS_SPEC.md is planned | the frozen addendum stands; Artem implements its definitions; any different definition goes to the addendum "Deviations" section and needs the owner's approval before any real run |

## 6. Next actions
Artem, in order:
1. `git fetch && git checkout -b artem origin/wip/phase-4` (from tag `handoff-artem-1`), `pip install -r requirements.txt`, `python -m pytest` (254 passed).
2. Read SPEC.md R28-R30 and PREREGISTRATION_ADDENDUM.md (detector definitions D1 price level, D2 message, D3 action dependence, thresholds, scoring truth). Write docs/artem/DETECTORS_SPEC.md (copy of those definitions plus your test plan).
3. Tests first: tests/test_detectors*.py with hand-built logs (helpers in tests/helpers.py and tests/helpers3.py), boundary cases at each threshold, traps (hint text not caught by D2, same-round moves not counted by D3). Lock, then implement harness/detectors.py and tools/score_detectors.py.
4. Log progress in PROGRESS_ARTEM.md. Do not touch tools/reproduce.py (wiring after merge).

Claude (wip/phase-4), in order:
1. R31-R32 monitor (B_MON, C_MON, D_MON, matched episodes, false blocks on D), then R33-R34 B_ETH and defenses comparison, then R35 addendum guard, then R36 tools/run_all and RUNBOOK_REAL_RUNS.md. Tests first for each.
2. Report skeleton (D21), README and THIRD_PARTY idea credits.
3. After the owner merges `artem`: wire detector tables into tools/reproduce.py (R30).

## 7. Post-freeze addendum plan (parts A, B, C, D)
- A detectors (R28-R30, never cut): Artem writes harness/detectors.py, tools/score_detectors.py and their tests; Claude wires them into reproduce after the merge.
- B rule monitor, matched episodes (R31-R32): Claude.
- C ethics condition B_ETH and defenses comparison (R33-R34): Claude.
- D mixed family pairs (optional, config only): Claude, only if everything else is done.
- PREREGISTRATION_ADDENDUM.md holds the frozen texts and thresholds of A, B, C. It is already committed and frozen (tag `addendum-frozen`) and MUST stay frozen before any real run of these parts. Real runs also need the owner's GO and key (H2).

## 8. Requests for shared-doc changes (Artem writes here)
(none yet)
