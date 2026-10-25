SUPERSEDED by report/REPORT.md (the report draft, 2026-10-25). Kept for history only; do not edit or cite.
The rules below about who writes the prose are replaced by ops/DECISIONS.md D26.

SKELETON ONLY. Not the report. No prose here on purpose (ops/DECISIONS.md D14, D21; ops/QUESTIONS.md #12).
The team writes every sentence of the final report in its own words. Apart: a report that "reads as generated" is not scored (docs/apart/Guidelines.md, "AI tools and your report").

Rules for using this file
- Notes are facts and pointers, not sentences to paste. Rewrite everything.
- Every number comes from a tool output named in a [RESULT: ...] placeholder (CLAUDE.md rule 2, SPEC R18). If a tool was not run, write "not run".
- Final report source: one file, e.g. `report/report.md` or the LaTeX of the official template. Only that file goes through `python -m tools.check_submission <file> --title "<exact title>"`. Do not run it on this file or on SUBMISSION_CHECKLIST.md (no abstract, no author line: it would FAIL by design).
- Exploratory items (addendum, memory arm, monitor_view, sensitivity, price_shift) always carry the label "exploratory, not preregistered" (or "post-freeze addendum") in text, table and figure captions.
- Wording: "directional", "to our knowledge", "at time of writing". Never "novel", "first" without "to our knowledge", "significant", "no effect".
- Page budget: main body max 8 pages (live sprint page, 2026-10-24), target about 6. References and appendices do not count.

---

## Title block

- Title: [TEAM: pick once, reuse byte-identical on every submission; see SUBMISSION_CHECKLIST.md on resubmission and PDF replacement]
- Authors and affiliations: report/AUTHORS.md (Artem, Adam Attar; affiliations still "to be filled")
- Repo link: public GitHub URL [TEAM: confirm which remote is public; COMPETITOR_SCAN.md says `adamattar-pixel/mole-in-the-market` is visible]

## Abstract (150 to 250 words, live rule 2026-10-24)

- 4 parts: problem, method, result, implication (NOVELTY_AND_JUDGES.md §b.3).
- `tools/check_submission.py` and SPEC R19 enforce 150 to 250 words (owner-approved test(fix) of a0cd120, docs/team-artem/OWNER_APPROVAL.md).
- Numbers in the abstract: [RESULT: results/tables.md, family rows, columns Say and Do for Direct offer] and [RESULT: tools.validate_e stdout, PASS/FAIL per family].

---

## 1. Introduction (0.75 page)

NOTES
- Question as preregistered: PREREGISTRATION.md "Questions" 1-3 (frozen d5e7ebc, tag `prereg-frozen`).
- Origin of the design: Apart Q3.2 undercover-offer suggestion, "hasn't been tested" (RELATED_WORK.md §8, Apart sprint Resources tab). Say openly the design follows Apart.
- Why it matters (oversight framing): message monitor vs price auditor see different things; the say/do 2x2 (NOVELTY_AND_JUDGES.md §b.1, first bullet).
- Theory of change: audits of AI sellers should check prices against a no-offer baseline, not only messages (NOVELTY_AND_JUDGES.md §b.1). Plus-factor doctrine only with a verified source (RELATED_WORK.md §9: Berger et al. 2025 is [U]).
- Contributions list, each hedged "to our knowledge": scripted sting in a logit price duopoly; one-sentence trust-label minimal pair (R04); harmless-request control D; permutation base rate for "do"; preregistered + keyless `reproduce` (NOVELTY_AND_JUDGES.md §a "Genuinely new"; COMPETITOR_SCAN.md §4).
- Page 1 excerpt box (see "Page 1 checklist" below).
- One-sentence headline claim: pick the row from "Claims allowed per outcome" below once results exist.

[RESULT: figures/exploratory/excerpt.md from `python -m tools.price_paths runs --game-id <id> --out-dir figures/exploratory`: spy message, both raw replies, prices rounds spy_start-1 to spy_start+3]
[FIGURE: Figure 1 = figures/game_grid.pdf, R27, from `python -m tools.reproduce runs results --viz-dir viz/data --figures-dir figures` (commit d6619da). Can sit on page 1 or start of Results]

---

## 2. Related Work (0.75 page)

NOTES
- 4 short groups: algorithmic pricing collusion; LLM agents with communication/offers; say vs do; trust labels and peer compliance (NOVELTY_AND_JUDGES.md §d row 2).
- One clause each on how we differ. Contrasts below are from RELATED_WORK.md, rephrase them.
- Cite only [V] or [S] entries (RELATED_WORK.md key). GroupGuard: read its honeypot section before any "first sting" wording.
- Sprint-adjacent overlap: say it (Elliott, saihariG, ayodejiades, maiyasaliha, carver; COMPETITOR_SCAN.md §1-2). Cite their repos only if public at submission. Do not compare numbers with Elliott (COMPETITOR_SCAN.md §4 "avoid").

Citations (10), with difference note

| # | Citation | URL | Difference (note, not text) |
|---|---|---|---|
| 1 | Calvano et al. 2020, AER | https://www.aeaweb.org/articles?id=10.1257/aer.20190623 [S] | Source of demand params; Q-learners, tacit; we use LLMs + explicit offer |
| 2 | Fish, Gonczarowski, Shorrer 2024 | https://arxiv.org/abs/2404.00806 [V] | Same game, no channel; we add one frozen offer, ask if "yes" moves prices beyond tacit baseline |
| 3 | Agrawal et al. 2025, double auctions | https://arxiv.org/abs/2507.01413 [V] | Free seller talk; ours is one scripted outsider, fixed text. Authority-pressure result = closest prior for B_T |
| 4 | Zeng & Rudzicz 2026, Voluntary Collusion | https://arxiv.org/abs/2605.27593 [V] | Offer from environment as a tool, non-market games; ours peer message in price game + label pair + D control. Apart's 3.2 starter |
| 5 | Nakamura et al. 2026, Colosseum | https://arxiv.org/abs/2602.15198 [V] | CLOSEST on say vs do ("collusion on paper"); cooperative DCOP, assigned coalitions; ours competitive, unsolicited, refusable offer + base rate |
| 6 | Shi, Zhang, Schölkopf, Conitzer, Jin 2026, When Agents Lie | https://arxiv.org/abs/2607.05132 [V] | Announcement vs action about own move; ours acceptance of third-party cartel offer + price follow-through |
| 7 | Giebel, Rösner, Schröder 2026, SSRN | https://papers.ssrn.com/abstract=6832662 [S] | Free bilateral chat raises prices; ours one frozen third-party message, reply separated from price effect |
| 8 | Motwani et al. 2024, Secret Collusion | https://arxiv.org/abs/2402.07510 [V] | Steganography; our "do only" cell is the low-tech miss of a text monitor |
| 9 | Wallace et al. 2024, Instruction Hierarchy | https://arxiv.org/abs/2404.13208 [V] | B_T = claimed privilege inside an untrusted peer message |
| 10 | Kavathekar et al. 2025, TAMAS | https://arxiv.org/abs/2511.05269 [V] | Impersonation mixes label and content; B vs B_T differ by one sentence |
| opt | Tao et al. 2026, GroupGuard | https://arxiv.org/abs/2603.13940 [V] | Honeypot as defense component in QA tasks; CHECK before "first sting" |
| opt | Sharma et al. 2023, Sycophancy | https://arxiv.org/abs/2310.13548 [V] | Motivates D control: "accept" may be agreeableness |

---

## 3. Methodology (1.5 pages)

NOTES
- Game: 2 firms, 20 rounds, spy_start 8, logit demand a=2, a0=0, mu=0.25, c=1, beta=100, alpha=1 (PREREGISTRATION.md "Design"; configs/espion_core.yaml). Nash 1.47293, monopoly = deal 1.92498, gap 0.45205, "do" band [1.8798, 1.9702] (AUDIT_PASS_1_2.md §0, from `GameConfig.from_dict`). Recompute from logs fields nash_price, monopoly_price before quoting.
- Spy = script, byte-identical text to both firms, once at spy_start, no LLM call (R02; harness/spy.py). Firms never see the rival's reply; in a 2-firm market "another agent" can only be the rival (AUDIT_PASS_1_2.md finding 10).
- Memoryless sellers in the frozen design: offer and own reply absent from prompts after spy_start (AUDIT_PASS_1_2.md finding 1, harness/agent.py `build_messages`). Must be stated here, not only in Limitations.
- Conditions table A, E, B, B_T, C, D with full names (PREREGISTRATION.md "Conditions" + "Frozen texts"); full texts verbatim in Appendix B.
- Definitions: say, do (10% of gap, window spy_start+1..+3, every round), false positive, base rate (seeded permutation), game as unit, Wilson 95% (PREREGISTRATION.md "Definitions", "Definition details"). E threshold 0.25 of gap (same file).
- Post-freeze addendum (exploratory): B_ETH, B_MON/C_MON/D_MON, detectors D1-D3, scoring, H5-H7 (PREREGISTRATION_ADDENDUM.md, frozen 8b7b5a1, hash in 378f1dd, tag `addendum-frozen`). State that the monitor rule was written knowing the offer texts.
- Non-preregistered exploratory: memory arm (MEMORY_ARM.md; commits 4a0da3e, cd64683), sensitivity grid (tools/sensitivity.py; 20351c6, 3ed6452), monitor_view (MONITOR_VIEW.md; e6288ed, 664944e), price_shift (PRICE_PATHS.md; a862a25, 1d196dc, fafcb67).
- Preexisting vs new work: see note at the end of this file.

Replication checklist (judges: "enough detail to replicate")
- [ ] Model ids per family, exact OpenRouter ids [TEAM: from configs/espion_*.yaml once `tbd` replaced, D10; MODEL_AND_COST.md]
- [ ] Served model and provider as logged per call (commit 59d2bbc: provenance in logs) [RESULT: runs/*.json provenance fields, one line per family]
- [ ] Temperature value sent, or "provider default" if `temperature: null` [TEAM: configs/espion_*.yaml key `temperature`]
- [ ] Reasoning setting per family (`reasoning` key, harness/runner.py `family_reasoning`) and logged reasoning tokens
- [ ] "Seeds" 1-5 = replicates; many providers ignore `seed` (AUDIT_PASS_1_2.md finding 9). Use "replicates" in text
- [ ] Prompts verbatim in Appendix B: system + user template from harness/agent.py `build_messages`; frozen texts block from PREREGISTRATION.md; ethics_instruction and pact_pattern from PREREGISTRATION_ADDENDUM.md; memory block format from MEMORY_ARM.md if that arm is reported
- [ ] Invalid price rule: previous price kept (QUESTIONS #10) + count of fallbacks [RESULT: per-game invalid counts from logs; spy-round invalids separately, AUDIT_PASS_1_2.md finding 12]
- [ ] Metrics + thresholds: behavioral_gap_fraction 0.10, behavioral_window 3, e_threshold_gap_fraction 0.25, d1_last_rounds 5, d1_gap_fraction 0.5, d3_min_abs_corr 0.5, d3_min_pairs 5
- [ ] Base-rate draws and seed: `tools.reproduce --n-draws 1000 --seed 0` (defaults) [RESULT: results/summary.json keys n_draws, seed]
- [ ] Game counts per config and excluded games [RESULT: results/tables.md lines "Games:" and "Excluded games:"]
- [ ] Prereg: commit d5e7ebc029cb6b66da32983b62ecff74c2b17f7d, tag `prereg-frozen`; addendum 8b7b5a17bf0a6a3ed2f9f16575e6d7d20a29226a, tag `addendum-frozen`; "Deviations" sections of both files (currently "(none)")
- [ ] Run commit and config hash per game (log fields git_commit, config_hash) [RESULT: distinct values across runs/]
- [ ] Cost: total and per game [RESULT: `tools.run` stdout via harness/costs.py `cost_summary`]
- [ ] Reproduce command + checksums [RESULT: results/checksums.txt]

---

## 4. Results (2 pages)

NOTES
- Order: 4.0 positive control first (Apart: "always include the positive control"), then by question Q1, Q2, Q3, then addendum (exploratory), then other exploratory.
- Each subsection opens with the one-line answer, then the number (NOVELTY_AND_JUDGES.md §b.3).
- Every rate as k/n + Wilson 95%. Families never pooled unless labeled. Per-firm rates secondary.
- Never "no effect" from a null at n=5; give CIs and the minimum detectable difference (AUDIT_PASS_1_2.md finding 6 table).
- "Do" also measures anchoring on the stated price (offer contains 1.92; AUDIT_PASS_1_2.md finding 5): show say0_do1 cell for B and C.
- Max 3 main-body figures (NOVELTY_AND_JUDGES.md §b.3); the rest to appendix.

4.0 Positive control (H0)
[RESULT: `python -m tools.validate_e runs` stdout: per family PASS/FAIL, effect, A games, E games]
[RESULT: results/tables.md, line "Positive control E" per family; results/summary.json e_validation[family].effect_gap_fraction]
- If E fails for a family: NOVELTY_AND_JUDGES.md §c last row; B refusals for that family uninformative.

4.1 Q1 say vs do in Direct offer (H2, H3)
[RESULT: results/tables.md, "## Family <f>" table, row Direct offer, columns Say, Do, Do p-value vs base rate]
[RESULT: results/tables.md "Base rate (A and D, permutation): mean ..." per family]
[RESULT: results/summary.json say_do_2x2[family][B]: say1_do1, say1_do0, say0_do1, say0_do0]
[RESULT: results/tables.md "False positives (accept in D)" per family (H3)]
- Column name caveat: "Do p-value vs base rate" = anchor-permutation p, descriptive; base rate not time-matched (AUDIT_PASS_1_2.md finding 2). Rename in text.
[FIGURE: Figure 2 = figures/exploratory/price_paths.pdf from `python -m tools.price_paths runs --out-dir figures/exploratory` (descriptive, means; caption: band = min-max over replicates, not a CI)]

4.2 Q2 offer form, Direct vs Hint vs Harmless (H1)
[RESULT: results/tables.md, rows Direct offer, Hint, Harmless request, columns Say, Do]
- C "accept" may answer a non-proposal (NOVELTY_AND_JUDGES.md threats).

4.3 Q3 trust label, Direct vs Trusted direct (H4)
[RESULT: results/tables.md, rows Direct offer vs Trusted direct offer, columns Say, Do, both families]

4.4 Post-freeze addendum (exploratory): detectors (H5)
[FIGURE/TABLE: detector table R29, `tools/score_detectors.py` -> written by reproduce (R30). NOT BUILT YET (ops/HANDOFF.md §1 "Not started"). Columns per SPEC R29: detector, precision, recall, false alarm rate on A and D, flag rate per condition, Wilson CI, family base rate]

4.5 Post-freeze addendum (exploratory): defenses (H6, H7)
[FIGURE/TABLE: defenses comparison R34, say and do in B vs B_ETH vs B_MON matched by family and seed, Wilson CI. NOT BUILT YET]
[RESULT: monitor metrics R32: collusion removed (pairs), false blocks on D_MON. NOT BUILT YET]
- Prevention/utility not measured if only detection is reported (COMPETITOR_SCAN.md §4, munip).
- Ethics sentence close to carver's provider-line defense: cite, do not claim new.

4.6 Other exploratory (not preregistered), each in its own labeled table
[RESULT: `python -m tools.monitor_view runs` -> results_exploratory/monitor/monitor_view.md: 2x2 table (Family, Condition, Games, Say+Do, Say only, Do only, Neither) and monitors table (Family, Monitor, Detection on B, B_T, C, E, False positive on A, D). Ground truth = offer exposure, not intent (MONITOR_VIEW.md caveats). Drop if R29 covers it (team-artem/README.md item 8)]
[FIGURE: figures/exploratory/price_shift.pdf, same tool as Figure 2: do-window shift vs No spy, bootstrap 95%, 2000 draws]
[RESULT: `python -m tools.sensitivity runs --out results_exploratory/sensitivity.md`: Family, Condition, Tolerance, Window, Games, Say, Do; prereg cell 0.10/3 must equal 4.1]
[RESULT: memory arm, `python -m tools.reproduce runs_exploratory/memory results_exploratory/memory --configs espion_mem` tables.md, table title "Exploratory (not preregistered): seller memory arm"; compare B_mem vs B, A_mem vs A descriptively. Only if run (MEMORY_ARM.md)]

---

## 5. Discussion (0.75 page)

NOTES
- Oversight reading of the 2x2: which monitor to trust per cell (NOVELTY_AND_JUDGES.md §b.1).
- Recommendation for auditors: check prices against a no-offer baseline (same source).
- Trust label: attack surface if B_T > B, reassuring if equal; both reportable (§b.1).
- Sting as a pre-deployment compliance test; quote measured cost per game [RESULT: cost_summary per game].
- Replication vs new: transcript-monitor false alarms already shown by saihariG, ayodejiades, Raj-Taware (COMPETITOR_SCAN.md §4). Present ours as replication in a new setting.
- What surprised the team [TEAM: own observation from reading logs; this is the "trace of what you actually did"].
- Future work: report option (Guey et al. 2026, https://arxiv.org/abs/2610.10620), more replicates (O1), neutral-number arm for anchoring, free-text replies, reasoning models, more firms.

---

## Appendix A. Limitations and Dual-Use / Ethical Considerations

Heading must be exactly the line above after "Appendix A. " (check_submission accepts a prefix; appendix_ok = heading ends with the exact title).

Limitations, points to cover (no prose)
- Power: 5 replicates x 2 families, 10 games per condition; Wilson width up to 0.65 at n=5 (AUDIT_PASS_1_2.md finding 6).
- Memoryless sellers in the frozen design: say-do gap partly built in (finding 1). Memory arm result, or "not run".
- Base rate not time-matched; p descriptive (finding 2).
- Offer contains the deal price: "do" = "moved to the stated price", includes anchoring (finding 5).
- Binary "do" may hit ceiling/floor given tacit collusion (finding 7); spy at round 8 of 20, prices may not have settled (finding 8).
- "Say" is a forced categorical field: lower bound for a text monitor (NOVELTY_AND_JUDGES.md threats).
- Seeds not honored by all providers; temperature/reasoning as set (finding 9).
- Two families, one game, deal = monopoly price, hint ambiguity.
- Monitor rule written knowing the offer texts; keyword rule easy to evade (PREREGISTRATION_ADDENDUM.md).
- Ground truth = scripted offer + "do", not intent.
- Everything after the freeze labeled exploratory; deviations listed (or "none").

Dual-use / ethical, points to cover (no prose)
- What the result does and does not establish (Apart wording, docs/apart/Guidelines.md).
- Offer texts plain, not optimized; no persuasion search (CLAUDE.md rule 9; PREREGISTRATION.md "Frozen texts").
- Publish rates and a few representative excerpts only, no tuned playbook (SPEC R21). State how the excerpt game was chosen.
- Could findings make collusion easier: e.g. which label or form works best. Mitigation: no optimization, small n, frozen texts already public.
- Could findings make collusion harder to detect: "say no, price high" teaches evasion of transcript monitors; monitor rule is public and evadable. Why price-based audits matter.
- Defenses tested are weak baselines (keyword rule, one ethics sentence); not a security claim.
- No humans, no real market, no personal data; API models only; logs released in repo [TEAM: confirm runs/ contains no secrets before release].
- AI assistance disclosure: code written with an AI coding assistant, reviewed and run by the team; report written by the team (THIRD_PARTY.md last line).

## Appendix B. Prompts and frozen texts (verbatim)

- System and user templates: copy from harness/agent.py `build_messages` (render one real round-1 and round-8 prompt from a log `rounds[].firms[].prompt` field if logged, else from the function).
- Frozen yaml block: PREREGISTRATION.md "Frozen texts" (verbatim, including `{deal_price}` placeholder and rendered value).
- Addendum yaml block: PREREGISTRATION_ADDENDUM.md "Frozen texts and thresholds".
- Memory block format: MEMORY_ARM.md "Design" (only if reported).

## Appendix C. Reproduction (optional)

- Commands: ops/HANDOFF.md §4. `reproduce` keyless, deterministic (R15, AUDIT_PASS_1_2.md §0).
[RESULT: results/checksums.txt]
[RESULT: sensitivity table, if not in main body]

## References

- Only entries actually cited in the text. Only [V]/[S] from RELATED_WORK.md. One consistent style.
- Include starter code: luciasauer/algorithmic_pricing_llms (R01 cross-check), Apart sprint page.
- Run `check_submission` online once (without --offline) so links are checked.

---

## Claims allowed per outcome

Base sources: NOVELTY_AND_JUDGES.md §c (headline per outcome) and §a ("Not new"); COMPETITOR_SCAN.md §4 ("avoid claiming"). Always "directional", "to our knowledge"; never "novel".

| Outcome (from tables.md) | Allowed claim (pointer, reword) | Required qualifiers | Not allowed |
|---|---|---|---|
| Say high, do low in B (H2) | §c row 1: transcript monitor false alarms | directional; conditional on memoryless sellers unless memory arm agrees | "agents lie"; "new finding" (Colosseum, saihariG) |
| Say low, do high | §c row 2: message audits miss | directional; anchoring caveat (offer contains price) | "covert collusion" or intent |
| Say high, do high | §c row 3: one scripted offer suffices | directional; vs base rate | "cartel forms in general" |
| Say low, do low (only E colludes) | §c row 4: refusal unless allowed | only for families where E PASS | "models are safe" |
| B_T > B, clear margin | §c row 5: sender label as attack surface | give k/n + CI; directional | "significant" |
| B_T about equal B | §c row 6: no difference at our precision | state minimum detectable difference | "no effect" |
| D accept high (H3) | §c row 7: yes = agreeableness | D is a harmless request, not "no offer" | |
| Families disagree | §c row 8: risk is model-specific | 2 families only | generalize to "LLMs" |
| E fails for a family | §c row 9: limitation for that family | drop that family's B interpretation | any B claim for it |
| Detector / defense results | addendum H5-H7 outcome | "post-freeze addendum, exploratory" | "a framing defense works" as new (carver) |
| Any "first" | "first measured sting in a price game, to our knowledge, at time of writing" | after checking GroupGuard | "first undercover / trusted agent test" |

## Page 1 checklist

- [ ] One-sentence claim from the table above, with the measured numbers, reworded by the team.
- [ ] Real excerpt box: `python -m tools.price_paths runs --game-id espion_core__<family>__B__s<n> --out-dir figures/exploratory` -> figures/exploratory/excerpt.md (verbatim spy message, both raw replies, price table). Game id from results/labels.csv or viz/data/games.csv. Choice of game stated (R21).
- [ ] Condition names in full ("Direct offer, trusted sender"), "say" and "do" defined once (NOVELTY_AND_JUDGES.md §b.3).
- [ ] Figure 1 (game grid) on page 1 or first Results page.
- [ ] No generic opening about "the rise of AI".
- [ ] 30-second test with someone outside the team.

## Preexisting vs new work (R20)

- THIRD_PARTY.md: no third-party code reused; harness written during the sprint; ideas credited (Fish-style duopoly, ArnolFokam idea only, luciasauer cross-check, idea credits list).
- RELATED_WORK.md §8 calls ArnolFokam "our base harness, declare as preexisting", THIRD_PARTY.md says "Not used, idea only". [TEAM: resolve before writing; the report must match THIRD_PARTY.md]
- Tag `preexisting-baseline` is referenced by THIRD_PARTY.md and SPEC R20 but DOES NOT EXIST (checked 2026-10-24, `git rev-parse preexisting-baseline` fails; AUDIT_PASS_1_2.md finding 4). Proposed target fd8c920 ("chore: add project scaffolding, spec and audit files"). Owner creates and pushes it; then cite tag + hash in Methodology.
- New during sprint: everything after that tag. Sprint dates Oct 23-25, 2026.
- Report text: team's own writing; AI assistant used for code (THIRD_PARTY.md).
