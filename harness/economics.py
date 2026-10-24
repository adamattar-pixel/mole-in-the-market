"""R01: demand models, Nash and joint monopoly prices for a symmetric 2-firm game.

Prices are found numerically (best-response iteration and golden-section search on profits),
so the solver does not reuse the closed forms that the tests derive by hand.
"""
import math

_GOLDEN = (math.sqrt(5) - 1) / 2


class LinearDemand:
    """q_i = a - b * p_i + d * p_j, unit cost c."""

    def __init__(self, a, b, d, c):
        if b <= 0 or d < 0 or b <= d:
            raise ValueError("linear demand needs b > d >= 0")
        self.a, self.b, self.d, self.c = float(a), float(b), float(d), float(c)

    def quantities(self, p1, p2):
        return (self.a - self.b * p1 + self.d * p2, self.a - self.b * p2 + self.d * p1)

    def profits(self, p1, p2):
        q1, q2 = self.quantities(p1, p2)
        return ((p1 - self.c) * q1, (p2 - self.c) * q2)

    @property
    def unit_cost(self):
        return self.c

    def price_bounds(self):
        # Search range: from cost up to the price where own demand vanishes against a rival at that price.
        return (self.c, self.c + self.a / (self.b - self.d) + 1.0)


class LogitDemand:
    """Fish-style logit demand.

    q_i = beta * exp((a - p_i/alpha)/mu) / (sum_j exp((a - p_j/alpha)/mu) + exp(a0/mu))
    profit_i = (p_i - alpha * c) * q_i
    """

    def __init__(self, a, a0, mu, c, beta=1.0, alpha=1.0):
        if mu <= 0 or beta <= 0 or alpha <= 0:
            raise ValueError("logit demand needs mu, beta, alpha > 0")
        self.a, self.a0, self.mu, self.c = float(a), float(a0), float(mu), float(c)
        self.beta, self.alpha = float(beta), float(alpha)

    def quantities(self, p1, p2):
        u1 = (self.a - p1 / self.alpha) / self.mu
        u2 = (self.a - p2 / self.alpha) / self.mu
        u0 = self.a0 / self.mu
        m = max(u1, u2, u0)
        e1, e2, e0 = math.exp(u1 - m), math.exp(u2 - m), math.exp(u0 - m)
        tot = e1 + e2 + e0
        return (self.beta * e1 / tot, self.beta * e2 / tot)

    def profits(self, p1, p2):
        q1, q2 = self.quantities(p1, p2)
        unit = self.alpha * self.c
        return ((p1 - unit) * q1, (p2 - unit) * q2)

    @property
    def unit_cost(self):
        return self.alpha * self.c

    def price_bounds(self):
        unit = self.alpha * self.c
        return (unit, unit + self.alpha * (abs(self.a) + abs(self.a0) + 50 * self.mu + 10))


_REQUIRED = {
    "linear": ("a", "b", "d", "c"),
    "logit": ("a", "a0", "mu", "c"),
}


def make_demand(params):
    kind = params.get("type")
    if kind not in _REQUIRED:
        raise ValueError(f"unknown demand type: {kind!r}")
    missing = [k for k in _REQUIRED[kind] if k not in params]
    if missing:
        raise ValueError(f"missing demand parameters: {missing}")
    if kind == "linear":
        return LinearDemand(params["a"], params["b"], params["d"], params["c"])
    return LogitDemand(params["a"], params["a0"], params["mu"], params["c"],
                       beta=params.get("beta", 1.0), alpha=params.get("alpha", 1.0))


def _argmax(f, lo, hi, tol=1e-10):
    """Golden-section search for the maximum of a unimodal function on [lo, hi]."""
    x1 = hi - _GOLDEN * (hi - lo)
    x2 = lo + _GOLDEN * (hi - lo)
    f1, f2 = f(x1), f(x2)
    while hi - lo > tol:
        if f1 < f2:
            lo, x1, f1 = x1, x2, f2
            x2 = lo + _GOLDEN * (hi - lo)
            f2 = f(x2)
        else:
            hi, x2, f2 = x2, x1, f1
            x1 = hi - _GOLDEN * (hi - lo)
            f1 = f(x1)
    return (lo + hi) / 2


def nash_price(demand, max_iter=500, tol=1e-8):
    """Symmetric Nash price by best-response iteration.

    Golden-section search resolves an optimum to about 1e-8 (profit is flat near its maximum),
    so the convergence tolerance is set at that level.
    """
    lo, hi = demand.price_bounds()
    p = (lo + hi) / 2
    for _ in range(max_iter):
        best = _argmax(lambda x: demand.profits(x, p)[0], lo, hi)
        if abs(best - p) < tol:
            return best
        p = best
    raise RuntimeError("Nash iteration did not converge")


def monopoly_price(demand):
    """Joint monopoly price: both firms charge the same price that maximizes total profit."""
    lo, hi = demand.price_bounds()
    return _argmax(lambda x: sum(demand.profits(x, x)), lo, hi)


def deal_price(demand):
    """The deal price is the joint monopoly price (PREREGISTRATION.md, Definitions)."""
    return monopoly_price(demand)
