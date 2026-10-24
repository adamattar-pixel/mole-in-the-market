"""R15: reproduce outputs are byte-identical on every OS (OPEN_ISSUES #19, follow-up).

Found 2026-10-25: on Windows, Path.write_text() in text mode turns every "\n" into "\r\n", so results/*.json,
*.md, checksums.txt and viz/data/meta.json differ byte for byte from the macOS outputs (same content once the
"\r" are removed, checked on the real runs). Every output of the reproduce chain must be written with LF only.
"""
from pathlib import Path

from helpers import responses_with
from helpers3 import full_log, write_logs
from tools import reproduce as rep

TEXT_SUFFIXES = {".json", ".md", ".csv", ".txt", ".js"}


def logs():
    acc = responses_with(10, {5: ("accept", "decline")})
    flat = lambda post: [(10.0, 10.0) if r < 5 else (post, post) for r in range(1, 11)]
    return [full_log("A", "fx", 1, flat(10.0)), full_log("E", "fx", 1, flat(20.0)),
            full_log("B", "fx", 1, flat(10.0), acc), full_log("D", "fx", 1, flat(10.0), acc)]


def test_R15_I19_reproduce_writes_lf_only(tmp_path):
    write_logs(logs(), tmp_path / "runs")
    rep.reproduce(tmp_path / "runs", tmp_path / "out", viz_dir=tmp_path / "viz", figures_dir=tmp_path / "figs")
    files = [p for d in ("out", "viz") for p in (tmp_path / d).rglob("*") if p.suffix in TEXT_SUFFIXES]
    names = sorted(p.name for p in files)
    for expected in ("summary.json", "tables.md", "checksums.txt", "labels.csv", "detectors.json", "detectors.md",
                     "defenses.json", "defenses.md", "meta.json", "data.js"):
        assert expected in names, expected
    with_cr = sorted(p.name for p in files if b"\r" in p.read_bytes())
    assert with_cr == []
