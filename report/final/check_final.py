"""One command for the final checks of the report (run from the repo root):

    python3 report/final/check_final.py "<exact title>" [path/to/final_report.md]

1. rebuilds REPORT.docx and REPORT.pdf and prints the main-body page count (limit: 8 pages);
2. tools.check_submission online with the exact title (abstract 150-250 words, appendix title, authors, links);
3. tools.check_numbers against results/, results_exploratory/ and report/build/factcheck.txt with the allow list of
   report/SUBMISSION_CHECKLIST.md (each remaining line must be a cited fact).
"""
import subprocess
import sys

title = sys.argv[1] if len(sys.argv) > 1 else None
report = sys.argv[2] if len(sys.argv) > 2 else "report/final/REPORT.md"
ALLOW = ["0.10", "10%", "0.25", "0.5", "1.47", "1.473", "1.47293", "0.45205", "1.8798", "1.9702", "1.925", "3.3", "3.8"]
py = sys.executable
codes = []
codes.append(subprocess.run([py, "report/final/build_report.py"]).returncode)
cmd = [py, "-m", "tools.check_submission", report] + (["--title", title] if title else [])
codes.append(subprocess.run(cmd).returncode)
codes.append(subprocess.run([py, "-m", "tools.check_numbers", report, "--sources", "results", "results_exploratory",
                             "report/build/factcheck.txt", "--allow"] + ALLOW).returncode)
print("exit codes (build, check_submission, check_numbers):", codes)
