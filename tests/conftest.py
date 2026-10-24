import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT, ROOT / "tests"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import pytest


@pytest.fixture(autouse=True)
def _no_repo_env_file(monkeypatch, tmp_path_factory):
    """The suite never loads the repo .env (secrets): tools.run and tools.run_all read it at startup."""
    from harness import envfile
    monkeypatch.setattr(envfile, "ENV_PATH", tmp_path_factory.mktemp("noenv") / ".env")
