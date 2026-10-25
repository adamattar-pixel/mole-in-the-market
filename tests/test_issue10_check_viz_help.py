"""OPEN_ISSUES #10/#11 follow-up: tools/check_viz.py took "--help" as a folder name and crashed
(FileNotFoundError '--help/app.js'). It must print its usage and exit 0, and still check viz/ by default."""
import subprocess
import sys
from pathlib import Path

import pytest

from tools import check_viz

ROOT = Path(__file__).resolve().parent.parent


def test_issue10_check_viz_help_exits_zero(capsys):
    with pytest.raises(SystemExit) as e:
        check_viz.main(["--help"])
    assert e.value.code == 0
    assert "usage" in capsys.readouterr().out.lower()


def test_issue10_check_viz_script_entry_point():
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "check_viz.py"), "--help"], capture_output=True, text=True)
    assert r.returncode == 0 and "usage" in r.stdout.lower()


def test_issue10_check_viz_default_still_checks_viz():
    assert check_viz.main([]) == 0
