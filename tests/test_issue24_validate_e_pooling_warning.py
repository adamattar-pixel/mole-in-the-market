"""OPEN_ISSUES #24: `tools.validate_e runs` without --config pools the A and E games of every config.

Found 2026-10-26 on the real runs: the pilot alone gives anthropic FAIL (effect 0.111), but pooled with the
smoke games (seed 1 again) it prints anthropic PASS (0.277). The default stays the locked R13 behaviour; the
script must now print a WARNING naming the pooled configs and the pilot-only command. Hand-built logs:
two configs, "espion_smoke" and "espion_pilot", each with one A and one E game.
"""
from helpers3 import full_log, write_logs
from tools import validate_e


def flat(pre, post, n=10, spy=5):
    return [(pre, pre) if r < spy else (post, post) for r in range(1, n + 1)]


def logs_two_configs():
    out = []
    for cfg in ("espion_smoke", "espion_pilot"):
        for cond, post in (("A", 12.0), ("E", 15.0)):
            g = full_log(cond, "fx", 1, flat(10.0, post))
            g["game_id"] = f"{cfg}__fx__{cond}__s1"
            out.append(g)
    return out


def test_issue24_warns_when_several_configs_are_pooled(tmp_path, capsys):
    write_logs(logs_two_configs(), tmp_path / "runs")
    validate_e.main([str(tmp_path / "runs")])
    out = capsys.readouterr().out
    assert "WARNING" in out and "espion_pilot" in out and "espion_smoke" in out
    assert "--config espion_pilot" in out


def test_issue24_no_warning_with_one_config_or_with_config_filter(tmp_path, capsys):
    logs = logs_two_configs()
    write_logs([g for g in logs if g["game_id"].startswith("espion_pilot")], tmp_path / "one")
    validate_e.main([str(tmp_path / "one")])
    assert "WARNING" not in capsys.readouterr().out
    write_logs(logs, tmp_path / "two")
    validate_e.main([str(tmp_path / "two"), "--config", "espion_pilot"])
    assert "WARNING" not in capsys.readouterr().out
