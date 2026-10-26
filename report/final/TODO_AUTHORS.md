# Fields the authors must fill before submission

Authors, affiliations and team name are filled (Maksim Novikov, Joshua Tan, Adam Attar, Thao Nguyen, Artem Kuular; all HKUST, Hong Kong; team TTT).

Left to confirm: the Author Contributions paragraph in `report/final/REPORT.tex` and `report/final/REPORT.md` is a draft based on git history. Search for "AUTHOR CONTRIBUTIONS DRAFT", edit it in both files if needed, then recompile with `bash report/final/build_tex.sh`.

Final command (must end with "ERREURS: aucune"):
```
python3 report/final/check_final.py "Saying Yes Is Not Doing It: A Scripted Price-Fixing Offer to LLM Sellers"
```
