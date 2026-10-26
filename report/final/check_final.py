"""Final checks of the report, one command (run from the repo root):

    python3 report/final/check_final.py "Saying Yes Is Not Doing It: A Scripted Price-Fixing Offer to LLM Sellers"

1. compiles REPORT.tex into REPORT.pdf (build_tex.sh) and checks the main body is at most 8 pages;
2. tools.check_submission online on REPORT.tex with the exact title (abstract 150-250 words, appendix title, authors, links);
3. tools.check_numbers on REPORT.md (the readable copy of the same text) against results/, results_exploratory/ and
   report/build/factcheck.txt (allow list of report/SUBMISSION_CHECKLIST.md); facts cited from outside the repo are in CITED.
The fields left empty on purpose for the authors are listed as "A FAIRE PAR LES AUTEURS" and never count as errors.
Exit code 0 when every other check passes, 1 otherwise.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

TITLE = "Saying Yes Is Not Doing It: A Scripted Price-Fixing Offer to LLM Sellers"
TEX = Path("report/final/REPORT.tex")
MD = Path("report/final/REPORT.md")
ALLOW = ["0.10", "10%", "0.25", "0.5", "1.47", "1.473", "1.47293", "0.45205", "1.8798", "1.9702", "1.925", "3.3", "3.8"]
CITED = {"5.04": "OpenRouter usage at the credit cap, from the OpenRouter dashboard (ops/STATE.md, QUESTIONS #27)"}
PLACEHOLDER = re.compile(r"\[(AUTHORS|TEAM):[^\]]*\]")
SECTION = re.compile(r"^(?:## |\\section\*?\{)(.*?)\}?\s*$")

title = sys.argv[1] if len(sys.argv) > 1 else TITLE
py = sys.executable
errors, todo = [], []

for path in (TEX, MD):
    section = "(header)"
    for line in path.read_text(encoding="utf-8").split("\n"):
        s = SECTION.match(line)
        if s:
            section = s.group(1).strip()
        for m in PLACEHOLDER.finditer(line):
            todo.append(f"{path} | section: {section} | search: {m.group(0)}")

bash = shutil.which("bash")
build = subprocess.run([bash, "report/final/build_tex.sh"], capture_output=True, text=True) if bash else None
out = build.stdout.strip() if build else ""
print(out)
m = re.search(r"main body: ([0-9.]+) pages", out)
if build is None:
    errors.append("bash not found, cannot run report/final/build_tex.sh")
elif build.returncode or not m:
    errors.append("LaTeX build failed: " + build.stderr.strip()[-300:])
elif float(m.group(1)) > 8:
    errors.append(f"main body is {m.group(1)} pages, limit 8")

sub = subprocess.run([py, "-m", "tools.check_submission", str(TEX), "--title", title], capture_output=True, text=True)
for line in sub.stdout.strip().split("\n"):
    if line.startswith("authors:") and PLACEHOLDER.search(line):
        print("authors: A FAIRE PAR LES AUTEURS (placeholder line found and detected by check_submission)")
        continue
    print(line)
    if line.rstrip().endswith("FAIL") or " FAIL " in line or "broken:" in line:
        errors.append("check_submission: " + line)

num = subprocess.run([py, "-m", "tools.check_numbers", str(MD), "--sources", "results", "results_exploratory",
                      "report/build/factcheck.txt", "--allow"] + ALLOW, capture_output=True, text=True)
for line in num.stdout.strip().split("\n"):
    tok = re.match(r"line (\d+): (\S+) ", line)
    if tok and tok.group(2) in CITED:
        print(f"{line}  -> cited fact: {CITED[tok.group(2)]}")
    elif tok:
        print(line)
        errors.append("check_numbers: " + line)
    else:
        print(line)

print()
print("A FAIRE PAR LES AUTEURS (dans REPORT.tex, puis la meme chose dans REPORT.md):" if todo else "A FAIRE PAR LES AUTEURS: rien")
for t in todo:
    print("  - " + t)
print("ERREURS:" if errors else "ERREURS: aucune (tout le reste passe)")
for e in errors:
    print("  - " + e)
sys.exit(1 if errors else 0)
