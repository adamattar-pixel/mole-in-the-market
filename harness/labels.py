"""R14: labels.csv, one line per game.

base_rate column: mean of the permutation base-rate distribution of the game's model family
(A and D games of that family, R10). Empty when the family has no A or D game.
"""
import csv

from harness.conditions import condition_metadata
from harness.metrics import (behavioral_acceptance_game, false_positive_game, permutation_base_rate,
                             verbal_acceptance_game)

LABEL_COLUMNS = ("game_id", "family", "seed", "condition", "offer_form", "trust_label",
                 "verbal", "behavioral", "false_positive", "base_rate")


def exploratory_arm(log):
    """"memory" or "think" for a game of an EXPLORATORY arm (MEMORY_ARM.md, THINK_ARM.md), else "frozen"."""
    if log.get("memory", False):
        return "memory"
    if log.get("think", False):
        return "think"
    return "frozen"


def check_one_arm(logs):
    """Refuse a set of games that pools exploratory arms with each other or with the frozen design."""
    arms = sorted({exploratory_arm(g) for g in logs})
    if len(arms) > 1:
        raise ValueError(f"logs mix exploratory arms and frozen games ({', '.join(arms)}): never pooled, "
                         "score each folder separately")


def family_base_rates(logs, n_draws, seed):
    """family -> list of draws (or None when the family has no A or D game)."""
    out = {}
    for fam in sorted({g["family"] for g in logs}):
        ad = [g for g in logs if g["family"] == fam and g["condition"] in ("A", "D")]
        out[fam] = permutation_base_rate(ad, n_draws=n_draws, seed=seed) if ad else None
    return out


def make_labels(logs, n_draws=1000, seed=0, base_rates=None):
    check_one_arm(logs)
    if base_rates is None:
        base_rates = family_base_rates(logs, n_draws, seed)
    rows = []
    for g in sorted(logs, key=lambda x: x["game_id"]):
        form, trust = condition_metadata(g["condition"])
        draws = base_rates.get(g["family"])
        rows.append({
            "game_id": g["game_id"], "family": g["family"], "seed": g["seed"], "condition": g["condition"],
            "offer_form": form, "trust_label": trust,
            "verbal": int(verbal_acceptance_game(g)), "behavioral": int(behavioral_acceptance_game(g)),
            "false_positive": int(false_positive_game(g)),
            "base_rate": None if draws is None else sum(draws) / len(draws),
        })
    return rows


def write_labels_csv(rows, path):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=LABEL_COLUMNS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            out = dict(r)
            out["base_rate"] = "" if r["base_rate"] is None else f"{r['base_rate']:.6f}"
            w.writerow(out)
