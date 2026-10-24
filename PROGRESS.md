# PROGRESS - Claude's memory and the owner's dashboard
Claude updates this file at the end of every phase and whenever the state changes. After a context reset, read this file first.

## Current state
Phase: 1 (hard stop H1, drafts only) then 2 | Last green commit: 2a4469c | Tests: 1 passed

## Log
| Date | Phase | What was done | Evidence (command, result) | Deviations |
|---|---|---|---|---|
| 2026-10-24 | 0 | pytest runner, requirements.txt, pyproject.toml, harness package skeleton, QUESTIONS.md #1-8 | `python -m pytest` -> 1 passed; `git log -3 --format=fuller` author = committer = Adam Attar, no trailer | No baseline harness to import (harness/ was empty, tag `preexisting-baseline` = scaffolding commit fd8c920). Harness is written from scratch as sprint work (QUESTIONS #1). Gate 0 green |

## Waiting on the owner (hard stops)
- H1: approve and freeze PREREGISTRATION.md (texts, E threshold) before Phase 4
- H2: API key and GO for the first real run (Phase 4)

## Workflow rule (owner, 2026-10-24)
Per phase: write ALL tests from SPEC/PREREGISTRATION first (skeletons raise NotImplementedError), show them red, commit `test(Rxx-Ryy): add failing tests from spec (locked)` (not pushed until green), record its hash here, then implement without touching locked tests. End of phase: `git diff <locked> -- tests/` must be empty except listed new tests.

## Locked test commits
| Phase | Requirements | Commit |
|---|---|---|
