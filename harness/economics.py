"""R01: demand models, Nash and joint monopoly prices for a symmetric 2-firm game."""


class LinearDemand:
    """q_i = a - b * p_i + d * p_j, unit cost c."""

    def __init__(self, a, b, d, c):
        raise NotImplementedError

    def quantities(self, p1, p2):
        raise NotImplementedError

    def profits(self, p1, p2):
        raise NotImplementedError


class LogitDemand:
    """Fish-style logit demand.

    q_i = beta * exp((a - p_i/alpha)/mu) / (sum_j exp((a - p_j/alpha)/mu) + exp(a0/mu))
    profit_i = (p_i - alpha * c) * q_i
    """

    def __init__(self, a, a0, mu, c, beta=1.0, alpha=1.0):
        raise NotImplementedError

    def quantities(self, p1, p2):
        raise NotImplementedError

    def profits(self, p1, p2):
        raise NotImplementedError


def make_demand(params):
    raise NotImplementedError


def nash_price(demand):
    raise NotImplementedError


def monopoly_price(demand):
    raise NotImplementedError


def deal_price(demand):
    raise NotImplementedError
