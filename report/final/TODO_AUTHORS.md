# Fields the authors must fill before submission
Authors in the report, in this order: Adam Attar, Joshua Tan, Maksim Novikov, Thao Nguyen, Viet Hoang, Artem Kuular.
The field below is in `report/final/REPORT.tex` (the PDF source, highlighted in yellow) and, with the same text, in `report/final/REPORT.md` (the readable copy). Search for the exact text, replace the whole bracket in both files, then recompile with `bash report/final/build_tex.sh`.
In REPORT.tex the bracket sits inside `\todo{...}`: replace `\todo{[...]}` with plain text so the yellow goes away.

| # | Section | Text to search (replace the whole bracket) | What to write |
|---|---|---|---|
| 1 | header, line starting with "Affiliations:" | `[AUTHORS: affiliation of each of the 6 authors]` | the affiliation of each author |

Final command (must end with "ERREURS: aucune"):
```
python3 report/final/check_final.py "Saying Yes Is Not Doing It: A Scripted Price-Fixing Offer to LLM Sellers"
```
