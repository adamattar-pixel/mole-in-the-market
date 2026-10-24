"""Local .env support without a new dependency (D23, RUNBOOK_REAL_RUNS.md step 1).

harness.envfile.load_env reads KEY=VALUE lines from the repo-root .env if it exists. It never overrides a
variable already set in the environment, ignores comments and blank lines, strips optional quotes, and never
prints a value. tools.run and tools.run_all call it at startup.
The repo .env is never read here: every test uses a file in tmp_path or replaces the loader.
"""
from pathlib import Path

import pytest

from harness import envfile

ROOT = Path(__file__).resolve().parent.parent


def write(tmp_path, text):
    p = tmp_path / ".env"
    p.write_text(text, encoding="utf-8")
    return p


def test_default_path_is_repo_root_env():
    # tests/conftest.py points ENV_PATH elsewhere so the suite never loads a real .env; REPO_ENV is the default
    assert Path(envfile.REPO_ENV).resolve() == (ROOT / ".env").resolve()


def test_default_path_is_read_at_call_time(tmp_path, monkeypatch):
    env = {}
    monkeypatch.setattr(envfile, "ENV_PATH", write(tmp_path, "A=1\n"))
    assert envfile.load_env(environ=env) == ["A"] and env == {"A": "1"}


def test_missing_file_is_a_no_op(tmp_path):
    env = {}
    assert envfile.load_env(tmp_path / ".env", env) == []
    assert env == {}


def test_reads_key_value_lines(tmp_path):
    env = {}
    p = write(tmp_path, "A=1\nB=two words\n")
    assert sorted(envfile.load_env(p, env)) == ["A", "B"]
    assert env == {"A": "1", "B": "two words"}


def test_ignores_comments_blank_lines_and_lines_without_equals(tmp_path):
    env = {}
    p = write(tmp_path, "# a comment\n\n   \n  # indented comment\nNOEQUALS\nA=1\n")
    envfile.load_env(p, env)
    assert env == {"A": "1"}


def test_strips_whitespace_and_optional_quotes(tmp_path):
    env = {}
    p = write(tmp_path, " A = 1 \nB=\"x y\"\nC='z'\nD=\"unbalanced\nE=\n")
    envfile.load_env(p, env)
    assert env == {"A": "1", "B": "x y", "C": "z", "D": "\"unbalanced", "E": ""}


def test_value_may_contain_equals(tmp_path):
    env = {}
    envfile.load_env(write(tmp_path, "A=b=c\n"), env)
    assert env == {"A": "b=c"}


def test_never_overrides_the_environment(tmp_path):
    env = {"A": "from-shell", "B": ""}
    p = write(tmp_path, "A=from-file\nB=from-file\nC=new\n")
    assert envfile.load_env(p, env) == ["C"]
    assert env == {"A": "from-shell", "B": "", "C": "new"}


def test_defaults_to_os_environ(tmp_path, monkeypatch):
    monkeypatch.delenv("MOLE_ENVFILE_TEST_VAR", raising=False)
    envfile.load_env(write(tmp_path, "MOLE_ENVFILE_TEST_VAR=ok\n"))
    import os
    assert os.environ["MOLE_ENVFILE_TEST_VAR"] == "ok"
    monkeypatch.delenv("MOLE_ENVFILE_TEST_VAR")


def test_never_prints_values(tmp_path, capsys):
    envfile.load_env(write(tmp_path, "SECRET_ONE=very-secret-value\n"), {})
    out = capsys.readouterr()
    assert "very-secret-value" not in out.out + out.err


@pytest.fixture
def recorder(monkeypatch):
    calls = []

    def fake_load_env(*a, **k):
        calls.append((a, k))
        return []
    return calls, fake_load_env


def test_tools_run_calls_the_loader_at_startup(tmp_path, monkeypatch, recorder):
    from tools import run as run_tool
    calls, fake = recorder
    monkeypatch.setattr(run_tool, "load_env", fake)
    assert run_tool.main([str(ROOT / "configs" / "espion_dry.yaml"), "--out-dir", str(tmp_path / "dry")]) == 0
    assert len(calls) == 1


def test_tools_run_all_calls_the_loader_at_startup(tmp_path, monkeypatch, recorder):
    from tools import run_all
    calls, fake = recorder
    monkeypatch.setattr(run_all, "load_env", fake)
    assert run_all.main(["--dry", "--root", str(tmp_path / "s"), "--n-draws", "20"]) == 0
    assert len(calls) == 1
