# PROGRESS - Claude's memory and the owner's dashboard
Claude updates this file at the end of every phase and whenever the state changes. After a context reset, read this file first.

## Resume here (read this first)
- READ HANDOFF.md FIRST. Project owner: **Artem** (full handoff 2026-10-24). Adam Attar (adamattar-pixel) stays co-author and is reachable for decisions.
- Branch `wip/phase-4`, commit "docs: handoff ownership to Artem" (tag `handoff-artem-1` kept on the previous checkpoint). `python -m pytest` -> 254 passed, 0 red.
- main = gate-3 + preregistration freeze (tag `prereg-frozen`). Addendum frozen (tag `addendum-frozen`).
- Install and test: `pip install -r requirements.txt` then `python -m pytest`.
- Next actions, in order (details in HANDOFF.md section 6b): 1) pick the 2 model families and set OPENROUTER_API_KEY, 2) GO for real smoke then pilot (A, E) and the E gate, 3) core runs and `reproduce`, 4) detectors R28-R30, 5) R31-R36, tools/run_all, RUNBOOK_REAL_RUNS.md, 6) report and check_submission. Runs freeze Sunday noon; submit early Sunday before 23:59 AoE.
- Frozen, never edited: PREREGISTRATION.md, PREREGISTRATION_ADDENDUM.md, locked tests (D1). Any change = QUESTIONS.md + reported deviation.

## Current state
Phase: 4 no-API part done (gate open, H2); R19, R24-R25 done; R28-R36 not started in code | Checkpoint: handoff to Artem | Tests: 254 passed

## Log
| Date | Phase | What was done | Evidence (command, result) | Deviations |
|---|---|---|---|---|
| 2026-10-24 | 0 | pytest runner, requirements.txt, pyproject.toml, harness package skeleton, QUESTIONS.md #1-8 | `python -m pytest` -> 1 passed; `git log -3 --format=fuller` author = committer = Adam Attar, no trailer | No baseline harness to import (harness/ was empty, tag `preexisting-baseline` = scaffolding commit fd8c920). Harness is written from scratch as sprint work (QUESTIONS #1). Gate 0 green |
| 2026-10-24 | 1 | PROPOSED texts, definition details, E threshold and game design written in PREREGISTRATION.md (commit 5f7c031). NOT frozen | - | Hard stop H1: freeze waits for the owner. Phases 2-3 continue on PROPOSED texts |
| 2026-10-24 | 2 | R01-R11 implemented in harness/ (economics, config, spy, conditions, agent, metrics). Tests written first from SPEC, locked at 5c52047 (98 red, all NotImplementedError) | `python -m pytest` -> 99 passed; `git diff 5c52047 -- tests/` empty; mutations (gap 10%->20%: 4 tests red; window 3->2: 7 red; window start off-by-one, say >= -> >, inclusive <= -> <, all->any, D filter removed, Wilson term removed, p-value >= -> >: each red) then restored, 99 passed; identity ok, 0 trailers | Commits per requirement made while other locked tests were still red (owner's tests-first rule). R06-R11 share one commit (one file). Solver tolerance (not test tolerance) set to 1e-8. Audit pass 1 (fresh session) NOT RUN, pending owner. Gate 2 self-checks green |
| 2026-10-24 | 3 | R12-R17, R22, R23, R27: write-once logs, mock/OpenRouter clients, budget stop, runner with real-run guards, E validation + script, labels.csv, reproduce (tables, summary, checksums), viz export, consistency check, game grid PDF. Tests locked at c5adce2 (80 red: 79 NotImplementedError + 1 assertion) | `python -m pytest` -> 179 passed; `git diff c5adce2 HEAD -- tests/` = 1 line (approved test(fix) cef08e3, D3); mutations (write mode x->w: 2 red, budget > -> >=: 3 red, E >= -> >: 2 red, post-offer filter removed: 9 red, FROZEN guard removed: 2 red, skip-existing removed: 2 red, reply on all rounds: 2 red, model id check: 2 red, family check: 3 red) then restored; identity ok, 0 trailers, no secrets | Invalid price fallback = previous price (Nash in round 1), counted in the log (QUESTIONS #10). R01 cross-check vs luciasauer done (TRACEABILITY). Audit pass 2 (fresh session) NOT RUN, pending owner. Gate 3 self-checks green |
| 2026-10-24 | 1 | Preregistration FROZEN on the owner's order (D15). Only status words changed | freeze commit d5e7ebc ("prereg: freeze"), hash commit e95853a, tag prereg-frozen; `python -m pytest` 179 passed | - |
| 2026-10-24 | 4 (no API) | Gap tests for phases 0-3 (b2ffcd5 + test commit), TEST_ORDER_REPORT.md. Configs dry/smoke/pilot/core, dry mock client, tools/run.py, cost_summary, guards (mock never writes to runs/, real run refused on tbd models). Tests locked at 87c3b7f (22 red: 17 missing configs, 5 NotImplementedError) | `python -m pytest` -> 209 passed; mutations: tbd guard off 3 red, runs/ guard off 1 red, cost mean off 2 red, dry client non-deterministic 2 red; restored | A first mutation pass restored uncommitted files with git checkout and lost the implementation; it was rewritten, committed (0a048dd), and the mutation pass redone. Gate 4 OPEN: real smoke/pilot need H2 |
| 2026-10-24 | 4/7/8 + handoff | R19 check_submission (locked a0cd120, 20 red NotImplementedError, then green; mutations: 150->151 3 red, <= -> < 1 red, appendix heading check 1 red, overall not-run-as-pass 2 red). R24-R25 page + demo data (locked ef5bccd, 25 red; mutations: script list 1 red, external URL 2 red, runs/ refusal 2 red, synthetic flag 1 red; page rendered in headless Chrome and inspected). Plan v2: SPEC R28-R36, DECISIONS D16-D21, Phase 8 cut, addendum frozen (8b7b5a1/378f1dd, tag addendum-frozen). HANDOFF.md for Artem | `python -m pytest` -> 254 passed; git status clean | R28-R36 draft tests written but not committed (moved out of the repo) on the owner's handoff order. Self-audit: written, fresh-session audit NOT RUN |
| 2026-10-24 | handoff | Full ownership handoff to Artem: HANDOFF.md, CLAUDE.md (owner, identity rule), CONTRIBUTING.md, README.md authors and run commands, report/AUTHORS.md | `python -m pytest` -> 254 passed; git status clean | No requirement started. Adam stays co-author |

## Waiting on the owner (hard stops, owner = Artem since 2026-10-24)
- H2: API key and GO for the first real run (Phase 4)
- Audit pass 1 (Phase 2): run /audit in a fresh chat
- QUESTIONS.md open rows (1-9 answered 2026-10-24, see DECISIONS.md)
- Audit pass 2 (Phase 3): run /audit in a fresh chat

## Workflow rule (owner, 2026-10-24)
Per phase: write ALL tests from SPEC/PREREGISTRATION first (skeletons raise NotImplementedError), show them red, commit `test(Rxx-Ryy): add failing tests from spec (locked)` (not pushed until green), record its hash here, then implement without touching locked tests. End of phase: `git diff <locked> -- tests/` must be empty except listed new tests.

## Locked test commits
| Phase | Requirements | Commit |
|---|---|---|
| 2 | R01-R11 | 5c52047 |
| 3 | R12-R17, R22, R23, R27 | c5adce2 |
| 4 (no API) | R12, R13, R16, R17 (P4 tests) | 87c3b7f |
| 7 tool | R19 | a0cd120 |
| 8 (cut) | R24-R25 | ef5bccd |

## Plan changes
- 2026-10-24: Plan mis à jour : Phase 8 (page de replay) ajoutée, R22 à R27 (commit 9c49a66). R22, R23, R27 join Phase 3.
