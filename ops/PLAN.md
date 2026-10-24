# PLAN - phases and gates
Claude works in autonomous mode: it passes each gate by itself when all evidence is green (see CLAUDE.md), logs it in PROGRESS.md, and moves on. It stops only at the hard stops H1 to H6 in CLAUDE.md. Hard stops that are certain: owner approval of the preregistration freeze (before Phase 4) and the owner's GO plus API key before the first real run (Phase 4).
Times are a proposal for Saturday Oct 24 and Sunday Oct 25 (deadline Sunday 11:59 PM AoE). Runs freeze Sunday at noon (to confirm).

| Phase | Content | Gate (evidence required) | Status |
|---|---|---|---|
| 0 | Scaffolding, baseline import of existing harness, `preexisting-baseline` tag, test runner works | Tests of the baseline run, `git log -1 --format=fuller` shows the owner's identity and no trailer | CURRENT |
| 1 | Complete and freeze PREREGISTRATION.md (texts, E threshold, hypotheses). Owner approves | Freeze commit, hash written in PREREGISTRATION.md, tag `prereg-frozen` | |
| 2 | Core logic with tests on a mock model: R01 to R11 | All tests green, TRACEABILITY.md filled, audit pass 1 (fresh session) | |
| 3 | Pipeline: logs, labels, `reproduce`, cost cap: R12 to R17, plus viz export R22, R23 and report figure R27 (cheap, the report figure depends on them) | `reproduce` deterministic on mock data, audit pass 2 | |
| 4 | Real smoke and pilot on A and E only (espion_smoke, espion_pilot). Measure real cost per game | Cost per game measured. E validation (R13): if E shows no collusion, change model once, otherwise plan B | |
| 5 | Core runs B, B_T, C, D (5 seeds, 2 families), base rate on A and D | Logs saved, `reproduce` regenerates the tables, audit pass 3 | |
| 6 | Options O1 then O2 then O3, each behind its own gate | Core finished and saved | |
| 7 | Report on the official Apart template, abstract, appendix, submission checks (R19 to R21), repo public | Audit pass 4, checklist in docs/apart/README.md, submit early Sunday | |
| 8 | CUT (D17). Code and tests already written are kept, no further work. OPTIONAL visual replay page (R24 to R26), design in docs/viz/DESIGN.md. Tests first: tools/check_viz.py and data tests before the HTML | Entry: Phase 3 green; wiring to real data only after Phases 4 and 5 (decision D13). Until then the page runs on demo data only (viz/demo/, DEMO DATA banner). Never blocks Phase 7. Time cap: if not done by Sunday 4:00 PM (owner local time, to confirm), cut it and keep only figure R27 | |

Cut order: the Phase 8 page is cut before any option O1 to O3.

## Post-freeze additions (D16-D21), exploratory
| Step | Content | Gate |
|---|---|---|
| A1 | PREREGISTRATION_ADDENDUM.md (monitor rule, ethics sentence, detector definitions and thresholds, hypotheses H5-H7), committed, hash recorded, tag addendum-frozen | Before any real run of A, B, C |
| A2 | Detectors D1, D2, D3 and scoring (R28-R30), wired into reproduce. Never cut | Tests green, mutation checks |
| A3 | Rule monitor, matched episodes B/C, cost on D (R31-R32) | Tests green |
| A4 | Ethics condition B_ETH and defenses comparison (R33-R34) | Tests green |
| A5 | Run guards and tools/run_all, RUNBOOK_REAL_RUNS.md (R35-R36) | Tests green, dry run of the whole pipeline |
| A6 | Report skeleton with placeholders (D21), README and THIRD_PARTY credits | check_submission run |
| A7 | Optional: mixed family pairs (config only), O1 | Only if all above done |
Cut order if time runs short: mixed families, then O1, then B_ETH, then monitor. Detectors are never cut. O2 dropped.

Plan B if E fails twice: track 1.5 (Pareto curve of restrictions), see docs/context/contexte_projet_v7.md section 10.
