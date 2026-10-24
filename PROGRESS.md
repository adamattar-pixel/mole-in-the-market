# PROGRESS - Claude's memory and the owner's dashboard
Claude updates this file at the end of every phase and whenever the state changes. After a context reset, read this file first.

## Resume here (read this first; a cold start needs only this file)
- Branch: `wip/phase-4` (work in progress, Phase 4 without real API calls). `main` = last green gate: gate-3.
- Last commit: see `git log -1` on the branch; gate-3 closed at the commit that adds this text.
- Install and test: `pip install -r requirements.txt` then `python -m pytest`. Expected at gate-3: 179 passed, 0 red.
- Red tests and why: none at gate-3.
- Next action: Phase 4 without API (configs espion_dry, espion_smoke, espion_pilot, core B/B_T/C/D; dry runs with the mock client; budget cap; cost per game with the mock), tests first. Then R19 tools/check_submission.py, then Phase 8 page on demo data (viz/demo/).
- Preregistration FROZEN (D15): freeze commit d5e7ebc, hash recorded in e95853a, tag `prereg-frozen`. Any change to frozen items = hard stop H6.
- Owner decisions pending: H2 API key, GO and the 2 model families (D10); audit passes 1 and 2 in a fresh session (/audit); open QUESTIONS.md rows.
- Read next: docs/context/DECISIONS.md (owner decisions, wins over v7 and SPEC), CLAUDE.md, CONTRIBUTING.md, PLAN.md, TRACEABILITY.md.
- Code map: harness/ (economics, config, spy, conditions, agent, metrics, runlog, clients, runner, validation, labels, vizexport), tools/ (reproduce, validate_e), tests/ (test names carry the Rxx id).
- Commands: `python -m tools.reproduce runs results --viz-dir viz/data --figures-dir figures` (all tables from runs/, no key, no network); `python -m tools.validate_e runs` (E PASS/FAIL per family).
- Rules: locked tests are never edited (D1). Real runs refuse to start unless PREREGISTRATION.md status is FROZEN and the real client is used.

## Current state
Phase: 4 (no real API) | Last green gate: gate-3 | Tests: 179 passed

## Log
| Date | Phase | What was done | Evidence (command, result) | Deviations |
|---|---|---|---|---|
| 2026-10-24 | 0 | pytest runner, requirements.txt, pyproject.toml, harness package skeleton, QUESTIONS.md #1-8 | `python -m pytest` -> 1 passed; `git log -3 --format=fuller` author = committer = Adam Attar, no trailer | No baseline harness to import (harness/ was empty, tag `preexisting-baseline` = scaffolding commit fd8c920). Harness is written from scratch as sprint work (QUESTIONS #1). Gate 0 green |
| 2026-10-24 | 1 | PROPOSED texts, definition details, E threshold and game design written in PREREGISTRATION.md (commit 5f7c031). NOT frozen | - | Hard stop H1: freeze waits for the owner. Phases 2-3 continue on PROPOSED texts |
| 2026-10-24 | 2 | R01-R11 implemented in harness/ (economics, config, spy, conditions, agent, metrics). Tests written first from SPEC, locked at 5c52047 (98 red, all NotImplementedError) | `python -m pytest` -> 99 passed; `git diff 5c52047 -- tests/` empty; mutations (gap 10%->20%: 4 tests red; window 3->2: 7 red; window start off-by-one, say >= -> >, inclusive <= -> <, all->any, D filter removed, Wilson term removed, p-value >= -> >: each red) then restored, 99 passed; identity ok, 0 trailers | Commits per requirement made while other locked tests were still red (owner's tests-first rule). R06-R11 share one commit (one file). Solver tolerance (not test tolerance) set to 1e-8. Audit pass 1 (fresh session) NOT RUN, pending owner. Gate 2 self-checks green |
| 2026-10-24 | 3 | R12-R17, R22, R23, R27: write-once logs, mock/OpenRouter clients, budget stop, runner with real-run guards, E validation + script, labels.csv, reproduce (tables, summary, checksums), viz export, consistency check, game grid PDF. Tests locked at c5adce2 (80 red: 79 NotImplementedError + 1 assertion) | `python -m pytest` -> 179 passed; `git diff c5adce2 HEAD -- tests/` = 1 line (approved test(fix) cef08e3, D3); mutations (write mode x->w: 2 red, budget > -> >=: 3 red, E >= -> >: 2 red, post-offer filter removed: 9 red, FROZEN guard removed: 2 red, skip-existing removed: 2 red, reply on all rounds: 2 red, model id check: 2 red, family check: 3 red) then restored; identity ok, 0 trailers, no secrets | Invalid price fallback = previous price (Nash in round 1), counted in the log (QUESTIONS #10). R01 cross-check vs luciasauer done (TRACEABILITY). Audit pass 2 (fresh session) NOT RUN, pending owner. Gate 3 self-checks green |
| 2026-10-24 | 1 | Preregistration FROZEN on the owner's order (D15). Only status words changed | freeze commit d5e7ebc ("prereg: freeze"), hash commit e95853a, tag prereg-frozen; `python -m pytest` 179 passed | - |

## Waiting on the owner (hard stops)
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

## Plan changes
- 2026-10-24: Plan mis à jour : Phase 8 (page de replay) ajoutée, R22 à R27 (commit 9c49a66). R22, R23, R27 join Phase 3.
