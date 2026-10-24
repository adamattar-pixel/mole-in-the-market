# CLAUDE.md - Mole in the Market

## What this repo is
Research code and report for Apart Research's AI Collusion Research Sprint (Oct 23 to 25, 2026; deadline Sunday Oct 25, 11:59 PM AoE), track 3.2.
A scripted spy offers a secret price-fixing deal to LLM sellers in a 2-firm price game. We measure what agents SAY (accept) and what they DO (prices).
Read in this order: docs/context/contexte_projet_v7.md, SPEC.md, PREREGISTRATION.md, PLAN.md, AUDIT.md.

## Who you work with
- The owner speaks French. Talk to him in French, start each reply with "maître", keep answers short and simple, no jargon, no long dashes (use "-" or "|").
- Code, comments, commit messages and repo docs: English.

## Non negotiable rules
1. Correctness over looks. A feature is done only when its tests pass AND it matches the SPEC.md requirement. Never say "done" from reading code: show the test output.
2. Never fabricate. No invented results, numbers, logs or citations. Every number in the report must come from the output of `reproduce`. If something was not run, write "not run".
3. Never make a test pass by weakening it (removing asserts, loosening tolerances, skipping, mocking the thing under test, hardcoding expected values). If a test looks wrong, stop and ask.
4. Known-answer tests: expected values are computed by hand (or by an independent formula written in the test), never copied from the code's own output.
5. Mocks only in tests and dry runs. A real run uses the real API client. Every log records model, seed, config hash and git commit.
6. Frozen items (PREREGISTRATION.md: definitions, offer and label texts, hypotheses, E threshold) are not changed after the freeze commit without the owner's explicit approval.
7. No scope creep. Only what SPEC.md lists. Options O1 to O3 only when PLAN.md says the gate is open.
8. Keep preexisting and third-party code separate and recorded in THIRD_PARTY.md. Never present it as new work.
9. Dual-use: do not write or optimize persuasive offers beyond the frozen texts.
10. Secrets: never read, print or commit .env or API keys.
11. If blocked or unsure on a hard stop (see below), ask one short question instead of guessing. Otherwise keep going.

## Continuous phase-gated workflow (autonomous mode)
Work through PLAN.md phase after phase WITHOUT waiting for the owner, as long as every gate is green. For each requirement:
1. Restate the requirement ID(s) from SPEC.md.
2. Write the test first, run it, see it fail for the right reason.
3. Implement the minimum to pass.
4. Mutation check for definition-critical code (R06 to R11): temporarily break the code (for example change 10% to 20%, or off-by-one on the 3 rounds), confirm a test fails, restore. A test that cannot fail is worthless.
5. Run the FULL test suite. Commit only when everything is green.
6. Commit after every green requirement (small commits, at least one per requirement). Never leave a long stretch of work uncommitted.

Self-gate at the end of each phase (the /gate checks, done by yourself):
- full tests green, TRACEABILITY.md updated, AUDIT.md checklist items ticked only with evidence, commit identity verified, no deviation from SPEC.md or PREREGISTRATION.md.
- If ALL green: write the result in PROGRESS.md, commit, `git push origin main` (plain push only), then continue to the next phase immediately.
- If something is red: fix it. After 3 failed attempts on the same problem, stop and ask.

Memory across long sessions: PROGRESS.md is your memory. After any context reset or compaction, read PROGRESS.md, PLAN.md and TRACEABILITY.md first, then resume where you stopped. Update PROGRESS.md at the end of every phase (what is done, evidence, deviations, open questions).

## When you MUST stop and ask (hard stops, and only these)
H1. Freezing PREREGISTRATION.md (offer texts, E threshold, hypotheses). Draft proposals in the file marked PROPOSED, use placeholders in tests, keep going with phases that do not need the final texts, but do not freeze and do not start real runs.
H2. Any real API call or spend (Phase 4 and later), and the API key. Needs the owner's GO and a frozen preregistration.
H3. A requirement is ambiguous, or SPEC.md and PREREGISTRATION.md or v7 contradict each other, in a way that changes a definition.
H4. A test looks wrong, or passing it would require weakening it.
H5. The same failure survives 3 fix attempts.
H6. Anything touching frozen items, secrets, force push, git config, or deleting runs/ logs.
When a question does not block other work, write it in QUESTIONS.md and continue with work that does not depend on it.
