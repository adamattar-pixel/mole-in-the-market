# Fields the authors must fill before submission
Authors already in the report: Adam Kuular, Joshua Tan, Maksim Novikov, Thao Nguyen.
Every field below is in `report/final/REPORT.tex` (the PDF source, highlighted in yellow) and, with the same text, in `report/final/REPORT.md` (the readable copy). Search for the exact text, replace the whole bracket in both files, then recompile with `bash report/final/build_tex.sh`.
In REPORT.tex the bracket sits inside `\todo{...}`: replace `\todo{[...]}` with plain text so the yellow goes away.

| # | Section | Text to search (replace the whole bracket) | What to write |
|---|---|---|---|
| 1 | header (`\author{...}` in REPORT.tex, line starting with "Authors:" in REPORT.md) | `[AUTHORS: name of author 5]` | the fifth author's name (in REPORT.tex keep `\author{...}` on one line, authors separated by `\and`) |
| 2 | header | `[AUTHORS: name of author 6]` | the sixth author's name |
| 3 | header, line starting with "Affiliations:" | `[AUTHORS: affiliation of each of the 6 authors]` | the affiliation of each author |
| 4 | Author Contributions | `[TEAM: write the Author Contributions here, one or two sentences per author, say who did what]` | one or two sentences per author |

Final command (must end with "ERREURS: aucune"):
```
python3 report/final/check_final.py "Saying Yes Is Not Doing It: A Scripted Price-Fixing Offer to LLM Sellers"
```
