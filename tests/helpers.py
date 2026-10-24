"""Hand-built game logs for the known-answer tests (test code only)."""


def make_log(condition, spy_start, nash, monopoly, prices, responses=None, deal=None):
    """prices: list of (p_firm0, p_firm1), one per round, round numbers start at 1.
    responses: list of (r_firm0, r_firm1), default no_message everywhere."""
    if responses is None:
        responses = [("no_message", "no_message")] * len(prices)
    assert len(responses) == len(prices)
    rounds = []
    for i, ((p0, p1), (r0, r1)) in enumerate(zip(prices, responses), start=1):
        rounds.append({
            "round": i,
            "firms": {
                "0": {"price": p0, "response_to_message": r0},
                "1": {"price": p1, "response_to_message": r1},
            },
        })
    return {
        "game_id": f"test-{condition}",
        "condition": condition,
        "spy_start": spy_start,
        "n_rounds": len(prices),
        "nash_price": nash,
        "monopoly_price": monopoly,
        "deal_price": monopoly if deal is None else deal,
        "rounds": rounds,
    }


def responses_with(n_rounds, accepts):
    """accepts: dict round_number -> (r_firm0, r_firm1); other rounds no_message."""
    out = []
    for r in range(1, n_rounds + 1):
        out.append(accepts.get(r, ("no_message", "no_message")))
    return out
