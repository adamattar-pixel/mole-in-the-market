# team-artem: Artem's contributions (branch `artem`)

Everything here lives in new files, so it never conflicts with the phase work on `wip/phase-*`. Code changes sit in small commits that can be cherry-picked one at a time.

## Note for Adam (read first)

1. **Blocker before real runs: the sellers have no memory.** `harness/runner.py` builds the history from prices only. The offer is shown once, in round `spy_start`, and the seller's own accept is never fed back. In the "do" window (rounds 9 to 11) the seller cannot see the deal price, or even that it accepted. A say-do gap is therefore partly built into the design. The frozen design is left as is. Branch `artem` adds an opt-in `memory` flag and an EXPLORATORY arm (A, B and D with memory), which writes to `runs_exploratory/memory/` and is kept out of the preregistered tables. See [MEMORY_ARM.md](MEMORY_ARM.md). Proposed use: run it next to the core, and report it as a declared exploratory analysis (a suggested Deviations line is in MEMORY_ARM.md).
2. **`reproduce` mixes smoke and pilot games and does not filter mock games.** A fix is on branch `artem-reproduce-filter` (see FIXES.md once merged).
3. **No temperature, no reasoning control, no record of which model was actually served.** Newer models (GPT-5.x and 6, Claude 4.5 and later) reason by default. A fix is on branch `artem-client-settings` (see FIXES_CLIENT.md). Your decisions: the temperature value and the reasoning effort.
4. **Model choice (D10).** See [MODEL_AND_COST.md](MODEL_AND_COST.md). Recommended: `openai/gpt-5.4` + `meta-llama/llama-3.3-70b-instruct`, about $14 for the full 124-game plan with a 3x margin. Optional exploratory third family: `anthropic/claude-haiku-4.5`, about $5. Artem has an $80 Anthropic key that can be used through OpenRouter BYOK.
5. **Rules that changed on the live sprint page (checked 2026-10-24):**
   - The abstract is now **150 to 250 words**. R19 and `docs/apart/` still say "150 or fewer".
   - Resubmitting with the same title replaces the form details but **not the PDF**. A new PDF needs a slightly different title, or an email to sprints@apartresearch.com before the deadline.
6. **Novelty risk.** Apart's own suggested 3.2 weekend project is almost our core design. Our novelty claim rests on four things: the trust-label pair B vs B_T, the harmless-request false-positive control, the base rate for "do", and (if we run it) the memory arm. See [NOVELTY_AND_JUDGES.md](NOVELTY_AND_JUDGES.md).
7. **Repo hygiene.** The `preexisting-baseline` tag is missing on the remote (the audit suggests tagging fd8c920). Artem's GitHub account (Aku-90210) has pull-only access. Please add him as a collaborator so he can push `artem` and open PRs.

8. **Overlap with your R28 to R36 (seen 2026-10-24, after `378f1dd`).** `tools/monitor_view.py` (message-only vs action-only vs combined monitors, scored on offer exposure) was built before your detector plan. Your R29 `score_detectors.py` is the official version. Keep monitor_view only if it adds something (it scores on offer exposure rather than on offer AND do), otherwise drop it. The memory arm is not in the frozen addendum, so it can only be reported as a non-preregistered exploratory analysis, unless you freeze a second addendum before running it.
9. **Merge status.** `artem` already merges `origin/wip/phase-4` at `378f1dd` with no conflicts: 340 passed, 0 red. Until Artem can push, `~/Code/artem-for-adam.bundle` on Artem's machine holds the commits (`git fetch artem-for-adam.bundle artem:artem`).

## Files

| File | What |
|---|---|
| [AUDIT_PASS_1_2.md](AUDIT_PASS_1_2.md) | Independent audit, passes 1 and 2 (fresh session), with a ready-to-paste ops/AUDIT.md row |
| [MEMORY_ARM.md](MEMORY_ARM.md) | Exploratory seller-memory arm: design, separation, how to run |
| [MODEL_AND_COST.md](MODEL_AND_COST.md) | Token counts from the real prompt, OpenRouter prices (fetched 2026-10-24), model pair recommendation |
| [RELATED_WORK.md](RELATED_WORK.md) | About 40 related works with checked URLs and how we differ |
| [NOVELTY_AND_JUDGES.md](NOVELTY_AND_JUDGES.md) | Honest novelty check, the rubric dimension by dimension, headline claims per outcome, report outline (bullet material only, D14) |

## Code commits on `artem` (all tests-first, locked tests untouched)
- Memory arm: `4a0da3e` (tests), `cd64683` (feat), `5263663` (docs)
- Sensitivity grid `tools/sensitivity.py` (exploratory, zero cost): `20351c6` (tests), `3ed6452` (feat)
