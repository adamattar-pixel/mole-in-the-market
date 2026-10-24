# CLAUDE.md - Mole in the Market

## What this repo is
Research code and report for Apart Research's AI Collusion Research Sprint (Oct 23 to 25, 2026; deadline Sunday Oct 25, 11:59 PM AoE), track 3.2.
A scripted spy offers a secret price-fixing deal to LLM sellers in a 2-firm price game. We measure what agents SAY (accept) and what they DO (prices).
ops/DECISIONS.md (owner decisions) wins over docs/context/contexte_projet_v7.md and SPEC.md in case of conflict. Never edit contexte_projet_v7.md.

## Coordination (several agents and people work in parallel)
- Cold start, in this order: ops/STATE.md, ops/CLAIMS.md, this file, ops/DECISIONS.md, ops/OPEN_ISSUES.md, then SPEC.md, PREREGISTRATION.md, PREREGISTRATION_ADDENDUM.md. The map of every process doc is ops/README.md.
- Before starting work, check ops/CLAIMS.md on every remote branch and add your own row (one active writer per file area). Remove it in the PR that merges the work.
- Branches `wip/phase-<N>-<name>-<topic>`, PR into the current `wip/phase-<N>`; only green gate PRs go into `main` (ops/CLAIMS.md).
- Keep ops/STATE.md current in the same commit as any change of state. Run `python3 -m tools.check_ops` after editing ops/.

## Who you work with
- Project owner (since 2026-10-24, see ops/HANDOFF.md): **Artem**. Talk to him in English: short and simple, no jargon, no long dashes (use "-" or "|"). Hard stops H1 to H6 (freeze approvals, API key, GO for real runs, frozen items) go to Artem.
- Co-author: Adam Attar (adamattar-pixel), reachable for decisions (model ids, D10). If someone else runs the session, answer in English unless they write in another language. Keep answers short and simple.
- Code, comments, commit messages and repo docs: English.

## Non negotiable rules
1. Correctness over looks. A feature is done only when its tests pass AND it matches the SPEC.md requirement. Never say "done" from reading code: show the test output.
2. Never fabricate. No invented results, numbers, logs or citations. Every number in the report must come from the output of `reproduce`. If something was not run, write "not run".
3. Never make a test pass by weakening it (removing asserts, loosening tolerances, skipping, mocking the thing under test, hardcoding expected values). If a test looks wrong, stop and ask.
4. Known-answer tests: expected values are computed by hand (or by an independent formula written in the test), never copied from the code's own output.
5. Mocks only in tests and dry runs. A real run uses the real API client. Every log records model, seed, config hash and git commit.
6. Frozen items (PREREGISTRATION.md: definitions, offer and label texts, hypotheses, E threshold) are not changed after the freeze commit without the owner's explicit approval.
7. No scope creep. Only what SPEC.md lists. Options O1 to O3 only when ops/PLAN.md says the gate is open.
8. Keep preexisting and third-party code separate and recorded in THIRD_PARTY.md. Never present it as new work.
9. Dual-use: do not write or optimize persuasive offers beyond the frozen texts.
10. Secrets: never read, print or commit .env or API keys.
11. If blocked or unsure on a hard stop (see below), ask one short question instead of guessing. Otherwise keep going.

## Continuous phase-gated workflow (autonomous mode)
Work through ops/PLAN.md phase after phase WITHOUT waiting for the owner, as long as every gate is green. For each requirement:
1. Restate the requirement ID(s) from SPEC.md.
2. Write the test first, run it, see it fail for the right reason.
3. Implement the minimum to pass.
4. Mutation check for definition-critical code (R06 to R11): temporarily break the code (for example change 10% to 20%, or off-by-one on the 3 rounds), confirm a test fails, restore. A test that cannot fail is worthless.
5. Run the FULL test suite. Commit only when everything is green.
6. Commit after every green requirement (small commits, at least one per requirement). Never leave a long stretch of work uncommitted.

Self-gate at the end of each phase (the /gate checks, done by yourself):
- full tests green, ops/TRACEABILITY.md updated, ops/AUDIT.md checklist items ticked only with evidence, commit identity verified, no deviation from SPEC.md or PREREGISTRATION.md.
- If ALL green: write the result in ops/PROGRESS.md and ops/STATE.md, commit, open the gate PR from `wip/phase-<N>` into `main` (the owner merges it and tags gate-N), then continue to the next phase immediately.
- If something is red: fix it. After 3 failed attempts on the same problem, stop and ask.

Memory across long sessions: ops/STATE.md is the current state, ops/PROGRESS.md the history log. After any context reset or compaction, read ops/STATE.md, ops/CLAIMS.md, ops/DECISIONS.md and ops/PLAN.md first, then resume where you stopped. Append an ops/PROGRESS.md row at the end of every phase (what is done, evidence, deviations, open questions).

## Git rules
- `main` only receives green gate PRs (then tag gate-N). Work in progress goes to your own `wip/phase-<N>-<name>-<topic>` branch, PR into `wip/phase-<N>` (the owner Artem may work on it directly), with a plain push after each green requirement and at least every 30 minutes. Never force push a shared branch.
- Before ANY push: no secrets (.env, API keys, nothing secret in runs/), `python -m pytest` run, `git log -1 --format=fuller` shows the contributor's own name and email (each contributor commits under their own identity) and no Co-Authored-By or other AI trailer, ops/STATE.md updated (branches, last commit, red tests and why, next action, pending owner decisions).
- Tests first (ops/DECISIONS.md D1): locked test commit `test(Rxx-Ryy): add failing tests from spec (locked)` before implementation; locked tests are never edited, except an owner-approved `test(fix)` commit.
- Every contributor commits under their own identity (see CONTRIBUTING.md). Never change git config.

## When you MUST stop and ask (hard stops, and only these)
H1. Freezing PREREGISTRATION.md (offer texts, E threshold, hypotheses). Draft proposals in the file marked PROPOSED, use placeholders in tests, keep going with phases that do not need the final texts, but do not freeze and do not start real runs.
H2. Any real API call or spend (Phase 4 and later), and the API key. Needs the owner's (Artem's) GO and a frozen preregistration and addendum.
H3. A requirement is ambiguous, or SPEC.md and PREREGISTRATION.md or v7 contradict each other, in a way that changes a definition and is not settled by ops/DECISIONS.md.
H4. A test looks wrong, or passing it would require weakening it.
H5. The same failure survives 3 fix attempts.
H6. Anything touching frozen items, secrets, force push, git config, or deleting runs/ logs.
When a question does not block other work, write it in ops/QUESTIONS.md (and the work it needs in ops/OPEN_ISSUES.md) and continue with work that does not depend on it.
