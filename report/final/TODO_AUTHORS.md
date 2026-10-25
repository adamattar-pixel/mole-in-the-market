# Fields the authors must fill before submission
All three are in `report/final/REPORT.md`, highlighted in yellow in the docx and pdf. Search for the exact text, replace it, then rebuild.

| # | File | Section | Text to search (replace the whole bracket) | What to write |
|---|---|---|---|---|
| 1 | report/final/REPORT.md | header, line starting with "Authors:" | `[AUTHORS: write the 6 author names and their affiliations here, one "Name, Affiliation" per author]` | the 6 authors, one "Name, Affiliation" per author; keep the word "Authors:" at the start of the line |
| 2 | report/final/REPORT.md | Author Contributions | `[TEAM: write the Author Contributions here, one or two sentences per author, say who did what]` | one or two sentences per author |
| 3 | report/final/REPORT.md | LLM Usage Statement | `[AUTHORS: say which parts you rewrote or checked yourselves]` | which parts you rewrote or checked yourselves |

Also remove the first line ("AI-DRAFTED, authors must review and rewrite before submission (D37)...") once you have reviewed and rewritten the draft.

Final command (must end with "ERREURS: aucune"):
```
python3 report/final/check_final.py "Saying Yes Is Not Doing It: A Scripted Price-Fixing Offer to LLM Sellers"
```
