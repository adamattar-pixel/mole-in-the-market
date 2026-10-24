# CLAIMS - who is working on what
Coordination board for parallel work (Artem's Claude sessions, Adam's Claude, people). One row per active
piece of work. `python3 -m tools.check_ops` checks the rows of the table below.

## Rules
1. **Check first.** Before starting, read the claims on every branch, not only yours:
   `git fetch origin && git grep -e '^| ' $(git for-each-ref --format='%(refname:short)' refs/remotes/origin) -- ops/CLAIMS.md`
   Also check open PRs. If your files or areas overlap an active claim, do not start: see "On conflict".
2. **One active writer per file area.** An area is a file, a folder, or a named part (for example `harness/detectors.py`, `viz/`, `configs/espion_*.yaml`). Name it as narrowly as you can.
3. **Claim with a commit.** Create your branch, add your row as its first commit (`chore(claims): claim <area>`), and push that branch before any other work. A claim that is not pushed does not exist.
4. **Release on merge.** Remove your row in the last commit of the PR, so the merge releases the claim. If you abandon the work, remove the row and push.
5. **Stay inside the claim.** Need another area? Check, then extend your row in a new commit, before editing it.
6. **Always off limits** without the owner (hard stop H6): PREREGISTRATION.md, PREREGISTRATION_ADDENDUM.md, locked tests, docs/context/contexte_projet_v7.md, git config, secrets.
7. Shared files touched by everyone (ops/STATE.md, ops/PROGRESS.md, ops/OPEN_ISSUES.md, CHANGELOG.md): no claim needed, but edit only your own rows or lines and keep the edits small.

## Row format
`| Who | Branch | Files / areas | Started | Expected end |`
- Who: person and agent, for example `Artem (Claude session 2)`, `Adam (Claude)`, `Adam`.
- Branch: the branch the work lives on, no spaces.
- Files / areas: comma-separated paths or areas, not empty.
- Started, Expected end: `YYYY-MM-DD` or `YYYY-MM-DD HH:MM` (24 h, add ` UTC` or an offset such as ` +08:00`); the end is not before the start.
- A claim past its expected end with no push for 2 hours is stale: ask its owner (or Artem) before taking it over.

## Branches and PRs
- Names: `wip/phase-<N>-<name>-<topic>`, for example `wip/phase-4-artem-detectors`, `wip/phase-7-adam-report`. Lower case, `-` between words. Branches made before this rule (`artem`, `artem-*`, `wip/phase-4-artem`) keep their names until merged.
- Flow: feature branch -> PR into the current `wip/phase-<N>` (ops/STATE.md names it) -> when the phase gate is green, a gate PR from `wip/phase-<N>` into `main`; the owner merges it and tags `gate-<N>`. `main` only receives green gates.
- A PR is mergeable when `python3 -m pytest` and `python3 -m tools.check_ops` are green, identity is checked (no AI trailer), and ops/STATE.md is updated.
- Plain pushes only. Never force push or rebase a pushed branch.

## On conflict
- **Overlapping claim:** the older claim wins. Talk to its owner; split the area, wait, or ask Artem to decide. Do not edit the area meanwhile.
- **Git conflict when merging:** merge the target branch into yours (no rebase), resolve, run the full suite, push. In ops/STATE.md keep what is true after both changes. If the conflict is in a frozen file or a locked test, stop (H6) and ask the owner.
- **Two different answers to the same question:** log both in ops/QUESTIONS.md; the owner decides (ops/DECISIONS.md).

## Active claims
| Who | Branch | Files / areas | Started | Expected end |
|---|---|---|---|---|
