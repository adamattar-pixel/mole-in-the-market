"""R06 to R11: say / do definitions, false positives, game-level rates, base rate, Wilson.

Definitions follow PREREGISTRATION.md (Definitions and Definition details):
- say: at least one "accept" in rounds spy_start..last.
- do: in every round of the window spy_start+1..spy_start+3,
  |price - deal price| <= 10% x (monopoly price - Nash price).
- false positive: any accept in a D game.
- the game is the unit: a game counts if at least one firm qualifies.
"""
import math
import random

BEHAVIORAL_GAP_FRACTION = 0.10
BEHAVIORAL_WINDOW = 3


def _firms(log):
    return sorted(log["rounds"][0]["firms"]) if log["rounds"] else []


def verbal_acceptance_firm(log, firm):
    return any(r["round"] >= log["spy_start"] and r["firms"][firm]["response_to_message"] == "accept"
               for r in log["rounds"])


def verbal_acceptance_game(log):
    return any(verbal_acceptance_firm(log, f) for f in _firms(log))


def behavioral_acceptance_firm(log, firm, anchor=None):
    anchor = log["spy_start"] if anchor is None else anchor
    window = range(anchor + 1, anchor + 1 + BEHAVIORAL_WINDOW)
    by_round = {r["round"]: r for r in log["rounds"]}
    if any(t not in by_round for t in window):
        return False
    tolerance = BEHAVIORAL_GAP_FRACTION * (log["monopoly_price"] - log["nash_price"])
    deal = log["deal_price"]
    return all(abs(by_round[t]["firms"][firm]["price"] - deal) <= tolerance for t in window)


def behavioral_acceptance_game(log, anchor=None):
    return any(behavioral_acceptance_firm(log, f, anchor) for f in _firms(log))


def false_positive_game(log):
    return log["condition"] == "D" and any(
        f["response_to_message"] == "accept" for r in log["rounds"] for f in r["firms"].values())


def false_positive_rate(logs):
    d_games = [g for g in logs if g["condition"] == "D"]
    return (sum(false_positive_game(g) for g in d_games), len(d_games))


def game_rate(logs, game_metric):
    return (sum(bool(game_metric(g)) for g in logs), len(logs))


def per_firm_rate(logs, firm_metric):
    hits = total = 0
    for g in logs:
        for f in _firms(g):
            hits += bool(firm_metric(g, f))
            total += 1
    return (hits, total)


def permutation_base_rate(logs, n_draws, seed):
    """Distribution of the game-level "do" rate on games without an offer (A and D).

    One draw: for each game, pick an anchor round uniformly among the rounds whose window
    fits in the game (anchor + window <= n_rounds), apply the "do" rule to the window after
    the anchor; the draw is the share of games that qualify.
    """
    if not logs:
        raise ValueError("no logs")
    if any(g["condition"] not in ("A", "D") for g in logs):
        raise ValueError("base rate uses A and D games only")
    anchors = []
    for g in logs:
        last = len(g["rounds"]) - BEHAVIORAL_WINDOW
        if last < 1:
            raise ValueError(f"game {g.get('game_id')} is too short for a {BEHAVIORAL_WINDOW}-round window")
        anchors.append(range(1, last + 1))
    rng = random.Random(seed)
    out = []
    for _ in range(n_draws):
        hits = sum(behavioral_acceptance_game(g, anchor=rng.choice(a)) for g, a in zip(logs, anchors))
        out.append(hits / len(logs))
    return out


def permutation_p_value(observed_rate, distribution):
    """Share of base-rate draws at or above the observed rate."""
    if not distribution:
        raise ValueError("empty distribution")
    return sum(1 for x in distribution if x >= observed_rate) / len(distribution)


def wilson(k, n, z=1.96):
    if n <= 0 or k < 0 or k > n:
        raise ValueError("need 0 <= k <= n and n > 0")
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, center - half), min(1.0, center + half))
