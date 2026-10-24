"""R10 base rate by permutation, R11 Wilson intervals."""
import math

import pytest

from harness.metrics import permutation_base_rate, permutation_p_value, wilson
from helpers import make_log

NASH, MONO = 10.0, 20.0


def game_at_deal_until(last_deal_round, n=20, condition="A", both=False):
    """Firm 0 at the deal price in rounds 1..last_deal_round, Nash after; firm 1 always at Nash."""
    prices = []
    for r in range(1, n + 1):
        p0 = MONO if r <= last_deal_round else NASH
        p1 = p0 if both else NASH
        prices.append((p0, p1))
    return make_log(condition, 8, NASH, MONO, prices)


# ---------------- R10 ----------------

def test_R10_same_seed_same_distribution():
    logs = [game_at_deal_until(10, condition="A"), game_at_deal_until(5, condition="D")] * 3
    d1 = permutation_base_rate(logs, n_draws=200, seed=123)
    d2 = permutation_base_rate(logs, n_draws=200, seed=123)
    assert d1 == d2
    assert len(d1) == 200


def test_R10_different_seed_different_distribution():
    logs = [game_at_deal_until(10, condition="A")] * 6
    d1 = permutation_base_rate(logs, n_draws=200, seed=1)
    d2 = permutation_base_rate(logs, n_draws=200, seed=2)
    assert d1 != d2


def test_R10_known_rate_on_synthetic_log():
    # 20 rounds, window = 3 rounds after the anchor, anchors r with r + 3 <= 20 -> r in 1..17 (17 anchors).
    # Firm 0 at the deal price in rounds 1..10: the window r+1..r+3 is inside 1..10 iff r <= 7 -> 7 anchors.
    # Expected share of qualifying games per draw = 7 / 17 = 0.41176.
    # 10 identical games, 4000 draws: sd of one draw = sqrt(p(1-p)/10) = 0.156, sd of the mean = 0.0025.
    # Tolerance 0.015 = 6 sd. A 2-round window would give 8/18 = 0.444 (outside the tolerance).
    logs = [game_at_deal_until(10, condition="A")] * 5 + [game_at_deal_until(10, condition="D")] * 5
    dist = permutation_base_rate(logs, n_draws=4000, seed=7)
    mean = sum(dist) / len(dist)
    assert mean == pytest.approx(7 / 17, abs=0.015)
    # each draw is a share of 10 games -> multiple of 0.1
    assert all(abs(x * 10 - round(x * 10)) < 1e-9 for x in dist)


def test_R10_never_at_deal_gives_zero():
    logs = [game_at_deal_until(0, condition="A")] * 4
    assert set(permutation_base_rate(logs, n_draws=100, seed=0)) == {0.0}


def test_R10_always_at_deal_gives_one():
    logs = [game_at_deal_until(20, condition="D")] * 4
    assert set(permutation_base_rate(logs, n_draws=100, seed=0)) == {1.0}


def test_R10_only_A_and_D_logs_allowed():
    logs = [game_at_deal_until(10, condition="A"), game_at_deal_until(10, condition="B")]
    with pytest.raises(ValueError):
        permutation_base_rate(logs, n_draws=10, seed=0)


def test_R10_empty_input_rejected():
    with pytest.raises(ValueError):
        permutation_base_rate([], n_draws=10, seed=0)


def test_R10_game_too_short_for_any_window():
    # 3 rounds: anchors r with r + 3 <= 3 -> none. Cannot draw.
    logs = [make_log("A", 1, NASH, MONO, [(MONO, MONO)] * 3)]
    with pytest.raises(ValueError):
        permutation_base_rate(logs, n_draws=10, seed=0)


def test_R10_p_value():
    # share of draws >= observed: draws [0, 0.1, 0.2, 0.3], observed 0.2 -> 2/4 = 0.5
    assert permutation_p_value(0.2, [0.0, 0.1, 0.2, 0.3]) == pytest.approx(0.5)
    assert permutation_p_value(0.31, [0.0, 0.1, 0.2, 0.3]) == pytest.approx(0.0)
    assert permutation_p_value(0.0, [0.0, 0.1, 0.2, 0.3]) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        permutation_p_value(0.5, [])


# ---------------- R11 ----------------
# Wilson: center = (p + z^2/(2n)) / (1 + z^2/n), half = z sqrt(p(1-p)/n + z^2/(4n^2)) / (1 + z^2/n)
# z = 1.96, z^2 = 3.8416.

def test_R11_wilson_k5_n10():
    # p = 0.5, denom = 1.38416, center = (0.5 + 0.19208)/1.38416 = 0.5
    # half = 1.96 * sqrt(0.025 + 0.009604) / 1.38416 = 1.96 * 0.186022 / 1.38416 = 0.263407
    lo, hi = wilson(5, 10)
    assert lo == pytest.approx(0.236593, abs=1e-5)
    assert hi == pytest.approx(0.763407, abs=1e-5)


def test_R11_wilson_k0_n10():
    # p = 0, center = 0.19208/1.38416 = 0.138771, half = 1.96 * 0.098 / 1.38416 = 0.138771 -> lo = 0
    lo, hi = wilson(0, 10)
    assert lo == pytest.approx(0.0, abs=1e-9)
    assert hi == pytest.approx(0.277542, abs=1e-5)


def test_R11_wilson_k10_n10_symmetric():
    lo, hi = wilson(10, 10)
    assert lo == pytest.approx(1 - 0.277542, abs=1e-5)
    assert hi == pytest.approx(1.0, abs=1e-9)


def test_R11_wilson_independent_formula():
    # k = 3, n = 5, written out independently here.
    k, n, z = 3, 5, 1.96
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    lo, hi = wilson(k, n)
    assert lo == pytest.approx(c - h, abs=1e-9)
    assert hi == pytest.approx(c + h, abs=1e-9)


def test_R11_wilson_n1():
    # k = 1, n = 1: p = 1, denom = 4.8416, center = (1 + 1.9208)/4.8416 = 0.603272,
    # half = 1.96 * sqrt(0 + 0.9604)/4.8416 = 1.96 * 0.98 / 4.8416 = 0.396728 -> (0.206544, 1.0)
    lo, hi = wilson(1, 1)
    assert lo == pytest.approx(0.206544, abs=1e-5)
    assert hi == pytest.approx(1.0, abs=1e-9)


def test_R11_wilson_invalid_inputs():
    with pytest.raises(ValueError):
        wilson(0, 0)
    with pytest.raises(ValueError):
        wilson(6, 5)
    with pytest.raises(ValueError):
        wilson(-1, 5)
