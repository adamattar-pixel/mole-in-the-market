# Numbers check of the authors' report drafts (2026-10-26, read only)
Files: report/draft/*.md (the authors' sections). Nothing in them was changed.
Command: `python -m tools.check_numbers <file> --sources results results_exploratory --allow 0.10 10% 0.25 0.5 1.473 1.47293 0.45205 1.8798 1.9702 1.925 3.3 3.8 4.5`

312 result numbers checked in 7 files; 19 are not written in a reproduce output. None is invented. Every one was recomputed here:

| Number (file:line) | What it is | Recomputed | Verdict |
|---|---|---|---|
| 1.47 (00_box1:7, 01_intro:9, 04_results:17 and :50) | Nash price, rounded | Nash 1.4729 (harness/economics.py) | design constant: add `1.47` to --allow |
| 15.98 (01_intro:11, 04_results:17 and :66, 05_discussion:5) | profit per firm at 2.50 | 15.9760 | correct (hand computation) |
| 22.17 (04_results:17, 05_discussion:5) | profit per firm "at the Nash price (1.47)" | 22.1695 at 1.47; 22.2927 at the exact Nash 1.4729 | correct at the rounded price; at the exact Nash price it is 22.29. Say "at 1.47" or use 22.29 |
| 36.68 (90_appendix_bc:44) | quantity at 1.92 in a prompt history line | 36.6818 | correct (quoted from a log) |
| 0.97 (04_results:40) | Wilson lower bound of 130/130 | 0.9713 | correct |
| 0.66 x2 (04_results:80) | Wilson upper bound of 0/2 | 0.6576 | correct |
| 0.87, 0.71 (04_results:80) | Wilson lower bounds of 39/40 and 34/40 traces | 0.8712, 0.7093 | correct |
| 0.024 (03_methods:24, 90_appendix_bc:115) | mean cost per game, Haiku | 0.0239 over the 10 Haiku pilot logs (Llama: 0.0121 over 30) | correct (from runs/, not a reproduce output) |
| 5.04 (90_appendix_bc:134) | OpenRouter usage at the cap | external (OpenRouter dashboard, ops/STATE.md) | cannot be recomputed from the repo; cite the dashboard |

## Also checked
- `python -m tools.check_submission report/ai_draft/REPORT_AI_DRAFT.md --offline` runs (the tool works). That moved-aside draft has
  an abstract of 374 words (rule: 150 to 250), no authors line, and its two figure links break from report/ai_draft/. Run the
  checker on the final assembled report, placed in report/, with `--title "<exact title>"` and without --offline.
- Since OPEN_ISSUES #27, relative links are resolved from the report's own folder (Markdown rule).
