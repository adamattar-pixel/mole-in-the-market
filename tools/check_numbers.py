"""R18: every result number in a document must come from the reproduce outputs.

Usage: python -m tools.check_numbers report/draft.md [--sources results] [--allow 0.10 0.25] [--include-code]
Exit 0 when every result-like number of the document is found in the sources, 1 otherwise.

Checked: decimals (0.67), percentages (67%, 66.7%), counts (2/3). Not checked: plain integers, dates, ids such
as R28 or H4, hashes, versions followed by letters (3.8B), and numbers inside ``` code blocks (unless
--include-code). A decimal with p digits matches a source number v when round(v, p) equals it; a percentage
when round(100 * v, p) equals it; a count k/n when a JSON object has "k": k and "n": n, or "k/n" is written in a
source. Design constants that are not results (frozen thresholds) are passed with --allow.
This is a guard for the rule "every number in the report comes from reproduce"; a match does not prove the
number is used with the right meaning, so a human still reads the report.
"""
import argparse
import json
import re
from pathlib import Path

_TOKEN = re.compile(
    r"(?P<count>(?<![\w./-])\d+/\d+(?![\w/-]|\.\d))"
    r"|(?P<percent>(?<![\w.])\d+(?:\.\d+)?%)"
    r"|(?P<decimal>(?<![\w.])\d+\.\d+(?![\w]|\.\d))")
_SOURCE_SUFFIXES = (".json", ".md", ".csv", ".txt")


def extract_numbers(text, include_code=False):
    out, in_code = [], False
    for i, line in enumerate(text.splitlines(), start=1):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code and not include_code:
            continue
        for m in _TOKEN.finditer(line):
            kind = m.lastgroup
            out.append({"line": i, "token": m.group(kind), "kind": kind})
    return out


def collect_sources(paths):
    files = []
    for p in map(Path, paths):
        if not p.exists():
            raise FileNotFoundError(p)
        if p.is_dir():
            files += sorted(f for f in p.rglob("*") if f.is_file() and f.suffix in _SOURCE_SUFFIXES)
        else:
            files.append(p)
    return files


class _Pool:
    """Numbers, counts and literal tokens found in the source files."""

    def __init__(self, sources):
        self.values, self.counts, self.literals = [], set(), set()
        self._rounded = {}
        for f in sources:
            text = Path(f).read_text(encoding="utf-8")
            if Path(f).suffix == ".json":
                self._walk(json.loads(text))
            for t in extract_numbers(text, include_code=True):
                self.literals.add(t["token"])
                if t["kind"] == "decimal":
                    self.values.append(float(t["token"]))

    def _walk(self, x):
        if isinstance(x, dict):
            k, n = x.get("k"), x.get("n")
            if isinstance(k, int) and isinstance(n, int) and not isinstance(k, bool):
                self.counts.add((k, n))
            for v in x.values():
                self._walk(v)
        elif isinstance(x, list):
            for v in x:
                self._walk(v)
        elif isinstance(x, (int, float)) and not isinstance(x, bool):
            self.values.append(float(x))

    def rounded(self, digits, scale):
        key = (digits, scale)
        if key not in self._rounded:
            self._rounded[key] = {round(round(v * scale, digits), digits) for v in self.values}
        return self._rounded[key]

    def has(self, token, kind):
        if token in self.literals:
            return True
        if kind == "count":
            k, n = (int(x) for x in token.split("/"))
            return (k, n) in self.counts
        num = token.rstrip("%")
        digits = len(num.split(".")[1]) if "." in num else 0
        scale = 100.0 if kind == "percent" else 1.0
        return round(float(num), digits) in self.rounded(digits, scale)


def check_text(text, sources, allow=None, include_code=False):
    """List of {line, token, kind} for result numbers not found in the sources (empty list = all found)."""
    pool = _Pool(sources)
    allowed = set(allow or [])
    out = []
    for t in extract_numbers(text, include_code=include_code):
        if t["token"] in allowed or pool.has(t["token"], t["kind"]):
            continue
        out.append(t)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("document")
    ap.add_argument("--sources", nargs="+", default=["results"], help="files or folders (default: results)")
    ap.add_argument("--allow", nargs="*", default=[], help="design constants that are not results")
    ap.add_argument("--include-code", action="store_true")
    a = ap.parse_args(argv)
    text = Path(a.document).read_text(encoding="utf-8")
    sources = collect_sources(a.sources)
    missing = check_text(text, sources, allow=a.allow, include_code=a.include_code)
    checked = len(extract_numbers(text, include_code=a.include_code))
    for m in missing:
        print(f"line {m['line']}: {m['token']} ({m['kind']}) not found in the sources")
    print(f"check_numbers: {checked} result numbers checked in {a.document}, {len(missing)} not found "
          f"(sources: {len(sources)} files)")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
