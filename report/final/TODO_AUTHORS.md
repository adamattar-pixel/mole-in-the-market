# Fields the authors must fill before submission
All three are in `report/final/REPORT.tex` (the PDF source, highlighted in yellow) and, with the same text, in `report/final/REPORT.md` (the readable copy). Search for the exact text, replace the whole bracket in both files, then recompile with `bash report/final/build_tex.sh`.
In REPORT.tex the bracket sits inside `\todo{...}`: replace `\todo{[...]}` with plain text so the yellow goes away.

| # | Section | Text to search (replace the whole bracket) | What to write |
|---|---|---|---|
| 1 | header (`\author{...}` in REPORT.tex, line starting with "Authors:" in REPORT.md) | `[AUTHORS: write the 6 author names and their affiliations here, one "Name, Affiliation" per author]` | the 6 authors, one "Name, Affiliation" per author (in REPORT.tex keep `\author{...}` on one line, separate authors with `\and`) |
| 2 | Author Contributions | `[TEAM: write the Author Contributions here, one or two sentences per author, say who did what]` | one or two sentences per author |
| 3 | LLM Usage Statement | `[AUTHORS: list the sections you rewrote, or state that the draft was edited only lightly]` | the sections you rewrote, or that the draft was edited only lightly |

Final command (must end with "ERREURS: aucune"):
```
python3 report/final/check_final.py "Saying Yes Is Not Doing It: A Scripted Price-Fixing Offer to LLM Sellers"
```
