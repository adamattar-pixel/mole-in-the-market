# Submission status (code side) - 2026-10-26
Checked by Adam's Claude session on branch `wip/phase-4-adam-final-demo`. The authors' prose was not edited.
Deadline: Sunday Oct 25, 23:59 AoE = Monday Oct 26, 11:59 UTC = 19:59 HKT.

## What was checked
The authors' sections report/draft/*.md were concatenated in reading order into a scratch file (outside the repo) and checked with
`python -m tools.check_submission <scratch file> --repo-root report/draft` (online, so web links were fetched).

| Check | Result | What a human must do |
|---|---|---|
| Abstract 150 to 250 words | FAIL: no "Abstract" heading in the drafts | Write the abstract (150 to 250 words, live sprint rule) under a heading "Abstract" |
| Appendix "Limitations and Dual-Use / Ethical Considerations" | OK (report/draft/91_appendix_a.md) | keep the exact heading |
| Authors line | FAIL: no "Authors:" line in the drafts | Add the author block of report/AUTHORS.md; affiliations still "to be filled" (OPEN_ISSUES #3) |
| Title identical on every submission | OK: "Saying Yes Is Not Doing It: A Scripted Price-Fixing Offer to LLM Sellers" (report/final/REPORT.tex, REPORT.md, REPORT.pdf, check_final.py) | Choose the title, then run the checker with `--title "<exact title>"` |
| Web links | 16 of 17 OK; papers.ssrn.com/abstract=6832662 answers HTTP 403 to scripts | Open the SSRN link in a browser; keep it if it loads (docs/adam/REFERENCES_CHECK.md) |
| Local links | OK from report/draft (../figures/key_figure.png exists) | If the final file moves, links are resolved from its own folder |
| Page count, main body <= 8 pages | MANUAL. Main-body sections total about 4,480 words (00 134, 01 1,429, 03 869, 04 1,673, 05 378) | Paste into the official template (docs/apart/SUBMISSION_TEMPLATE_URL.txt) and count pages |
| Numbers trace to outputs (R18) | 312 checked, 19 outside reproduce outputs, all recomputed and correct; one sentence to fix (22.17 vs 22.29) | Fix the 22.17 sentence; see docs/adam/DRAFT_NUMBERS_CHECK.md |
| Declared deviations stated | to do in the prose | report/SUBMISSION_CHECKLIST.md, section "Must be stated in the report" |

## Repo state behind the report
- `python -m tools.reproduce runs results --deviations run_all_deviations.json --viz-dir viz/data --figures-dir figures`: two runs give the same results/checksums.txt; results/ match the committed files (only viz meta `generated_at` and the PDF bytes differ by machine).
- Positive control (pilot only): `python -m tools.validate_e runs --config espion_pilot` -> Llama PASS 0.929, Haiku FAIL 0.111.
- results/defenses.md regenerated (QUESTIONS #31): not-run cells read NOT RUN / n/a.

## Final run before submitting
`python3 report/final/check_final.py "Saying Yes Is Not Doing It: A Scripted Price-Fixing Offer to LLM Sellers"` (online) must end with "ERREURS: aucune"; it lists the 3 fields left for the authors (report/final/TODO_AUTHORS.md).

## Tag gate-4 (owner action after the PR is merged, D35)
Claude never creates or moves tags. After the PR `wip/phase-4-adam-final-demo` -> `wip/phase-4` (and `wip/phase-4` -> `main`)
is merged and CI is green, the owner runs:
```
git fetch origin
git switch main && git pull --ff-only origin main
python3 -m pytest -q && python3 -m tools.check_ops          # green before tagging
git tag -a gate-4 -m "gate-4: Phase 4 closed with declared deviations (Llama-only core, QUESTIONS #24 #26 #27, D29)"
git push origin gate-4
```

## Final report (2026-10-26, D37, D38)
report/final/REPORT.md, REPORT.docx, REPORT.pdf, title "Saying Yes Is Not Doing It: A Scripted Price-Fixing Offer to LLM Sellers". Main body 6.09 pages (6.24 with the author fields filled in a test copy). Only the 3 fields of report/final/TODO_AUTHORS.md are left, then submission before 11:59 UTC.

## LaTeX version (2026-10-26, D39)
report/final/REPORT.pdf is now compiled from report/final/REPORT.tex (`bash report/final/build_tex.sh`), main body 5.67 pages. The text was rewritten at the owner's request without changing any fact; REPORT.md holds the same text. The Word copy (REPORT.docx, REPORT_docx.pdf) is optional.
