"""R24: the replay page is static and offline, and loads only its data file.

Usage: python -m tools.check_viz [viz_dir]   (exit 0 when no problem)
viz/index.html must load exactly data/data.js then app.js; viz/demo.html exactly demo/data.js then app.js.
No external URL, no network API (fetch, XMLHttpRequest, WebSocket, EventSource, sendBeacon, dynamic import).
"""
import re
import sys
from pathlib import Path

_SCRIPT_SRC = re.compile(r"<script\b[^>]*\bsrc\s*=\s*[\"']([^\"']+)[\"']", re.I)
_INLINE_SCRIPT = re.compile(r"<script\b(?![^>]*\bsrc\s*=)[^>]*>(.*?)</script>", re.I | re.S)
_EXTERNAL = re.compile(r"(?:https?:)?//[A-Za-z0-9.-]+\.[A-Za-z]{2,}|https?://", re.I)
_NETWORK = [r"\bfetch\s*\(", r"XMLHttpRequest", r"\bWebSocket\b", r"\bEventSource\b", r"sendBeacon",
            r"\bimport\s*\("]


def script_sources(html):
    return _SCRIPT_SRC.findall(html)


def _js_problems(name, js):
    out = [f"{name}: network call matches {p!r}" for p in _NETWORK if re.search(p, js)]
    if _EXTERNAL.search(js):
        out.append(f"{name}: external URL")
    return out


def check_page(html, data_file, js_sources):
    problems = []
    if _EXTERNAL.search(html):
        problems.append("html: external URL")
    srcs = script_sources(html)
    if srcs != [data_file, "app.js"]:
        problems.append(f"html: scripts must be exactly [{data_file!r}, 'app.js'], found {srcs}")
    for i, inline in enumerate(_INLINE_SCRIPT.findall(html)):
        problems += _js_problems(f"inline script {i}", inline)
    for name, js in sorted(js_sources.items()):
        problems += _js_problems(name, js)
    return problems


def check_repo(viz_dir):
    viz = Path(viz_dir)
    read = lambda n: (viz / n).read_text(encoding="utf-8")
    js = {"app.js": read("app.js")}
    problems = [f"index.html: {p}" for p in check_page(read("index.html"), "data/data.js", js)]
    problems += [f"demo.html: {p}" for p in check_page(read("demo.html"), "demo/data.js", js)]
    css = read("style.css")
    if _EXTERNAL.search(css) or re.search(r"@import", css):
        problems.append("style.css: external resource")
    return sorted(set(problems))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    viz = Path(argv[0]) if argv else Path(__file__).resolve().parent.parent / "viz"
    problems = check_repo(viz)
    for p in problems:
        print("PROBLEM", p)
    print("check_viz:", "OK" if not problems else f"{len(problems)} problem(s)")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
