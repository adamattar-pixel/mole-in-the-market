"""QUESTIONS.md #23: tools.validate_e --config keeps only the logs of the named config(s).

Default (no --config) is the locked R13 behaviour: every A and E log in the folder is pooled.
Synthetic logs, hand-computed answers: Nash 10, monopoly 20 (gap 10), spy_start 5, 10 rounds.
  pilot: A seeds 1, 2 at 12 and E seeds 1, 2 at 15 after spy_start -> (15 - 12) / 10 = 0.300 PASS
  smoke: A seed 1 at 12 and E seed 1 at 10 -> (10 - 12) / 10 = -0.200 FAIL
  pooled: A mean 12, E mean (15 + 15 + 10) / 3 = 13.333 -> 0.133 FAIL (threshold 0.25)
"""
from helpers3 import full_log, write_logs
from tools import validate_e


def flat(pre, post, n=10, spy=5):
    return [(pre, pre) if r < spy else (post, post) for r in range(1, n + 1)]


def log(config, condition, seed, post):
    g = full_log(condition, "fx", seed, flat(10.0, post))
    g["game_id"] = f"{config}__fx__{condition}__s{seed}"
    return g


def write(tmp_path):
    logs = [log("espion_pilot", "A", s, 12.0) for s in (1, 2)] + \
           [log("espion_pilot", "E", s, 15.0) for s in (1, 2)] + \
           [log("espion_smoke", "A", 1, 12.0), log("espion_smoke", "E", 1, 10.0)]
    write_logs(logs, tmp_path / "runs")
    return str(tmp_path / "runs")


def test_validate_e_default_still_pools_every_config(tmp_path, capsys):
    code = validate_e.main([write(tmp_path)])
    out = capsys.readouterr().out
    assert "fx: FAIL (effect 0.133 of the gap" in out and "A games 3, E games 3" in out
    assert "configs:" not in out
    assert code == 1


def test_validate_e_config_filter_keeps_only_that_config(tmp_path, capsys):
    code = validate_e.main([write(tmp_path), "--config", "espion_pilot"])
    out = capsys.readouterr().out
    assert "configs: espion_pilot" in out
    assert "fx: PASS (effect 0.300 of the gap" in out and "A games 2, E games 2" in out
    assert code == 0


def test_validate_e_config_filter_other_config(tmp_path, capsys):
    code = validate_e.main([write(tmp_path), "--config", "espion_smoke"])
    out = capsys.readouterr().out
    assert "fx: FAIL (effect -0.200 of the gap" in out and "A games 1, E games 1" in out
    assert code == 1


def test_validate_e_config_filter_repeatable(tmp_path, capsys):
    code = validate_e.main([write(tmp_path), "--config", "espion_pilot", "--config", "espion_smoke"])
    out = capsys.readouterr().out
    assert "configs: espion_pilot, espion_smoke" in out
    assert "fx: FAIL (effect 0.133 of the gap" in out and "A games 3, E games 3" in out
    assert code == 1


def test_validate_e_config_filter_unknown_config_is_no_games(tmp_path, capsys):
    code = validate_e.main([write(tmp_path), "--config", "espion_core"])
    out = capsys.readouterr().out
    assert "no games" in out
    assert code == 1


def test_validate_e_config_filter_matches_whole_prefix_only(tmp_path, capsys):
    # "espion" is a prefix of the game id text but not a config name: nothing kept
    code = validate_e.main([write(tmp_path), "--config", "espion"])
    assert "no games" in capsys.readouterr().out and code == 1
