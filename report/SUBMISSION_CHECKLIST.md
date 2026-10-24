Submission checklist (working list, not the report). Do not run tools/check_submission.py on this file.

Sources: docs/apart/Guidelines.md (copied before the sprint) and the live sprint page as checked 2026-10-24. Where they disagree, the live page wins and is marked LIVE.

## Official pre-submission checklist (docs/apart/Guidelines.md)

- [ ] Report PDF on the official Apart template (link on the Guidelines tab; not the one in any acceptance email)
- [ ] Project title and abstract
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
| Abstract length | 150 to 250 words | tools/check_submission.py MAX_ABSTRACT_WORDS = 150, SPEC R19 "<= 150", locked test a0cd120 | Not changed (locked). check_submission prints FAIL above 150: check 150-250 by hand. Owner decides on a new, separate check |
| Page limit | max 8 pages, excluding references and appendices | check_submission: "page count: MANUAL" | Count on the compiled PDF |
| Appendix title | exactly "Limitations and Dual-Use / Ethical Considerations" | APPENDIX_TITLE matches; a prefix like "Appendix A." is accepted | Keep the exact string |
| Resubmission | same title does NOT replace the PDF (form details only) | Guidelines.md still says files are replaced | New PDF needs a slightly different title, or email sprints@apartresearch.com before the deadline. Get the PDF right the first time |

## Repo checks before submitting

- [ ] `python -m tools.check_submission <final report file> --title "<exact title>"` (online, so links are checked). Expected: abstract FAIL only if 151-250 words (see above); everything else OK
- [ ] Every number traced to a [RESULT: ...] source in report/SKELETON.md (SPEC R18, CLAUDE.md rule 2)
- [ ] `python -m tools.reproduce runs results --viz-dir viz/data --figures-dir figures` rerun at the submission commit; figures in the PDF match
- [ ] Positive control E reported per family (`python -m tools.validate_e runs`)
- [ ] Exploratory items labeled; Deviations sections of PREREGISTRATION.md and PREREGISTRATION_ADDENDUM.md quoted (or "none")
- [ ] Preregistration hashes and tags cited (d5e7ebc / `prereg-frozen`, 8b7b5a1 / `addendum-frozen`)
- [ ] Tag `preexisting-baseline` exists and is pushed (missing as of 2026-10-24; owner action)
- [ ] THIRD_PARTY.md and the report agree on preexisting vs new work (R20)
- [ ] Dual-use review: rates and representative excerpts only, no playbook (R21)
- [ ] No secrets in runs/ or anything linked from the report
- [ ] Wording pass: no "novel", no "significant", no "no effect"; "directional", "to our knowledge"
- [ ] Repo link in the report points to a public remote
