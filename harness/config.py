"""R01: game parameters come from config."""
from dataclasses import dataclass

from harness.economics import deal_price, make_demand, monopoly_price, nash_price


@dataclass(frozen=True)
class GameConfig:
    n_rounds: int
    spy_start: int
    demand_params: dict
    nash_price: float
    monopoly_price: float
    deal_price: float

    @classmethod
    def from_dict(cls, d):
        n_rounds, spy_start = int(d["n_rounds"]), int(d["spy_start"])
        if n_rounds < 1:
            raise ValueError("n_rounds must be >= 1")
        if not 1 <= spy_start <= n_rounds:
            raise ValueError("spy_start must be in 1..n_rounds")
        demand = make_demand(d["demand"])
        return cls(n_rounds=n_rounds, spy_start=spy_start, demand_params=dict(d["demand"]),
                   nash_price=nash_price(demand), monopoly_price=monopoly_price(demand),
                   deal_price=deal_price(demand))

    def demand(self):
        return make_demand(self.demand_params)
