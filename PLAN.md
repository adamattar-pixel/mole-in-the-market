# PLAN - phases and gates
Claude works only on the phase marked CURRENT and stops at each gate. The owner says "GO" to open the next phase.
Times are a proposal for Saturday Oct 24 and Sunday Oct 25 (deadline Sunday 11:59 PM AoE). Runs freeze Sunday at noon (to confirm).

| Phase | Content | Gate (evidence required) | Status |
|---|---|---|---|
| 0 | Scaffolding, baseline import of existing harness, `preexisting-baseline` tag, test runner works | Tests of the baseline run, `git log -1 --format=fuller` shows the owner's identity and no trailer | CURRENT |
| 1 | Complete and freeze PREREGISTRATION.md (texts, E threshold, hypotheses). Owner approves | Freeze commit, hash written in PREREGISTRATION.md, tag `prereg-frozen` | |
| 2 | Core logic with tests on a mock model: R01 to R11 | All tests green, TRACEABILITY.md filled, audit pass 1 (fresh session) | |
| 3 | Pipeline: logs, labels, `reproduce`, cost cap: R12 to R17 | `reproduce` deterministic on mock data, audit pass 2 | |
| 4 | Real smoke and pilot on A and E only (espion_smoke, espion_pilot). Measure real cost per game | Cost per game measured. E validation (R13): if E shows no collusion, change model once, otherwise plan B | |
| 5 | Core runs B, B_T, C, D (5 seeds, 2 families), base rate on A and D | Logs saved, `reproduce` regenerates the tables, audit pass 3 | |
| 6 | Options O1 then O2 then O3, each behind its own gate | Core finished and saved | |
| 7 | Report on the official Apart template, abstract, appendix, submission checks (R19 to R21), repo public | Audit pass 4, checklist in docs/apart/README.md, submit early Sunday | |

Plan B if E fails twice: track 1.5 (Pareto curve of restrictions), see docs/context/contexte_projet_v7.md section 10.
