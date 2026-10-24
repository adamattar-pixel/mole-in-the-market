"""R19: submission checks on the report source (Markdown or LaTeX). Page count is MANUAL.

Usage: python -m tools.check_submission report/report.md --title "Exact title" [--offline]
Checks: abstract 150 to 250 words (live sprint page, 2026-10-24), appendix titled exactly "Limitations and Dual-Use / Ethical Considerations",
authors listed, title equal to the expected one, web links resolve, relative repo links exist.
A check that was not run (for example links with --offline) is never reported as a pass.
"""
import argparse
import re
import urllib.request
from pathlib import Path

APPENDIX_TITLE = "Limitations and Dual-Use / Ethical Considerations"
MIN_ABSTRACT_WORDS = 150
MAX_ABSTRACT_WORDS = 250

_WORD = re.compile(r"[A-Za-z0-9]+(?:[-'.\u2019][A-Za-z0-9]+)*")
_URL = re.compile(r"https?://[^\s<>()\[\]\"']+")
_MD_HEADING = re.compile(r"^(#+)\s*(.*?)\s*#*\s*$")
_TEX_HEADING = re.compile(r"\\(?:sub)*section\*?\{(.*?)\}")


def count_words(text):
    return len(_WORD.findall(text or ""))


def _headings(text):
    out = []
    for line in text.splitlines():
        m = _MD_HEADING.match(line)
        if m:
            out.append(m.group(2))
    out += _TEX_HEADING.findall(text)
    return out


def _abstract(text):
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", text, flags=re.S)
    if m:
        return m.group(1)
    lines = text.splitlines()
    for i, line in enumerate(lines):
        h = _MD_HEADING.match(line)
        if h and h.group(2).strip().lower() == "abstract":
            body = []
            for nxt in lines[i + 1:]:
                if _MD_HEADING.match(nxt):
                    break
                body.append(nxt)
            return "\n".join(body)
    return None


def _authors(text):
    m = re.search(r"\\author\{(.*?)\}\s*$", text, flags=re.M)
    if m:
        raw = re.sub(r"\\thanks\{.*?\}", "", m.group(1))
        return [a.strip() for a in raw.split("\\and") if a.strip()]
    m = re.search(r"^\s*Authors?:\s*(.*)$", text, flags=re.M | re.I)
    if m:
        return [a.strip() for a in re.split(r",|;|\band\b", m.group(1)) if a.strip()]
    return []


def _title(text):
    m = re.search(r"\\title\{(.*?)\}", text, flags=re.S)
    if m:
        return m.group(1).strip()
    for line in text.splitlines():
        h = _MD_HEADING.match(line)
        if h and len(h.group(1)) == 1:
            return h.group(2).strip()
    return None


def extract_urls(text):
    seen = []
    for u in _URL.findall(text):
        u = u.rstrip(".,;:!?")
        if u not in seen:
            seen.append(u)
    return seen


def _local_links(text):
    out = []
    for target in re.findall(r"\]\(([^)\s]+)\)", text):
        if re.match(r"^(https?:|mailto:|#)", target):
            continue
        if target not in out:
            out.append(target)
    return out


def _http_status(url, timeout=15):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "check_submission"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status


def check_text(text, expected_title=None, fetch=None, repo_root=None):
    abstract = _abstract(text)
    n_words = None if abstract is None else count_words(abstract)
    authors = _authors(text)
    title = _title(text)
    r = {
        "abstract_words": n_words,
        "abstract_ok": n_words is not None and MIN_ABSTRACT_WORDS <= n_words <= MAX_ABSTRACT_WORDS,
        "appendix_ok": any(h.strip().endswith(APPENDIX_TITLE) for h in _headings(text)),
        "authors": authors,
        "authors_ok": bool(authors),
        "title": title,
        "title_ok": None if expected_title is None else (title == expected_title),
    }
    urls = extract_urls(text)
    if fetch is None:
        r["links"], r["links_ok"] = {u: None for u in urls}, None
    else:
        links = {}
        for u in urls:
            try:
                code = fetch(u)
                links[u] = 200 <= int(code) < 400
            except Exception:  # any network or HTTP error = broken link
                links[u] = False
        r["links"], r["links_ok"] = links, all(links.values())
    local = _local_links(text)
    if not local:
        r["local_links"], r["local_links_ok"] = {}, True
    elif repo_root is None:
        r["local_links"], r["local_links_ok"] = {t: None for t in local}, None
    else:
        r["local_links"] = {t: (Path(repo_root) / t).exists() for t in local}
        r["local_links_ok"] = all(r["local_links"].values())
    return r


def overall(result):
    """True only if every check ran and passed."""
    keys = ("abstract_ok", "appendix_ok", "authors_ok", "title_ok", "links_ok", "local_links_ok")
    return all(result[k] is True for k in keys)


def _mark(ok):
    return "NOT RUN" if ok is None else ("OK" if ok else "FAIL")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report")
    ap.add_argument("--title", default=None, help="exact title used on every submission")
    ap.add_argument("--offline", action="store_true", help="do not check web links (reported NOT RUN)")
    ap.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent))
    a = ap.parse_args(argv)
    text = Path(a.report).read_text(encoding="utf-8")
    r = check_text(text, expected_title=a.title, fetch=None if a.offline else _http_status, repo_root=a.repo_root)
    words = "missing" if r["abstract_words"] is None else f"{r['abstract_words']} words"
    print(f"abstract: {words} ({MIN_ABSTRACT_WORDS} to {MAX_ABSTRACT_WORDS}) {_mark(r['abstract_ok'])}")
    print(f"appendix '{APPENDIX_TITLE}': {_mark(r['appendix_ok'])}")
    print(f"authors: {', '.join(r['authors']) or 'none'} {_mark(r['authors_ok'])}")
    print(f"title: {r['title']!r} {_mark(r['title_ok'])}")
    if r["links_ok"] is None:
        print(f"links: NOT RUN ({len(r['links'])} found)")
    else:
        bad = [u for u, ok in r["links"].items() if not ok]
        print(f"links: {len(r['links']) - len(bad)}/{len(r['links'])} OK" + (f", broken: {bad}" if bad else ""))
    print(f"local links: {_mark(r['local_links_ok'])} {r['local_links'] or ''}".rstrip())
    print("page count: MANUAL (main body <= 8 pages on the official Apart template)")
    return 0 if overall(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
