# ops/ - process docs for agents and people

Everything about HOW the work is run lives here: state, plans, decisions, questions, audits, coordination.
The human-facing docs: README.md, CONTRIBUTING.md and THIRD_PARTY.md at the root; docs/SPEC.md,
docs/RUNBOOK_REAL_RUNS.md and docs/CHANGELOG.md in docs/. CLAUDE.md stays at the root because Claude Code loads it from there.
PREREGISTRATION.md and PREREGISTRATION_ADDENDUM.md stay at the root and are FROZEN (code and tags read them by path).

Path convention: repo docs write paths from the repo root (`ops/STATE.md`). Inside ops/, a bare name of a
sibling file (`QUESTIONS.md #21`) means the file in ops/. Older rows written before the move (2026-10-24) use
bare names for files that now live here.

## Cold start: read in this order
1. `ops/STATE.md` - where things stand right now (one screen).
2. `ops/CLAIMS.md` - who is working on what. Check it before touching anything.
3. `CLAUDE.md` - the rules (tests first, hard stops H1-H6, git rules).
4. `ops/DECISIONS.md` - owner decisions; they win over docs/SPEC.md and docs/context/contexte_projet_v7.md.
5. `ops/OPEN_ISSUES.md` - the backlog; pick work from here.
6. `docs/SPEC.md`, `PREREGISTRATION.md`, `PREREGISTRATION_ADDENDUM.md` - what to build and the frozen definitions.
7. As needed: `ops/PLAN.md`, `ops/TRACEABILITY.md`, `ops/QUESTIONS.md`, `ops/AUDIT.md`, `docs/RUNBOOK_REAL_RUNS.md`.

## Files
| File | What it is for | Who writes it | When |
|---|---|---|---|
| STATE.md | Current state: branches, open PRs, last green commit and test count, frozen items, who blocks what. The single "resume here" | Whoever changes the state (merge, gate, new branch, decision) | In the same commit as the change |
| CLAIMS.md | Coordination board: one row per active piece of work, rules for branches, PRs and conflicts | Every agent or person, for their own row | Add a row before starting, remove it on merge |
| OPEN_ISSUES.md | Numbered backlog (id, title, owner, status, link) | Anyone who finds an issue; the owner sets owners | When an issue is found or its status changes |
| PROGRESS.md | Append-only log of phases: what was done, evidence, deviations; locked test commits | The agent that finishes a phase or gate | End of every phase or gate |
| PLAN.md | Phases, gates, cut order | Owner (or an agent on the owner's order) | When the plan changes |
| DECISIONS.md | Dated owner decisions D1, D2, ... | Owner, or an agent recording the owner's words | When the owner decides |
| QUESTIONS.md | Non-blocking questions with the default taken; the owner answers in the last column | Agents ask, owner answers | When a question comes up |
| TRACEABILITY.md | Requirement -> test -> evidence | The agent that implements a requirement | At every gate |
| AUDIT.md | Audit checklist and audit log | Fresh-session reviewers (`/audit`), owner | After each audit |
| HANDOFF.md | Historical snapshot of the 2026-10-24 handoff from Adam to Artem | Nobody (frozen as history) | Never; current state goes to STATE.md |

## Check
`python3 -m tools.check_ops` fails if a path `ops/...` cited in the repo does not exist, or if a row in the
CLAIMS.md "Active claims" table is malformed. Run it before pushing a change to ops/.
