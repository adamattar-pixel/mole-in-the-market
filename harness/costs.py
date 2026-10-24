"""R17: measured cost per game, from the cost_usd field of each log."""


def _block(games):
    total = float(sum(g["cost_usd"] for g in games))
    return {"games": len(games), "total_usd": total, "mean_per_game_usd": (total / len(games)) if games else None}


def cost_summary(logs):
    """Per family and overall ("all"): number of games, total and mean cost per game in USD."""
    out = {fam: _block([g for g in logs if g["family"] == fam]) for fam in sorted({g["family"] for g in logs})}
    out["all"] = _block(list(logs))
    return out
