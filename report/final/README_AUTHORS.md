1. `report/final/REPORT.tex` is the source of `REPORT.pdf`; `REPORT.md` is a readable copy of the same text (keep both identical).
2. Fill the 3 yellow fields listed in `TODO_AUTHORS.md`, in REPORT.tex and the same in REPORT.md.
3. Recompile: `bash report/final/build_tex.sh` (no API key; needs Tectonic or latexmk with XeLaTeX); it prints the body length (limit 8 pages, now 5.67).
4. Check everything (online): `python3 report/final/check_final.py "Saying Yes Is Not Doing It: A Scripted Price-Fixing Offer to LLM Sellers"`; it must end with "ERREURS: aucune".
5. Submit `report/final/REPORT.pdf` on the Apart form before Monday Oct 26, 11:59 UTC, with this exact title.
