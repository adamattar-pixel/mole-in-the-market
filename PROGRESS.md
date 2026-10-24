# PROGRESS - Claude's memory and the owner's dashboard
Claude updates this file at the end of every phase and whenever the state changes. After a context reset, read this file first.

## Current state
Phase: 3 | Last green commit: 4ec7dd5 | Tests: 99 passed

## Log
| Date | Phase | What was done | Evidence (command, result) | Deviations |
|---|---|---|---|---|
| 2026-10-24 | 0 | pytest runner, requirements.txt, pyproject.toml, harness package skeleton, QUESTIONS.md #1-8 | `python -m pytest` -> 1 passed; `git log -3 --format=fuller` author = committer = Adam Attar, no trailer | No baseline harness to import (harness/ was empty, tag `preexisting-baseline` = scaffolding commit fd8c920). Harness is written from scratch as sprint work (QUESTIONS #1). Gate 0 green |
| 2026-10-24 | 1 | PROPOSED texts, definition details, E threshold and game design written in PREREGISTRATION.md (commit 5f7c031). NOT frozen | - | Hard stop H1: freeze waits for the owner. Phases 2-3 continue on PROPOSED texts |
| 2026-10-24 | 2 | R01-R11 implemented in harness/ (economics, config, spy, conditions, agent, metrics). Tests written first from SPEC, locked at 5c52047 (98 red, all NotImplementedError) | `python -m pytest` -> 99 passed; `git diff 5c52047 -- tests/` empty; mutations (gap 10%->20%: 4 tests red; window 3->2: 7 red; window start off-by-one, say >= -> >, inclusive <= -> <, all->any, D filter removed, Wilson term removed, p-value >= -> >: each red) then restored, 99 passed; identity ok, 0 trailers | Commits per requirement made while other locked tests were still red (owner's tests-first rule). R06-R11 share one commit (one file). Solver tolerance (not test tolerance) set to 1e-8. Audit pass 1 (fresh session) NOT RUN, pending owner. Gate 2 self-checks green |

## Waiting on the owner (hard stops)
- H1: approve and freeze PREREGISTRATION.md (texts, E threshold) before Phase 4
- H2: API key and GO for the first real run (Phase 4)
- Audit pass 1 (Phase 2): run /audit in a fresh chat
- QUESTIONS.md #1 to #8

## Workflow rule (owner, 2026-10-24)
Per phase: write ALL tests from SPEC/PREREGISTRATION first (skeletons raise NotImplementedError), show them red, commit `test(Rxx-Ryy): add failing tests from spec (locked)` (not pushed until green), record its hash here, then implement without touching locked tests. End of phase: `git diff <locked> -- tests/` must be empty except listed new tests.

## Locked test commits
| Phase | Requirements | Commit |
|---|---|---|
| 2 | R01-R11 | 5c52047 |

## Plan changes
- 2026-10-24: Plan mis à jour : Phase 8 (page de replay) ajoutée, R22 à R27 (commit 9c49a66). R22, R23, R27 join Phase 3.
