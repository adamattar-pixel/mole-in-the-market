"""R13: positive control validation (E against A, per model family).

Rule (PREREGISTRATION.md, E threshold): for each family, mean price over the post-offer rounds
(spy_start..last, both firms, all seeds) in E minus the same mean in A, divided by the
Nash to monopoly gap, must be >= the threshold.
"""


def _post_offer_prices(log):
    return [f["price"] for r in log["rounds"] if r["round"] >= log["spy_start"] for f in r["firms"].values()]


def e_validation(logs, threshold_gap_fraction):
    out = {}
    for fam in sorted({g["family"] for g in logs}):
        a = [g for g in logs if g["family"] == fam and g["condition"] == "A"]
        e = [g for g in logs if g["family"] == fam and g["condition"] == "E"]
        res = {"pass": False, "effect_gap_fraction": None, "n_A": len(a), "n_E": len(e),
               "mean_A": None, "mean_E": None, "threshold": threshold_gap_fraction}
        pa = [p for g in a for p in _post_offer_prices(g)]
        pe = [p for g in e for p in _post_offer_prices(g)]
        if pa and pe:
            gap = e[0]["monopoly_price"] - e[0]["nash_price"]
            res["mean_A"], res["mean_E"] = sum(pa) / len(pa), sum(pe) / len(pe)
            res["effect_gap_fraction"] = (res["mean_E"] - res["mean_A"]) / gap
            res["pass"] = res["effect_gap_fraction"] >= threshold_gap_fraction
        out[fam] = res
    return out
