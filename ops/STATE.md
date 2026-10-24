# STATE - where the repo stands (resume here)
This is the single "resume here". ops/PROGRESS.md keeps only the history log. Update this file in the same
commit as any change of state (merge, gate, new branch, owner decision). Last updated: 2026-10-24.

## Branches
| Branch | Tip | What it is for |
|---|---|---|
| `main` (origin) | 506e3d1 | Green gates only: gate-3 + preregistration freeze (D15). Next: gate-4 after the real smoke and pilot |
| `wip/phase-4` (origin) | 846d3d8 | Current shared phase branch: Phase 4 no-API work, R19, R24-R25, R28-R36, review fixes M1-M4, audit records. Same tip as local `artem` |
| `wip/phase-4-artem` (origin) = local `artem-owner-approval` | a6b6022 | Owner decisions (test(fix) #21, abstract 150-250, validate_e --config, cost guard). PR #1 into `wip/phase-4`, open |
| `artem-ops-reorg` (local) | this branch | ops/ reorg, coordination board, CHANGELOG, tools/check_ops.py. Stacked on `artem-owner-approval`; PR into `wip/phase-4` after PR #1 |
| `wip/phase-3` (origin) | da4011c | Historical (gate-3). No new work |
| `wip/phase-4-artem-workers` (local) | see git log | `--workers N` for tools.run and tools.run_all, `--continue-passing-families` (owner decision QUESTIONS #24, test(fix) approval #25). From local `artem`; PR into `wip/phase-4` after review. 727 tests pass |

Merge note: `artem-owner-approval` does not contain 846d3d8 (2 doc lines in AUDIT.md and PROGRESS.md). Git
follows the renames to ops/, but the PROGRESS.md "Resume here" line edited by 846d3d8 is removed here: keep
the removal (this file replaces it).

## Tests
- Last green: a6b6022 (`artem-owner-approval`), `python3 -m pytest` -> 653 passed, 0 failed. On `artem-ops-reorg` (2b2b6b3): 678 passed (+25 for tools/check_ops).
- Install and test: `python3 -m pip install -r requirements.txt` then `python3 -m pytest`.
- Whole pipeline dry (mock client, no key, no cost): `python3 -m tools.run_all --dry --exploratory --o1`.
- Ops check: `python3 -m tools.check_ops`.

## Frozen (never edited; any change = hard stop H6, owner only, logged as a deviation)
- PREREGISTRATION.md: frozen at d5e7ebc, tag `prereg-frozen` (e95853a, hash recorded).
- PREREGISTRATION_ADDENDUM.md: frozen at 8b7b5a1, tag `addendum-frozen` (378f1dd, hash recorded).
- Locked tests: every commit whose subject ends in `(locked)` (`git log --oneline --grep='(locked)'`). Only owner-approved `test(fix)` commits change them (cef08e3, 271e650, c8751dd, 61b2823).
- docs/context/contexte_projet_v7.md: never edited.
- Other tags: `preexisting-baseline` (fd8c920, scaffolding only), `gate-0` (a9f9862), `gate-2` (f999951), `gate-3` (da4011c), `handoff-artem-1` (f1462b9).

## Blocked, and on whom
| What | Waits on | Ref |
|---|---|---|
| Model ids for the 2 families (configs are `tbd`; a real run is refused until filled) | Adam | D10, QUESTIONS #7, OPEN_ISSUES #1 |
| OpenRouter key in the shell and GO for the first real run (smoke, then pilot, then E gate) | Artem | H2, OPEN_ISSUES #2 |
| Budget caps (per config and global 30 USD) | Artem | QUESTIONS #11, #17, #22 |
| Merge PR #1, then this branch, into `wip/phase-4` | Artem | - |
| Affiliations in README.md and report/AUTHORS.md | Artem and Adam | OPEN_ISSUES #3 |
| Keep docs/context/contexte_projet_v7.md in the public repo or not | Artem | OPEN_ISSUES #17 |

## Next action
1. Owner merges PR #1, then this branch. 2. Adam gives the model ids; fill configs and configs/prices.yaml
(RUNBOOK_REAL_RUNS.md step 2), suite green. 3. Real smoke `python3 -m tools.run_all --stop-after smoke`
(H2). 4. Follow RUNBOOK_REAL_RUNS.md. Runs freeze Sunday Oct 25 noon; submit early Sunday, before 23:59 AoE.
