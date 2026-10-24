"""R01: 2-firm game, Nash and monopoly prices from demand parameters (known answers)."""
import math

import pytest

from harness.config import GameConfig
from harness.economics import (LinearDemand, LogitDemand, deal_price, make_demand,
                               monopoly_price, nash_price)


# Linear demand q_i = a - b p_i + d p_j, cost c.
# Nash: d/dp_i [(p_i - c)(a - b p_i + d p_j)] = a - 2b p_i + d p_j + b c = 0,
#   symmetric -> p = (a + b c) / (2b - d).
# Joint monopoly (symmetric p): max (p - c)(a - (b - d) p)
#   -> a - 2(b - d) p + (b - d) c = 0 -> p = (a + (b - d) c) / (2 (b - d)).
# a=10, b=2, d=1, c=1: Nash = (10 + 2) / 3 = 4.0 ; monopoly = (10 + 1) / 2 = 5.5
def test_R01_linear_known_answer():
    dem = LinearDemand(a=10, b=2, d=1, c=1)
    assert nash_price(dem) == pytest.approx(4.0, abs=1e-6)
    assert monopoly_price(dem) == pytest.approx(5.5, abs=1e-6)


# Second linear case: a=20, b=4, d=2, c=2: Nash = (20 + 8) / 6 = 4.6667 ; monopoly = (20 + 4) / 4 = 6.0
def test_R01_linear_second_case():
    dem = LinearDemand(a=20, b=4, d=2, c=2)
    assert nash_price(dem) == pytest.approx(28 / 6, abs=1e-6)
    assert monopoly_price(dem) == pytest.approx(6.0, abs=1e-6)


def test_R01_linear_quantities_and_profits():
    # p1=4, p2=5: q1 = 10 - 8 + 5 = 7, q2 = 10 - 10 + 4 = 4 ; profits (4-1)*7 = 21, (5-1)*4 = 16
    dem = LinearDemand(a=10, b=2, d=1, c=1)
    assert dem.quantities(4, 5) == pytest.approx((7, 4))
    assert dem.profits(4, 5) == pytest.approx((21, 16))


def _logit_share(p, a=2.0, a0=0.0, mu=0.25):
    # symmetric price p (alpha = 1): s = e / (2e + e0)
    e = math.exp((a - p) / mu)
    return e / (2 * e + math.exp(a0 / mu))


# Logit, alpha = 1. Independent first order conditions written here:
# Nash: dq_i/dp_i = -q_i (1 - s_i) / mu  ->  p - c = mu / (1 - s)
# Joint monopoly (symmetric): ds/dp = -(s / mu)(1 - 2 s)  ->  p - c = mu / (1 - 2 s)
def test_R01_logit_first_order_conditions():
    dem = LogitDemand(a=2.0, a0=0.0, mu=0.25, c=1.0, beta=100.0, alpha=1.0)
    pn, pm = nash_price(dem), monopoly_price(dem)
    sn, sm = _logit_share(pn), _logit_share(pm)
    assert pn - 1.0 == pytest.approx(0.25 / (1 - sn), abs=1e-5)
    assert pm - 1.0 == pytest.approx(0.25 / (1 - 2 * sm), abs=1e-5)
    assert pm > pn


# Published values (Calvano et al. 2020, a=2, a0=0, mu=0.25, c=1): p_N ~ 1.473, p_M ~ 1.925.
# Hand check of the FOC: p=1.473 -> e^(0.527/0.25)=8.23, s=8.23/17.46=0.471, 0.25/0.529=0.473 ok.
def test_R01_logit_published_values():
    dem = LogitDemand(a=2.0, a0=0.0, mu=0.25, c=1.0)
    assert nash_price(dem) == pytest.approx(1.473, abs=2e-3)
    assert monopoly_price(dem) == pytest.approx(1.925, abs=2e-3)


# With price p and alpha, profit = alpha (p/alpha - c) q(p/alpha): optimum scales linearly in alpha.
def test_R01_logit_alpha_scaling():
    base = LogitDemand(a=2.0, a0=0.0, mu=0.25, c=1.0, alpha=1.0)
    scaled = LogitDemand(a=2.0, a0=0.0, mu=0.25, c=1.0, alpha=3.2)
    assert nash_price(scaled) == pytest.approx(3.2 * nash_price(base), rel=1e-5)
    assert monopoly_price(scaled) == pytest.approx(3.2 * monopoly_price(base), rel=1e-5)


def test_R01_logit_quantities_symmetric_at_equal_prices():
    # p1 = p2 = 2 = a: e = exp(0) = 1, e0 = 1 -> q = beta * 1/3 each
    dem = LogitDemand(a=2.0, a0=0.0, mu=0.25, c=1.0, beta=90.0)
    q1, q2 = dem.quantities(2.0, 2.0)
    assert q1 == pytest.approx(30.0) and q2 == pytest.approx(30.0)
    # profit = (2 - 1) * 30
    assert dem.profits(2.0, 2.0) == pytest.approx((30.0, 30.0))


def test_R01_deal_price_is_joint_monopoly_price():
    dem = LinearDemand(a=10, b=2, d=1, c=1)
    assert deal_price(dem) == pytest.approx(5.5, abs=1e-6)


def test_R01_invalid_parameters_rejected():
    with pytest.raises(ValueError):
        LogitDemand(a=2.0, a0=0.0, mu=0.0, c=1.0)
    with pytest.raises(ValueError):
        LinearDemand(a=10, b=1, d=1, c=1)  # b <= d: no finite monopoly price


def test_R01_make_demand_from_config():
    dem = make_demand({"type": "linear", "a": 10, "b": 2, "d": 1, "c": 1})
    assert nash_price(dem) == pytest.approx(4.0, abs=1e-6)
    with pytest.raises(ValueError):
        make_demand({"type": "cubic"})
    with pytest.raises((ValueError, KeyError)):
        make_demand({"type": "logit", "a": 2.0})


def test_R01_game_config_from_dict():
    cfg = GameConfig.from_dict({
        "n_rounds": 20, "spy_start": 8,
        "demand": {"type": "linear", "a": 10, "b": 2, "d": 1, "c": 1},
    })
    assert cfg.n_rounds == 20 and cfg.spy_start == 8
    assert cfg.nash_price == pytest.approx(4.0, abs=1e-6)
    assert cfg.monopoly_price == pytest.approx(5.5, abs=1e-6)
    assert cfg.deal_price == pytest.approx(5.5, abs=1e-6)


def test_R01_game_config_rejects_bad_rounds():
    demand = {"type": "linear", "a": 10, "b": 2, "d": 1, "c": 1}
    with pytest.raises(ValueError):
        GameConfig.from_dict({"n_rounds": 5, "spy_start": 6, "demand": demand})
    with pytest.raises(ValueError):
        GameConfig.from_dict({"n_rounds": 0, "spy_start": 1, "demand": demand})
    with pytest.raises(ValueError):
        GameConfig.from_dict({"n_rounds": 10, "spy_start": 0, "demand": demand})
