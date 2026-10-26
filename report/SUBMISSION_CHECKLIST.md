Submission checklist (working list, not the report). Do not run tools/check_submission.py on this file.

Sources: docs/apart/Guidelines.md (copied before the sprint) and the live sprint page as checked 2026-10-24. Where they disagree, the live page wins and is marked LIVE.

## Official pre-submission checklist (docs/apart/Guidelines.md)

- [ ] Report PDF on the official Apart template (link on the Guidelines tab; not the one in any acceptance email)
- [ ] Project title and abstract (LIVE: 150 to 250 words)
- [ ] Author names and affiliations (report/AUTHORS.md; affiliations still to fill)
- [ ] Appendix "Limitations and Dual-Use / Ethical Considerations" present
- [ ] Links work
- [ ] What is new work during the sprint is clearly identified (undisclosed prior work can lead to disqualification)
- [ ] Report is the team's own writing (generated-looking reports are not scored)
- [ ] Submitted through the official form on the sprint page before Sun Oct 25, 11:59 PM AoE (Mon 11:59 UTC)
- [ ] Optional: public GitHub repo link; 3 to 5 minute video

## LIVE rule updates (sprint page, 2026-10-24)

| Rule | Live value | Repo state | Action |
|---|---|---|---|
| Abstract length | 150 to 250 words | tools/check_submission.py MIN/MAX_ABSTRACT_WORDS = 150/250, SPEC R19 "150 to 250" (owner-approved test(fix) of a0cd120, docs/team-artem/OWNER_APPROVAL.md) | check_submission enforces 150 to 250 |
| Page limit | template recommends 4 pages; max 8 pages, excluding references and appendices | check_submission: "page count: MANUAL" | Count on the compiled PDF |
| Appendix title | exactly "Limitations and Dual-Use / Ethical Considerations" | APPENDIX_TITLE matches; a prefix like "Appendix A." is accepted | Keep the exact string |
| Resubmission | same title does NOT replace the PDF (form details only) | Guidelines.md still says files are replaced | New PDF needs a slightly different title, or email sprints@apartresearch.com before the deadline. Get the PDF right the first time |

## Repo checks before submitting

- [ ] `python3 report/final/check_final.py "Saying Yes Is Not Doing It: A Scripted Price-Fixing Offer to LLM Sellers"` (online, so links are checked; it compiles REPORT.tex and runs check_submission on it with the exact title "Saying Yes Is Not Doing It: A Scripted Price-Fixing Offer to LLM Sellers"). Expected: all OK (abstract must be 150 to 250 words)
- [ ] Every number traced to a source (SPEC R18): `python -m tools.check_numbers <report file> --sources results results_exploratory --allow 0.10 10% 0.25 0.5 1.47 1.473 1.47293 0.45205 1.8798 1.9702 1.925 3.3 3.8`; each remaining line must be a cited hand computation or log value (docs/adam/DRAFT_NUMBERS_CHECK.md)
- [ ] `python -m tools.reproduce runs results --deviations run_all_deviations.json --viz-dir viz/data --figures-dir figures` rerun at the submission commit; results/checksums.txt unchanged; figures in the PDF match
- [ ] Positive control E reported per family on the pilot only (`python -m tools.validate_e runs --config espion_pilot`: Llama PASS 0.929, Haiku FAIL 0.111). Never quote the pooled run without --config (it prints Haiku PASS 0.277, OPEN_ISSUES #24)
- [ ] Exploratory items labeled; Deviations sections of PREREGISTRATION.md and PREREGISTRATION_ADDENDUM.md quoted (or "none")
- [ ] Preregistration hashes and tags cited (d5e7ebc / `prereg-frozen`, 8b7b5a1 / `addendum-frozen`)
- [x] Tag `preexisting-baseline` exists and is pushed (fd8c920, checked 2026-10-26)
- [ ] THIRD_PARTY.md and the report agree on preexisting vs new work (R20)
- [ ] Dual-use review: rates and representative excerpts only, no playbook (R21)
- [ ] No secrets in runs/ or anything linked from the report
- [ ] Wording pass: no "novel", no "significant", no "no effect"; "directional", "to our knowledge"
- [ ] Repo link in the report points to a public remote

## Must be stated in the report (owner answers 2026-10-26, ops/DECISIONS.md D28-D30)
- [ ] Declared deviation (QUESTIONS #26): Llama re-pinned from Novita bf16 to CoreWeave fp16; Novita-era logs archived and re-run.
- [ ] Declared deviation (QUESTIONS #27): Haiku failed the E gate (0.111 < 0.25); the Sonnet fallback could not finish within the credit cap (8 partial games archived, exploratory).
- [ ] Declared deviation (QUESTIONS #24): core on 1 of 2 preregistered families (Llama only) via `--continue-passing-families`, not the plan B stop; 10 Haiku pilot games excluded (run_all_deviations.json).
- [ ] The frozen Deviations sections still say "(none)" unless the owner adds the lines of docs/adam/DEVIATIONS_TO_ADD.md (QUESTIONS #32); the report states the three deviations either way.
- [ ] Invalid replies: the rule "invalid price keeps the previous price" (QUESTIONS #10) never fired: 0 invalid prices and 0 invalid responses in the 44 real logs (tools/insight_checks.py, report/build/factcheck.py).
- [ ] Limitations: raw pricing reasoning traces of the 2 Qwen showcase games exist in git history (commit 8db26d3); they are untracked now and not purged (D30).
- [ ] Not run (credit cap): monitor (H6), ethics (H7), memory arm, gpt-oss THINK arm, O1; results/defenses.md shows NOT RUN / n/a, not zero.
- [ ] Profit at the Nash price: 22.17 is the profit at 1.47; at the exact Nash price 1.4729 it is 22.29 (docs/adam/DRAFT_NUMBERS_CHECK.md).
