# HANDOFF - full handoff: Artem is the project owner
Date: 2026-10-24. First checkpoint tag: `handoff-artem-1` (kept). Full ownership transfer: commit "docs: handoff ownership to Artem" on `wip/phase-4`.
Artem owns the project from now on. Adam Attar (adamattar-pixel) stays co-author and is reachable for decisions.

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

## 2. Ownership
- **Artem owns ALL files and ALL remaining work**: R28-R30 detectors and scoring, R31-R36 (monitor, B_ETH, defenses comparison, addendum guard, tools/run_all), RUNBOOK_REAL_RUNS.md, the report, the Phase 4 real runs, O1.
- His Claude Code may edit any file that is not frozen (section 3) and may work directly on `wip/phase-4`. No separate `artem` branch is needed.
- Hard stops H1 to H6 (CLAUDE.md) now go to Artem.
- Each contributor commits under their own name and email. No Co-Authored-By or other AI trailer, no secrets, no force push on shared branches, no rebase of pushed branches.
- Adam Attar (adamattar-pixel): co-author, reachable for decisions.

## 3. Frozen items: nobody edits them
Any change to a frozen item must be logged in QUESTIONS.md and reported as a deviation (in the "Deviations" section of the frozen file, with the owner's approval, and in the report). Hard stop H6 still applies.
- PREREGISTRATION.md (frozen at d5e7ebc, tag `prereg-frozen`). Any change = hard stop H6, owner only.
- PREREGISTRATION_ADDENDUM.md (frozen at 8b7b5a1, tag `addendum-frozen`). Changes only through its "Deviations" section with the owner's approval.
- Locked test commits (rule D1: never edited to pass; a gap = a new test in a separate commit): 5c52047 (R01-R11), c5adce2 (R12-R17, R22, R23, R27) + owner-approved fix cef08e3, 87c3b7f (Phase 4), a0cd120 (R19), ef5bccd (R24-R25). Gap tests: fc7ebeb.
- Rule D1 applies to every contributor: write tests/test_detectors*.py first from the spec, show them red, commit `test(R28-R29): add failing tests from spec (locked)`, then implement.

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
| 13 | Addendum already frozen with the D1-D3 detector definitions | the frozen addendum stands; detectors implement its definitions; any different definition is logged in QUESTIONS.md and goes to the addendum "Deviations" section before any real run |

## 6. Open decisions for Artem
1. The 2 model families (D10): OpenRouter model ids replacing the `tbd` placeholders in configs/espion_smoke|pilot|core.yaml (and in any new config).
2. The OpenRouter API key: set it as the environment variable OPENROUTER_API_KEY on your machine; never commit it.
3. GO for the first real run (espion_smoke, then espion_pilot on A and E, then the E gate).
4. Runs freeze: Sunday Oct 25 at noon (proposal in PLAN.md).
5. Submission: early Sunday, before 23:59 AoE (Monday 11:59 UTC), same title on every resubmission.
6. Open QUESTIONS.md rows #10-#13 (defaults already taken, see section 5).

## 6b. Next actions for Artem, in order
1. `git fetch && git checkout wip/phase-4 && git pull`, `pip install -r requirements.txt`, `python -m pytest` (expect 254 passed).
2. Decide items 1-3 above; put the real model ids in the configs (tests first if you add checks).
3. Real smoke and pilot (A, E) with `python -m tools.run configs/espion_smoke.yaml` then `configs/espion_pilot.yaml`; check the cost per game; `python -m tools.validate_e runs` (E gate: if E fails, change model once, else plan B, v7 section 10).
4. Core runs `python -m tools.run configs/espion_core.yaml`, then `python -m tools.reproduce runs results --viz-dir viz/data --figures-dir figures`.
5. R28-R30 detectors (never cut), then R31-R36, tools/run_all, RUNBOOK_REAL_RUNS.md, tests first for each (rule D1).
6. Report on the official template (report/AUTHORS.md has the author block), numbers only from `reproduce`, then `python -m tools.check_submission`.

## 7. Post-freeze addendum plan (parts A, B, C, D)
- A detectors (R28-R30, never cut): Artem (harness/detectors.py, tools/score_detectors.py, tests, wiring into tools/reproduce.py).
- B rule monitor, matched episodes (R31-R32): Artem.
- C ethics condition B_ETH and defenses comparison (R33-R34): Artem.
- D mixed family pairs (optional, config only): Artem, only if everything else is done.
- PREREGISTRATION_ADDENDUM.md holds the frozen texts and thresholds of A, B, C. It is already committed and frozen (tag `addendum-frozen`) and MUST stay frozen before any real run of these parts. Real runs also need the owner's GO and key (H2).

