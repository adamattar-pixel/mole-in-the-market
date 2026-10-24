# docs/adam - Adam's Claude session, branch `wip/phase-4-adam-numbers` (2026-10-25 night)
Branched from `origin/wip/phase-4` at 764b623 (Artem's last commit). No API call, no spend, no frozen file touched.
`gh` is not installed on this machine, so no PR was opened: the branch is pushed and ready for a PR into `wip/phase-4`.

## What is on the branch (tests first, each rule mutation-checked)
1. **R18 `tools/check_numbers.py`**: every result number of a document (decimals, percentages, k/n counts) must be
   found in the reproduce outputs. Locked tests de935f8, gap tests tests/test_R18_gaps.py (arXiv ids, DOIs,
   section numbers, counts from two integers of one JSON object, k <= n).
   Usage: `python -m tools.check_numbers report/<draft>.md --sources results results_exploratory --allow <design constants>`.
2. **NUMBERS_AUDIT.md**: the tool run on RESULTS_SUMMARY.md, KEY_FIGURE.md, PAGE1_EXCERPT.md, report/SKELETON.md.
   No invented number. 12 numbers are outside the reproduce outputs: 4 hand computations (checked, correct),
   5 values read from logs or traces (cite them), 2 non-results, 1 archived pilot value.
3. **OPEN_ISSUES #19, REPRO_CHECK.md**: `reproduce` on the committed logs now gives byte-identical results and
   checksums on Windows (`.gitattributes` eol=lf, LF writes in the reproduce chain, viz/demo regenerated).

4. **REFERENCES_CHECK.md**: the 12 citations of report/SKELETON.md fetched: 11 match (title, authors, year), the SSRN
   paper (Giebel et al.) blocks automated access (open it in a browser). Difference notes checked against the
   papers: Fish et al. and Colosseum notes confirmed; do NOT claim "first sting" (GroupGuard uses honeypots as a
   defense); Agrawal et al.: oversight reduces and CEO urgency increases collusion, a different manipulation from B_T.

## Merge notes
- Into `wip/phase-4`: no conflict (`git merge-tree` at bffa6f1+).
- With `wip/phase-4-hoang`: `.gitattributes` is now the same file on both branches (no conflict). Two conflicts left,
  both in shared tracking docs:
  - ops/CLAIMS.md: both branches add a row at the end. Keep both rows (or drop the row of a merged branch).
  - ops/OPEN_ISSUES.md row 19: Hoang marked it "open, .gitattributes added, demo not regenerated"; this branch
    marks it "done" (demo regenerated after the working copy was re-checked out as LF). Keep "done" and credit both.
- Code files edited on both branches (tools/reproduce.py, tools/score_detectors.py, tools/score_defenses.py) merge
  automatically: Hoang adds lines at the top (repo root on sys.path), this branch changes the write_text lines.
