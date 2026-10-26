#!/usr/bin/env bash
# One command: compile report/final/REPORT.tex to report/final/REPORT.pdf and print the main-body page count.
# Usage: bash report/final/build_tex.sh   (no API key; needs Tectonic, or latexmk with XeLaTeX)
set -euo pipefail
cd "$(dirname "$0")"
TECTONIC="$(command -v tectonic || true)"
if [ -z "$TECTONIC" ] && [ -n "${LOCALAPPDATA:-}" ] && [ -x "$LOCALAPPDATA/tectonic/tectonic.exe" ]; then
  TECTONIC="$LOCALAPPDATA/tectonic/tectonic.exe"
fi
if [ -n "$TECTONIC" ]; then
  "$TECTONIC" -X compile REPORT.tex > build_tex.log 2>&1 || { tail -30 build_tex.log >&2; exit 1; }
elif command -v latexmk >/dev/null; then
  latexmk -xelatex -interaction=nonstopmode -quiet REPORT.tex >/dev/null
else
  echo "no LaTeX engine found: install Tectonic (https://tectonic-typesetting.github.io) or latexmk with XeLaTeX" >&2
  exit 2
fi
PY=""
for p in python3 python py; do  # skip the Windows Store stub, which cannot import anything
  if command -v "$p" >/dev/null && "$p" -c "import pymupdf" >/dev/null 2>&1; then PY="$p"; break; fi
done
[ -n "$PY" ] || { echo "no Python with pymupdf found (pip install pymupdf)" >&2; exit 2; }
"$PY" - <<'EOF'
import sys
sys.path.insert(0, ".")
from build_report import body_pages
body_pages("REPORT.pdf")
EOF
