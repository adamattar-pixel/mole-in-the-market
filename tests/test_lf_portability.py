"""R15 checksums must not depend on the operating system (OPEN_ISSUES #19).

Found 2026-10-25: on a Windows clone (core.autocrlf), git writes the logs in runs/ with CRLF line ends, so the
sha256 of every log differs from the committed results/checksums.txt (made on macOS, LF), although the tables
are identical. The repository stores every text file with LF (`git ls-files --eol`: i/lf), so a
`.gitattributes` with `* text=auto eol=lf` makes every working copy byte-identical to the repository.
"""
import hashlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def test_R15_I19_gitattributes_forces_lf():
    text = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert re.search(r"^\*\s+text=auto\s+eol=lf\s*$", text, flags=re.M)


@pytest.mark.parametrize("name", ["PREREGISTRATION.md", "PREREGISTRATION_ADDENDUM.md", "results/checksums.txt"])
def test_R15_I19_key_files_have_lf_line_ends(name):
    assert b"\r\n" not in (ROOT / name).read_bytes()


def test_R15_I19_committed_input_checksums_match_this_working_copy():
    # every "sha256  runs/<file>" line of results/checksums.txt must match the log as checked out here
    lines = (ROOT / "results" / "checksums.txt").read_text(encoding="utf-8").splitlines()
    pairs = [l.split("  ", 1) for l in lines if "  runs/" in l]
    assert pairs
    bad = [rel for sha, rel in pairs
           if (ROOT / rel).exists() and hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != sha]
    assert bad == []
