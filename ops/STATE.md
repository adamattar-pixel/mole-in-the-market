# STATE - where the repo stands (resume here)
This is the single "resume here". ops/PROGRESS.md keeps only the history log. Update this file in the same
commit as any change of state (merge, gate, new branch, owner decision). Last updated: 2026-10-26 (authors and LLM statement, D40).

## Branches
| Branch | Tip | What it is for |
|---|---|---|
| `main` (origin) | see git log | Merge of `wip/phase-4-adam-report` on 2026-10-26 (D38, then D39 for the LaTeX report) on top of D36. Gates are `gate-N` tags (gate-4 exists) |
| `wip/phase-4` (origin) | 764b623 | Shared phase branch: everything merged (R28-R36, provider pins, THINK arm, workers, retries, key figure, insight checks), real run data, results summary |
| `wip/phase-4-hoang` (origin) | 6c07574 | Hoang: spend ledger, resilient runner, CLI filters, entry points, help texts, demo allowlist. Merged into `wip/phase-4-final` (d30493e) |
| `wip/phase-4-artem-viz`, `wip/phase-4-artem-grid` (local, in progress) | see git log | Replay page on real data; Figure 1 label fix |
| `wip/phase-4-adam-numbers` (origin) | 429f1c4 | Adam (Claude): R18 tools/check_numbers.py, numbers and references audits, OPEN_ISSUES #19. Merged into `wip/phase-4-final` (a0a56f6) |
| `wip/phase-4-final` (origin) | see git log | Adam (Claude), 2026-10-26: wip/phase-4 + both branches above + OPEN_ISSUES #24-#27 fixes. Ready for a PR into `wip/phase-4` (no gh on this machine); full suite 970 passed |
| `wip/phase-4-adam-final-demo` (origin) | see git log | Adam (Claude), 2026-10-26: wip/phase-4-final + owner answers (D28-D35), results/defenses.md NOT RUN labels (QUESTIONS #31), replay page story mode (docs/viz/DEMO.md), direct Anthropic client (mock only), docs/team-artem/SUBMISSION_STATUS.md and REMAINING_RUNS.md. Full suite 994 passed. Ready for a PR into `wip/phase-4` (opened by a human) |
| `wip/phase-4-adam-report` (origin) | see git log | Adam (Claude), 2026-10-26: D37, D38, AI-drafted report in report/final/, author placeholders, final check script; D39: new text, PDF compiled from REPORT.tex (main body 5.67 pages). Merged into main (D38, D39) |
| `wip/phase-3` (origin) | da4011c | Historical (gate-3) |

## Tests
- Current: on `wip/phase-4-adam-final-demo`, `python -m pytest -o addopts=""` -> 994 passed, 0 failed (2026-10-26); `tools.check_ops` OK; `reproduce --deviations` twice -> identical, equal to committed results/checksums.txt; `run_all --dry --exploratory --think --o1 --workers 4` exit 0 with no key.
- Last green: a6b6022 (`artem-owner-approval`), `python3 -m pytest` -> 653 passed, 0 failed. On `artem-ops-reorg` (2b2b6b3): 678 passed (+25 for tools/check_ops).
- Install and test: `python3 -m pip install -r requirements.txt` then `python3 -m pytest`.
- Whole pipeline dry (mock client, no key, no cost): `python3 -m tools.run_all --dry --exploratory --think --o1` (add `--workers 4` to run the games of each step 4 at a time; same logs).
- Ops check: `python3 -m tools.check_ops`.

## Frozen (never edited; any change = hard stop H6, owner only, logged as a deviation)
- PREREGISTRATION.md: frozen at d5e7ebc, tag `prereg-frozen` (e95853a, hash recorded).
- PREREGISTRATION_ADDENDUM.md: frozen at 8b7b5a1, tag `addendum-frozen` (378f1dd, hash recorded).
- Locked tests: every commit whose subject ends in `(locked)` (`git log --oneline --grep='(locked)'`). Only owner-approved `test(fix)` commits change them (cef08e3, 271e650, c8751dd, 61b2823).
- docs/context/contexte_projet_v7.md: never edited.
- Other tags: `preexisting-baseline` (fd8c920, scaffolding only), `gate-0` (a9f9862), `gate-2` (f999951), `gate-3` (da4011c), `handoff-artem-1` (f1462b9).

## Real runs (2026-10-24 evening, details in docs/team-artem/RESULTS_SUMMARY.md)
- Done: smoke, pilot A/E x 5 seeds (both families), E gate (Llama PASS 0.93, Haiku FAIL 0.11), Llama core B, B_T, C, D x 5 seeds.
- Deviations: Llama re-pinned to CoreWeave fp16 after the Novita outage (QUESTIONS #26); Sonnet fallback removed because it billed OpenRouter credits, so the core is Llama-only (QUESTIONS #27, run_all_deviations.json).
- Exploratory: 2 Qwen 3.8 reasoning games (raw traces local, git-ignored); 8 partial Sonnet games archived.
- **Not run**: monitor (R31-R32), ethics (R33-R34), memory arm, gpt-oss THINK arm, O1. Reason: the OpenRouter credit cap (5 USD) was reached at about 23:00 HKT (usage 5.04). All API calls are stopped until the owner decides.

## Blocked, and on whom
| What | Waits on | Ref |
|---|---|---|
| More runs (monitor, ethics, memory, THINK, O1, Haiku exploratory): need OpenRouter credit, or a direct Anthropic client for Haiku | Artem | QUESTIONS #27 |
| Confirm the night deviations (#26 re-pin, #27 Llama-only, test(fix) commits 85bf3e1/178f1ea and the pin fixes) | Artem | ops/QUESTIONS.md |
| Accept the locked M1 test change on wip/phase-4-hoang: a rerun no longer pays the dropped game's calls again | Artem | tests/test_review_M1_budget_resume.py |
| Gate-4 tag (E gate passed for Llama only, a deviation) | Artem | D24 |
| (done) Affiliations: HKUST, Hong Kong (report/AUTHORS.md); Artem's surname still missing in report/final/REPORT.md | Artem | OPEN_ISSUES #3 |
| Keep docs/context/contexte_projet_v7.md public or not | Artem | OPEN_ISSUES #17 |

## Human actions left (project closed on the code and report side, D38)
| What | Who | Ref |
|---|---|---|
| Fill the yellow fields of the report in REPORT.tex and REPORT.md (names of authors 5 and 6, affiliations, Author Contributions), then `bash report/final/build_tex.sh` | the authors | report/final/TODO_AUTHORS.md |
| Run `python3 report/final/check_final.py "Saying Yes Is Not Doing It: A Scripted Price-Fixing Offer to LLM Sellers"` (must end with "ERREURS: aucune") | authors | report/final/README_AUTHORS.md |
| Submit report/final/REPORT.pdf on the Apart form with the exact title, before Monday Oct 26, 11:59 UTC | authors | docs/apart/Guidelines.md |

Abandoned or closed by D38: remaining runs (0 USD, declared not run), frozen-file deviation lines (QUESTIONS #32), video (OPEN_ISSUES #23).

## Next action
Nothing on the code side. The authors fill report/final/TODO_AUTHORS.md, run the final check and submit before 11:59 UTC.
