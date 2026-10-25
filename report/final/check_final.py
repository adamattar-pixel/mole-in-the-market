"""Final checks of the report, one command (run from the repo root):

    python3 report/final/check_final.py "Saying Yes Is Not Doing It: A Scripted Price-Fixing Offer to LLM Sellers"

1. rebuilds REPORT.docx and REPORT.pdf from REPORT.md and checks the main body is at most 8 pages;
2. tools.check_submission online with the exact title (abstract 150-250 words, appendix title, authors, links);
3. tools.check_numbers against results/, results_exploratory/ and report/build/factcheck.txt (allow list of
   report/SUBMISSION_CHECKLIST.md); facts cited from outside the repo are listed in CITED below.
The fields left empty on purpose for the authors are listed as "A FAIRE PAR LES AUTEURS" and never count as errors.
Exit code 0 when every other check passes, 1 otherwise.
"""
import re
import subprocess
import sys
from pathlib import Path

TITLE = "Saying Yes Is Not Doing It: A Scripted Price-Fixing Offer to LLM Sellers"
REPORT = Path("report/final/REPORT.md")
ALLOW = ["0.10", "10%", "0.25", "0.5", "1.47", "1.473", "1.47293", "0.45205", "1.8798", "1.9702", "1.925", "3.3", "3.8"]
CITED = {"5.04": "OpenRouter usage at the credit cap, from the OpenRouter dashboard (ops/STATE.md, QUESTIONS #27)"}
PLACEHOLDER = re.compile(r"\[(AUTHORS|TEAM):[^\]]*\]")

title = sys.argv[1] if len(sys.argv) > 1 else TITLE
py = sys.executable
errors, todo = [], []

text = REPORT.read_text(encoding="utf-8")
section = "(header)"
for line in text.split("\n"):
    if line.startswith("## "):
        section = line[3:].strip()
    for m in PLACEHOLDER.finditer(line):
        todo.append(f"{REPORT} | section: {section} | search: {m.group(0)}")

build = subprocess.run([py, "report/final/build_report.py"], capture_output=True, text=True)
print(build.stdout.strip())
m = re.search(r"main body: ([0-9.]+) pages", build.stdout)
if build.returncode or not m:
    errors.append("build failed: " + build.stderr.strip()[-300:])
elif float(m.group(1)) > 8:
    errors.append(f"main body is {m.group(1)} pages, limit 8")

cmd = [py, "-m", "tools.check_submission", str(REPORT), "--title", title]
sub = subprocess.run(cmd, capture_output=True, text=True)
for line in sub.stdout.strip().split("\n"):
    if line.startswith("authors:") and PLACEHOLDER.search(line):
        print("authors: A FAIRE PAR LES AUTEURS (placeholder line found and detected by check_submission)")
        continue
    print(line)
    if line.rstrip().endswith("FAIL") or " FAIL " in line or "broken:" in line:
        errors.append("check_submission: " + line)

num = subprocess.run([py, "-m", "tools.check_numbers", str(REPORT), "--sources", "results", "results_exploratory",
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
print("A FAIRE PAR LES AUTEURS:" if todo else "A FAIRE PAR LES AUTEURS: rien")
for t in todo:
    print("  - " + t)
print("ERREURS:" if errors else "ERREURS: aucune (tout le reste passe)")
for e in errors:
    print("  - " + e)
sys.exit(1 if errors else 0)
