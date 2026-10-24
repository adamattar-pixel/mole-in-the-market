"""Review minors m2 and m4 (docs/team-artem/REVIEW_ARTEM_DIFF.md).

m2: OpenRouter reasoning effort values are max, xhigh, high, medium, low, minimal, none, and a request sets
effort or max_tokens, not both (OpenRouter reasoning tokens docs, checked by the reviewer 2026-10-24).
m4: in real mode run_all's root defaults to the repo root, not the current directory.
"""
import pytest

from harness.runner import validate_config
from helpers3 import cfg


@pytest.mark.parametrize("effort", ["max", "xhigh", "high", "medium", "low", "minimal", "none"])
def test_m2_every_documented_effort_accepted(effort):
    validate_config(cfg(reasoning={"effort": effort}))


def test_m2_effort_and_max_tokens_together_refused():
    with pytest.raises(ValueError, match="not both"):
        validate_config(cfg(reasoning={"effort": "low", "max_tokens": 100}))
    fams = [{"family": "fam", "models": {"0": "fam/m1", "1": "fam/m1"},
             "reasoning": {"effort": "high", "max_tokens": 0}}]
    with pytest.raises(ValueError, match="not both"):
        validate_config(cfg(families=fams))


def test_m4_real_mode_root_defaults_to_repo_root(tmp_path, monkeypatch):
    from tools import run_all
    seen = {}

    def fake(root, **kw):
        seen["root"] = root
        return {"status": "done"}

    monkeypatch.setattr(run_all, "run_pipeline", fake)
    monkeypatch.chdir(tmp_path)
    assert run_all.main([]) == 0
    assert str(seen["root"]) == str(run_all.ROOT)
    assert run_all.main(["--dry"]) == 0
    assert str(seen["root"]) == run_all.DEFAULT_DRY_ROOT
