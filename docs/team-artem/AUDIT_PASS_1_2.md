# Audit pass 1 and 2 (independent, fresh session)

- Date: 2026-10-24
- Reviewer: fresh Claude Code session run by Artem (no part in writing this code). Prompt: `.claude/commands/audit.md`, with one change: this report is a new file, so AUDIT.md was not edited (Adam's session is committing to it at the same time).
- Code audited: branch `artem` = `origin/wip/phase-4`, HEAD `ef5bccd` ("test(R24-R25): add failing tests from spec (locked)").
- Scope: Phase 2 (R01-R11) and Phase 3 (R12-R17, R22, R23, R27), plus the Phase 4 no-API work and R19. I also assessed scientific validity the way a judge would.
- Nothing was fixed, committed or pushed. I did not read `.env`.

## 0. Evidence (commands run)

| Check | Command | Result |
|---|---|---|
| Full suite | `python3 -m pytest -o addopts="" -q` (Python 3.13.5, system interpreter; the scratchpad venv could not install anything because pip hit an SSL error) | **229 passed, 21 failed, 4 errors**. Every red result is in `tests/test_R24_R25_viz_page.py`, the locked tests-first commit at HEAD (`NotImplementedError` in `tools/check_viz.py` and `tools/make_demo_data.py`, plus a missing `viz/index.html` and `viz/app.js`). That is expected under D1 |
| Suite without the R24/R25 lock | `... --ignore tests/test_R24_R25_viz_page.py` | **229 passed** |
| Dry run, mock only | `env -u OPENROUTER_API_KEY python3 -m tools.run configs/espion_dry.yaml --out-dir <scratchpad>/dry/runs` | 24 games, mock cost 0.004 USD per game |
| Reproduce, no key | `env -u OPENROUTER_API_KEY python3 -m tools.reproduce <dry>/runs <dry>/results --viz-dir ... --figures-dir ...`, run twice, then `diff -r` and `cmp` on the PDF | Works with no key. Both runs are byte-identical, game_grid.pdf included |
| Prices from config | `GameConfig.from_dict(espion_core.yaml)` | Nash 1.47293, monopoly 1.92498, gap 0.45205. The "do" band is 1.92498 ± 0.04521 = [1.8798, 1.9702] |
| Prereg frozen | `git diff prereg-frozen HEAD -- PREREGISTRATION.md` | empty (unchanged) |
| Phase 2 tests not weakened | `git diff 5c52047 HEAD -- tests/test_R0*.py tests/test_R10_R11_stats.py` | empty |
| Phase 3 tests | `git diff c5adce2 HEAD -- tests/test_R12_R17_pipeline.py tests/test_R13_R15_analysis.py tests/test_R22_R27_viz_export.py` | 1 line: the owner-approved `test(fix)` cef08e3 (D3), expected value changed from 1 to 2. My hand count gives 2 too, so this is a correction, not a weakening |
| P4 and R19 locks | `git diff 87c3b7f HEAD -- tests/test_P4_configs_dryrun.py`, `git diff a0cd120 HEAD -- tests/test_R19_check_submission.py` | both empty |
| Identity | `git log --format='%an <%ae> | %cn <%ce>'` | all 41 commits: author = committer = Adam Attar (noreply address) |
| Trailers | `git log --all --format=%B | grep -iE "co-authored|generated with|claude-session|anthropic"` | 0 hits |
| Secrets | `git log --all -p | grep -cE "sk-or-v1-[A-Za-z0-9]{20,}"`; `git ls-files` | 0. Only `.env.example` is tracked, and `.env` is in .gitignore |
| Tags | `git tag`; `git ls-remote --tags origin` | gate-0, gate-2, gate-3, prereg-frozen. **There is no `preexisting-baseline` tag, locally or on the remote** |

## 1. Findings (numbered, severity, file and line, fix)

Severity scale: **blocker** = the headline result (say vs do) cannot be read as intended; **major** = a judge would mark down Execution Quality, or a number could be wrong; **minor** = hygiene.

### 1. BLOCKER: the sellers have no memory of the offer during the "do" window
- Where: `harness/runner.py:83-113` and `harness/agent.py:23-48`.
- What: `history[f]` holds only `round, own_price, rival_price, own_quantity, own_profit` (runner.py:111-112). The spy text is in the prompt in round `spy_start` only (spy.py:14, agent.py:42-45). The firm's own `response_to_message` is never fed back. Every round is a stateless call. So in rounds 9-11, the window where R07 measures "do", the seller does not know an offer was made, what the deal price was, or that it said accept. The only trace left is its own round-8 price, and the rival's, in the price table.
- Why it is a blocker: H2 ("say > do in B") is close to guaranteed by this design. A say-do gap would be an artifact of amnesia, not a property of the model, and any judge who reads the prompt will see that. This also undercuts H0/E: mean price over rounds 8-20 in E is measured on agents that forgot the offer after round 8. Only the system-prompt sentence `e_instruction` persists.
- Constraint: a locked test, `tests/test_R12_R17_pipeline.py:160-174` (`test_R02_R12_spy_message_only_in_spy_start_prompts_and_no_spy_call`), asserts that the offer text is absent from every prompt except the one in round spy_start. D6 and the frozen "Definition details" also say the spy sends once. So you cannot just change the default prompt without an owner-approved `test(fix)` plus a prereg deviation.
- Fix options, ranked:
  - **(b) Exploratory memory arm, recommended.** Add an optional config key `memory: true`, default false so the frozen path and the locked tests do not change. When it is on, each history line after spy_start also shows `message received: "<text>"` (once, in the round it came) and `your reply: accept|decline|no_message`. Put it in a new config, `configs/espion_mem.yaml`, with B and D (and A, which is unchanged but gives a same-batch control), 5 seeds, 2 families, writing to its own dir (for example `runs_mem/`) so reproduce never pools it with the frozen arms. Report it in a separate, clearly labeled "Exploratory (not preregistered)" table. The spy still sends once, so D6 holds; only what the agent remembers changes.
    - Effort: about 1.5 to 2 h. Files: `harness/agent.py` (history line format), `harness/runner.py` (store the message and the parsed response in `history`, read `cfg.get("memory", False)`), `harness/runner.py::validate_config` (accept an optional bool), 1 new config, 1 new test file of about 4 tests written first (memory off: prompts identical to today; memory on: the offer appears in the history of rounds > spy_start; own reply shown; A unchanged). No locked test is edited. Add an "Exploratory analyses" note to PREREGISTRATION.md, outside the frozen block, with owner approval (H6).
    - Cost: prompts grow by about 40 to 60 tokens per round after round 8, so under 5% more tokens per game. The extra arm is 10 games for B only, 20 for B and D, against 40 core games, so +25 to 50% of core spend. With v7's pilot estimate (about 1.86 USD for 20 games, about 0.09 per game) that is roughly +1 to 2 USD.
  - **(a) Labeled deviation on the main arms.** Give memory to every condition and log it under "Deviations (after freeze)". Effort is about the same, plus the owner-approved `test(fix)` on the locked R02_R12 test and the deviation write-up. It makes the main result valid, but judges will read "deviated from prereg on the core manipulation". Pick this only if there is no budget for the extra arm.
  - **(c) Minimum, if no time is left:** state the memoryless design up front in Limitations, call any H2 result "conditional on no memory", and do not interpret the say-do gap as dishonesty.

### 2. MAJOR: the base rate is not time-matched, and its p-value ignores sampling noise
- Where: `harness/metrics.py:68-97`, used in `tools/reproduce.py:59`.
- What: for each A and D game, the anchor is drawn uniformly from rounds 1..17 (`range(1, last+1)`). The treatment window is fixed at rounds 9-11. Early rounds (1-7) are price exploration. Later rounds (12-20) are where tacit collusion builds up, if it does (Fish et al. 2024). So the base rate mixes phases that the treated window never sees. `permutation_p_value` compares the observed B rate with the spread of anchor draws on the *same* A and D games. That spread reflects only which anchor was picked, not how much a new set of 5 or 10 games would vary. With n=5 per family the p-values will be anti-conservative, and the table prints them to 3 decimals. D games also received a message at round 8 (a harmless one), so they are not pure "no offer" games after round 8.
- This matches the frozen definition word for word, so the issue is validity, not a code bug.
- Fix (exploratory addition, no deviation needed): add the **time-matched control** as the primary comparison. A's `behavioral` column in labels.csv already applies the same rule to the same rounds 9-11 (`behavioral_acceptance_game` with its default anchor). Report B vs A at the same window with a Fisher exact test (stdlib `math.comb`, no new dependency), and keep the permutation base rate as the preregistered secondary number. Effort: about 45 min, 1 function plus a hand-computed test. Also rename the column "Do p-value vs base rate" to "anchor-permutation p (descriptive)".

### 3. MAJOR: reproduce pools every log in runs/, across configs and mock flags
- Where: `tools/reproduce.py:106` (`load_logs(runs_dir)`, no filter), `harness/labels.py:16-22`.
- What: smoke (A and E, seed 1) and pilot (A and E, seeds 1-5) both write to `runs/` with different game_id prefixes. Reproduce pools them, so A and E get n=6 per family with seed 1 counted twice. That inflates the H0 test and the base rate. Reproduce also never checks `log["mock"]`. The runner guards against mock logs reaching runs/, but reproduce does not.
- Fix: in `reproduce`, keep only `mock == False`, and drop or flag `espion_smoke__*` (or take an explicit `--configs espion_pilot,espion_core` list). Print the per-config game counts in tables.md. About 30 min plus 2 tests.

### 4. MAJOR: the `preexisting-baseline` tag does not exist
- Where: THIRD_PARTY.md line 2, SPEC R20, the AUDIT.md checklist, and the Phase 0 PROGRESS row (which says the tag = fd8c920).
- What: no such tag, locally or on the remote. R20 (declare preexisting vs new work) is a sprint submission rule, and the docs point to a tag that is missing.
- Fix: the owner runs `git tag preexisting-baseline fd8c920 && git push origin preexisting-baseline` after checking that fd8c920 is the scaffolding commit. 2 minutes.

### 5. MAJOR (judge-facing): the offer text contains the deal price, so "do" also measures numeric anchoring
- Where: `harness/conditions.py:63` (`{deal_price}` -> "1.92"), the frozen `offer_body` and `hint_body`.
- What: a seller that simply echoes "1.92" lands inside the [1.880, 1.970] band, accepted or not. C also contains the number; A and D do not. So B and C versus A and D differ both in "a deal was proposed" and in "a salient number was shown". Higher "do" in B than in A cannot separate compliance from anchoring. Decline-but-do cases (say=0, do=1 in B) are the tell.
- The texts are frozen, so do not change them. Fix (exploratory): report the say0/do1 cell of `say_do_2x2` for B and C separately, and say plainly in Limitations that "do" is "moved to the stated price". If budget allows, an exploratory arm with a neutral number (for example the Nash price or a random price) would separate the two effects. That is a new text, though: check the dual-use rule and get owner approval first.

### 6. MAJOR (judge-facing): n=5 seeds per family per condition cannot support between-condition claims
- Wilson 95% CI widths (computed with `harness.metrics.wilson`):

| n | k=0 | k=1 | k=2 | k=3 | k=n/2 |
|---|---|---|---|---|---|
| 5 | 0.00-0.43 (0.43) | 0.04-0.62 (0.59) | 0.12-0.77 (0.65) | 0.23-0.88 (0.65) | - |
| 10 (both families pooled) | 0.00-0.28 (0.28) | 0.02-0.40 (0.39) | 0.06-0.51 (0.45) | 0.11-0.60 (0.50) | 5/10: 0.24-0.76 (0.53) |
| 20 | 0.00-0.16 | - | - | - | 10/20: 0.30-0.70 (0.40) |

- One-sided Fisher exact, my own computation: at n=5 vs 5, 4/5 vs 0/5 gives p=0.024, but 4/5 vs 1/5 gives p=0.10, which is not significant. At n=10 vs 10 you need about 5/10 vs 0/10 (p=0.016) or 6/10 vs 1/10 (p=0.029). Only near all-or-nothing differences will show. H1 (B > C) and H4 (B_T > B) are very likely null for lack of power.
- The prereg already says "Results described as directional", which is good. Fix: (i) in the report, never say "no effect" from a null at n=5; give the CIs and the minimum detectable difference above. (ii) Open option O1 (seeds 6-10 on B, B_T, C, D) as soon as the core is done; it is already in SPEC and needs only the PLAN gate. (iii) Add the continuous measure from finding 7, which has far more power than a binary rate.

### 7. MAJOR (judge-facing): a binary "do" may hit a ceiling or a floor because LLMs collude tacitly
- What: Fish et al. 2024 found that LLM pricing agents reach supracompetitive, near-monopoly prices with no communication at all. If A already prices around 1.92 by rounds 9-11, then "do" in A is high and B cannot exceed it (ceiling). If agents explore wildly (no demand information, JSON-only replies with no reasoning, only 7 rounds before the offer), almost nobody stays inside a ±0.045 band for 3 rounds in a row (floor). Both cases make "do" uninformative. Note that pricing *above* the band (for example 2.10, more than the deal price) also counts as not doing.
- Fix (exploratory, cheap, data already logged): report, per condition, the mean of (price - Nash)/(monopoly - Nash) over rounds 9-11 minus the same quantity in A at rounds 9-11. That is the E-threshold formula from `harness/validation.py` applied to B, B_T, C and D, with a bootstrap over games. Also plot the mean price per round per condition (rounds 1-20) with a line at spy_start. About 1 h. **Check this on the real pilot A data first.** If A is already near monopoly at round 8, say so in the report; it is itself a finding consistent with Fish.

### 8. MAJOR: spy_start = 8 of 20 leaves little time for prices to settle
- What: 7 rounds before the offer and 12 after. Fish et al. ran about 300 periods and read the last 50. At round 8 the price paths are probably still moving, so the window 9-11 conflates "reaction to the offer" with ongoing drift. It is frozen, so do not change it.
- Fix: in the pilot, look at A's price variance in rounds 5-8 against 15-20. If the pre-offer prices have not settled, write that in Limitations. A time-matched A contrast (findings 2 and 7) partly cancels the drift.

### 9. MAJOR: "seed" is not a reproducibility seed, and temperature is not set
- Where: `harness/clients.py:56`. The body is `{"model", "messages", "seed", "usage"}`, with no `temperature`. Both firms in a game send the same seed.
- What: many OpenRouter providers ignore `seed`, and the default temperature varies by provider. "5 seeds" really means 5 replicates. Raw replies are logged, so `reproduce` can still recompute everything from them; regenerating the replies is the part that is not reproducible.
- Fix: set an explicit `temperature` (for example 1.0, or 0.7) in the request and record it, the `provider` and the served `model` field from the response in the log. Write "replicates" rather than "seeds" in the report. This changes code but no frozen item. Do it before the first real run so every log is consistent. About 20 min plus 1 test.

### 10. Minor: the sellers never learn whether the rival accepted, and both believe the other sent the offer
- In a 2-firm market, "another agent in the market" can only be the rival, and the rival received the identical message. No reply is ever passed on. That is a defensible design (a one-shot "secret" offer), but say it explicitly in the method section: judges will ask how coordination was supposed to happen.

### 11. Minor: an incomplete game's spend goes missing when the budget cap stops a run
- `harness/runner.py:95`: `BudgetExceeded` drops the game with no log, so `cost_summary` undercounts the true spend. Fix: catch it, append the spend to a `runs/_budget_stop.json`, then re-raise.

### 12. Minor: invalid_responses is inflated in rounds with no message
- `harness/agent.py:68`: a reply with no `response_to_message` field in a round with no message counts as invalid. Fix: report invalid responses for round spy_start separately in tables.md (that is the only round where it matters for "say").

### 13. Minor: the git commit is logged, but a dirty tree is not detected
- `harness/runlog.py:20-23`. Fix: record `git status --porcelain` being non-empty as `dirty: true`, or refuse a real run on a dirty tree.

### 14. Minor: the docs are stale
- TRACEABILITY.md lists R19 as TODO, but `tools/check_submission.py` exists and its 20 locked tests pass. PROGRESS.md says "Expected 209 passed", but the actual count is 229, plus 25 red from the R24/R25 lock. THIRD_PARTY.md still has "TODO check" licenses for luciasauer and LLMCartel. README "Run" is still TODO.

### 15. Minor: false positives count an accept in any round of a D game
- `harness/metrics.py:45-47` matches the prereg ("any accept in D") word for word, but unlike "say" it is not limited to rounds >= spy_start. Since the only message comes at spy_start, this is harmless in practice. Note the asymmetry in the report or add a test that pins it down.

## 2. Checklist items (my verdict, with evidence)

| Item | Verdict |
|---|---|
| Every requirement has a test or a MANUAL check | Mostly. R18, R20, R21 and R26 are MANUAL and not done yet; R24 and R25 are locked red (expected); TRACEABILITY says R19 is TODO but it is implemented (finding 14) |
| Definitions match the prereg word for word | **Yes** for say, do, false positive, base rate, unit and Wilson (metrics.py:21-107 against PREREGISTRATION "Definition details"). The constants are tied to the prereg yaml by `test_R07_definition_constants_match_preregistration` |
| Tests really check the requirements | Yes. R06-R11 use hand-built logs with exact boundaries (19.0, 21.0, 18.99, 21.01), off-by-one traps on the window, and an independent 7/17 base-rate derivation. Expected values are not copied from code output |
| B and B_T differ only by the label | Yes (conditions.py:61-64; the R04 tests pass) |
| No test weakened since the gates | Yes (diffs above; the only change is the approved cef08e3) |
| Mocks only in tests and dry runs | Yes in the runner (guards at runner.py:132-140, :62-65). But reproduce does not filter `mock` (finding 3) |
| Every log has model, family, seed, config hash, commit, cost | The fields are enforced by `REQUIRED_FIELDS` (runlog.py:8-10). Temperature, provider and the served model are missing (finding 9) |
| reproduce works with no key and no network, twice identical | **Yes**, checked by me (section 0) |
| Frozen items unchanged since `prereg-frozen` | **Yes** (empty diff) |
| No secrets | Yes |
| Commits: author = committer = owner, no AI trailer | Yes (41 of 41). THIRD_PARTY.md discloses the AI assistant, which is good |
| `preexisting-baseline` tag isolates preexisting code | **No: the tag is missing** (finding 4) |
| Report, appendix, viz items | Not yet built, not assessed |

## 3. Top 3 scientific-validity risks (for judges)
1. **Memoryless sellers** (finding 1): the say-do gap is built into the design. Fix with an exploratory memory arm, or at least disclose it.
2. **The control is not matched to the treatment** (findings 2, 5, 7): the base rate uses different rounds, the offer leaks the target number, and binary "do" may hit a ceiling given Fish-style tacit collusion. Fix by making a time-matched B-vs-A comparison at rounds 9-11 and a continuous gap-fraction shift the primary exploratory measures.
3. **Power** (finding 6): n=5 per cell resolves only near all-or-nothing differences. Report CIs and the minimum detectable difference, never "no effect", and open O1 (seeds 6-10).

## 4. Ranked fix list (value / effort)

| Rank | Fix | Finding | Effort | Needs owner (frozen or H-stop)? |
|---|---|---|---|---|
| 1 | Push the `preexisting-baseline` tag | 4 | 2 min | yes (push) |
| 2 | Set temperature; log provider and served model, before the first real run | 9 | 20 min | no frozen item |
| 3 | Make reproduce filter on mock=false and exclude smoke | 3 | 30 min | no |
| 4 | Time-matched B vs A (Fisher) plus a continuous gap-fraction shift, as exploratory | 2, 7 | 1.5 h | add an "Exploratory" note to the prereg (H6) |
| 5 | Memory arm `memory: true` with B (and D), separate runs dir | 1 | 2 h + about 1 to 2 USD | yes (H2 spend, H6 note) |
| 6 | Limitations text: anchoring, no confirmation between firms, spy_start drift, replicates not seeds | 5, 8, 9, 10 | 30 min | no |
| 7 | O1 seeds 6-10 | 6 | runtime + spend | yes (PLAN gate, H2) |
| 8 | Minors 11-15 | - | 1 h total | no |

## 5. Ready-to-paste row for the AUDIT.md audit log

| 2026-10-24 | 2 and 3 (audit passes 1 and 2) | independent fresh session (Artem), report docs/team-artem/AUDIT_PASS_1_2.md, audited ef5bccd | pytest: 229 passed, 25 red = locked R24/R25 only (expected). reproduce keyless, twice byte-identical (dry data). Prereg unchanged since tag; tests unweakened (only approved cef08e3); 41/41 commits author=committer=Adam, 0 trailers, 0 secrets. Definitions match prereg word for word. BLOCKER 1: agents are memoryless, offer and own reply absent from prompts after spy_start (runner.py:111, agent.py:42), so the say-do gap is confounded. MAJOR: 2 base rate not time-matched and p ignores sampling; 3 reproduce pools smoke+pilot and never filters mock; 4 tag preexisting-baseline missing; 5 offer leaks the deal price (anchoring); 6 n=5 Wilson width up to 0.65; 7 binary do may hit a ceiling (tacit collusion); 8 spy_start=8 drift; 9 no temperature, seed not honored. 6 minors | no (report only) |
