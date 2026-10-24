# CONTRIBUTING - how to pick up the work (human or AI session)

## Resume in 5 steps
1. `git clone https://github.com/adamattar-pixel/mole-in-the-market` (or `git fetch` in an existing clone).
2. `git checkout wip/phase-<N>` (the current branch is named in PROGRESS.md, "Resume here"). If there is no wip branch, start from `main`.
3. Read PROGRESS.md first, then docs/context/DECISIONS.md, then CLAUDE.md (rules), then PLAN.md and TRACEABILITY.md.
4. `pip install -r requirements.txt` (Python 3.11 or later).
5. `python -m pytest` and compare with the expected result written in PROGRESS.md.

## Branches
- `main` only receives green gates. The owner merges into main at green gates.
- Work in progress goes to `wip/phase-<N>` (plain push, never force), after each green requirement and at least every 30 minutes, even with a locked test still red.
- One active session per branch. Each person works on their own branch `wip/<phase>-<first name>` (for example `wip/phase-4-sam`).

## Identity
- Commit under your own git identity: author = committer = the person who runs the session.
- No mention of Claude or Anthropic in commits: no "Co-Authored-By", no "Generated with", no "Claude-Session" trailer. The hook in .githooks/commit-msg removes such lines as a safety net.
- Check after each commit: `git log -1 --format=fuller`.

## Before any push
- No secrets: never commit .env or an API key; nothing secret in runs/.
- `python -m pytest` was run and its result is written in PROGRESS.md.
- Identity checked (see above).
- PROGRESS.md "Resume here" updated: branch and last commit, red tests and why, next action, owner decisions pending, install and test commands.

## Rules that do not change
- Tests first (decision D1): tests written from SPEC.md and PREREGISTRATION.md, shown red, locked in a `test(Rxx-Ryy): add failing tests from spec (locked)` commit, then implementation without touching them. A gap = a new test in a separate commit.
- Hard stops H1 to H6 (CLAUDE.md) are reserved to the owner: preregistration freeze, real API calls and spend, definition ambiguities, a locked test that looks wrong, the same failure 3 times, frozen items, secrets, force push, git config, deleting logs.
- Never fabricate results. Every number in the report comes from `python -m tools.reproduce`.
