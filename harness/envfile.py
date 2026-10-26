"""Tiny .env loader, no dependency (D23, docs/RUNBOOK_REAL_RUNS.md step 1).

Reads KEY=VALUE lines from the repo-root .env if it exists. A variable already set in the environment is never
overridden. Comments (#) and blank lines are ignored, one pair of matching quotes around a value is stripped.
Values are never printed or logged; only the names of the variables set are returned.
"""
import os
from pathlib import Path

REPO_ENV = Path(__file__).resolve().parent.parent / ".env"
ENV_PATH = REPO_ENV


def load_env(path=None, environ=None):
    path = Path(ENV_PATH if path is None else path)
    environ = os.environ if environ is None else environ
    if not path.is_file():
        return []
    loaded = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = (s.strip() for s in line.split("=", 1))
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key and key not in environ:
            environ[key] = value
            loaded.append(key)
    return loaded
