# CONTRIBUTING - how to pick up the work (human or AI session)

## Resume in 5 steps
1. `git clone https://github.com/adamattar-pixel/mole-in-the-market` (or `git fetch` in an existing clone).
2. `git checkout wip/phase-<N>` (the current branch is named in ops/STATE.md). If there is no wip branch, start from `main`.
3. Read in the cold-start order of ops/README.md: ops/STATE.md, ops/CLAIMS.md, CLAUDE.md (rules), ops/DECISIONS.md, ops/OPEN_ISSUES.md, then SPEC.md and the preregistration.
4. `pip install -r requirements.txt` (Python 3.11 or later).
5. `python -m pytest` and compare with the expected result written in ops/STATE.md.

## Branches
- `main` only receives green gate PRs. The owner (Artem, see ops/STATE.md) merges them and tags gate-N.
- Work goes to your own branch `wip/phase-<N>-<name>-<topic>` and a PR into the current `wip/phase-<N>` (plain push, never force), after each green requirement and at least every 30 minutes, even with a locked test still red.
- One active session per branch, one active writer per file area. Claim your area in ops/CLAIMS.md before starting (rules and conflict handling are there).

## Identity
- Commit under your own git identity: author = committer = the person who runs the session.
- No mention of Claude or Anthropic in commits: no "Co-Authored-By", no "Generated with", no "Claude-Session" trailer. The hook in .githooks/commit-msg removes such lines as a safety net.
- Check after each commit: `git log -1 --format=fuller`.

## Before any push
- No secrets: never commit .env or an API key; nothing secret in runs/.
- `python -m pytest` was run and its result is written in ops/STATE.md (and in an ops/PROGRESS.md row at the end of a phase).
- Identity checked (see above).
- ops/STATE.md updated: branches and last commit, red tests and why, next action, owner decisions pending.

## Rules that do not change
- Tests first (decision D1): tests written from SPEC.md and PREREGISTRATION.md, shown red, locked in a `test(Rxx-Ryy): add failing tests from spec (locked)` commit, then implementation without touching them. A gap = a new test in a separate commit.
- Hard stops H1 to H6 (CLAUDE.md) are reserved to the owner (Artem): preregistration freeze, real API calls and spend, definition ambiguities, a locked test that looks wrong, the same failure 3 times, frozen items, secrets, force push, git config, deleting logs.
- Never fabricate results. Every number in the report comes from `python -m tools.reproduce`.
