"""Extra known-answer checks for tools/price_paths.py (window length, interval quantile), added after the
mutation check showed the locked tests in test_artem_price_shift.py could not catch them."""
import pytest

from helpers3 import full_log
from tools import price_paths as pp


def test_window_mean_uses_every_window_round():
    # spy_start 2 -> window rounds 3, 4, 5 with two-firm means 10, 13, 19 -> 42 / 3 = 14
    log = full_log("B", "fx", 1, [(10.0, 10.0)] * 2 + [(10.0, 10.0), (12.0, 14.0), (19.0, 19.0), (1.0, 1.0)],
                   spy_start=2)
    assert pp.window_mean(log, 3, 5) == pytest.approx(14.0)


@pytest.mark.parametrize("q,expected", [(0.0, 0.0), (0.025, 0.1), (0.5, 2.0), (0.975, 3.9), (1.0, 4.0)])
def test_quantile_linear_interpolation_by_hand(q, expected):
    # positions q x 4 on [0, 1, 2, 3, 4]: 0.1 and 3.9 at the 2.5% and 97.5% points
    assert pp._quantile([0.0, 1.0, 2.0, 3.0, 4.0], q) == pytest.approx(expected)


def test_shift_interval_uses_the_95_percent_points():
    import random
    logs = [full_log("A", "fz", s, [(10.0, 10.0)] * 6, spy_start=2) for s in (1, 2)]
    logs += [full_log("B", "fz", s, [(10.0, 10.0)] * 2 + [(v, v)] * 4, spy_start=2)
             for s, v in ((1, 11.0), (2, 12.0), (3, 13.0), (4, 14.0), (5, 15.0))]
    e = pp.price_shift(logs, n_boot=400, seed=3)["fz"]["B"]
    assert e["shift"] == pytest.approx(3.0)
    # independent recomputation of the same seeded resampling (reference has zero spread)
    rng = random.Random("3|fz|B")
    x, r = [1.0 + k for k in range(5)], [0.0, 0.0]
    draws = sorted(sum(rng.choice(x) for _ in x) / 5 - sum(rng.choice(r) for _ in r) / 2 for _ in range(400))
    assert e["lo"] == pytest.approx(pp._quantile(draws, 0.025))
    assert e["lo"] > min(draws) and e["hi"] < max(draws)
