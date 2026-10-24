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
11. If blocked or unsure, ask one short question instead of guessing.

## Phase-gated workflow
For the current phase in PLAN.md only:
1. Restate the requirement IDs (SPEC.md) you are about to satisfy.
2. Write the tests first and show them failing.
3. Implement the minimum to pass.
4. Run the full test suite and show the output.
5. Update TRACEABILITY.md (requirement -> test -> status).
6. Tick the AUDIT.md checklist honestly (unchecked is fine, hiding is not).
7. STOP, report the evidence, wait for the owner's "GO". Do not start the next phase.

## Git rules
- Use the repo's configured git identity. Never change git config. Never use --author or --reset-author.
- Commits must carry only the owner's name. No "Co-Authored-By", no "Generated with Claude Code", no "Claude-Session" trailer, no mention of Claude or Anthropic in commit messages or PR text.
- Small commits, one logical change each. Format: type(scope): summary (feat, fix, test, docs, chore).
- After each commit run `git log -1 --format=fuller` and check author = committer = owner and no trailer. If a trailer slipped in, amend that local unpushed commit and tell the owner.
- Never push without being asked. Never force push. Tag gates as gate-N only when asked.
