"""Check the ops/ process docs (see ops/README.md).

Usage: python -m tools.check_ops [--root DIR]   (exit 0 when no problem)
Fails when a path ops/... cited in a doc, code comment or config does not exist, or when a row of the
"Active claims" table in ops/CLAIMS.md is malformed (format: ops/CLAIMS.md "Row format").
tests/, .git/ and run outputs are not scanned.
"""
import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUFFIXES = {".md", ".py", ".yaml", ".yml", ".toml", ".js", ".html", ".txt"}
SKIP_DIRS = {".git", "tests", "runs", "runs_exploratory", "dry_runs", "results", "results_o1", "figures",
             "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules"}
_REF = re.compile(r"(?<![\w./-])ops/[A-Za-z0-9_][A-Za-z0-9_./-]*")

CLAIMS_HEADER = ["Who", "Branch", "Files / areas", "Started", "Expected end"]
_DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})(?: (\d{2}:\d{2}))?(?: (?:UTC|[+-]\d{2}:\d{2}))?$")
_BRANCH = re.compile(r"^[A-Za-z0-9._/-]+$")


def _files(root):
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if p.is_file() and p.suffix in SUFFIXES and not SKIP_DIRS.intersection(rel.parts[:-1]):
            yield p


def ops_refs(root):
    """(file relative to root, line number, ops/ path) for every ops/ path cited under root."""
    root = Path(root)
    out = []
    for p in _files(root):
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for n, line in enumerate(lines, 1):
            for m in _REF.finditer(line):
                out.append((p.relative_to(root).as_posix(), n, m.group(0).rstrip("./-")))
    return out


def _parse_when(cell):
    m = _DATE.match(cell)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1) + " " + (m.group(2) or "00:00"), "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def _cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def claim_errors(text):
    """Problems in the "Active claims" table of a CLAIMS.md text."""
    lines = text.splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == "## Active claims")
    except StopIteration:
        return ["ops/CLAIMS.md: no '## Active claims' section"]
    table = []
    for n, line in enumerate(lines[start + 1:], start + 2):
        if line.startswith("#"):
            break
        if line.strip().startswith("|"):
            table.append((n, line))
    if len(table) < 2 or _cells(table[0][1]) != CLAIMS_HEADER:
        return [f"ops/CLAIMS.md: the Active claims table must start with | {' | '.join(CLAIMS_HEADER)} |"]
    errors = []
    for n, line in table[2:]:
        cells = _cells(line)
        where = f"ops/CLAIMS.md:{n}"
        if len(cells) != len(CLAIMS_HEADER):
            errors.append(f"{where}: {len(cells)} cells, expected {len(CLAIMS_HEADER)}")
            continue
        branch, started, ends = cells[1], cells[3], cells[4]
        if not all(cells):
            errors.append(f"{where}: empty cell")
        elif not _BRANCH.match(branch):
            errors.append(f"{where}: branch {branch!r} is not a branch name")
        elif _parse_when(started) is None or _parse_when(ends) is None:
            errors.append(f"{where}: dates must be YYYY-MM-DD or YYYY-MM-DD HH:MM")
        elif _parse_when(ends) < _parse_when(started):
            errors.append(f"{where}: expected end is before the start")
    return errors


def check(root):
    root = Path(root)
    errors = [f"{f}:{n}: {ref} does not exist" for f, n, ref in ops_refs(root) if not (root / ref).exists()]
    claims = root / "ops" / "CLAIMS.md"
    if not claims.is_file():
        errors.append("ops/CLAIMS.md is missing")
    else:
        errors += claim_errors(claims.read_text(encoding="utf-8"))
    return errors


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check ops/ references and the CLAIMS.md table.")
    ap.add_argument("--root", default=str(ROOT), help="repo root to check (default: this repo)")
    args = ap.parse_args(argv)
    errors = check(args.root)
    for e in errors:
        print(e)
    print("check_ops: OK" if not errors else f"check_ops: {len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
