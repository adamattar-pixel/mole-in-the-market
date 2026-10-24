"""R22 viz export, R23 consistency with labels.csv, R27 report figure (game grid).

Data contract: docs/viz/DESIGN.md. Everything here is computed from runs/ and labels; nothing is typed by hand.
"""
import csv
import hashlib
import json
from pathlib import Path

from harness.conditions import CONDITIONS, build_condition

CONDITION_NAMES = {"A": "No spy", "E": "Deal allowed (control)", "B": "Direct offer",
                   "B_T": "Trusted direct offer", "C": "Hint", "D": "Harmless request"}

OUTCOME_COLORS = {"say_do": "#3ddc97", "say_only": "#f0b429", "do_only": "#a78bfa", "neither": "#3a4350"}

OUTCOME_LABELS = {"say_do": "said yes and moved prices", "say_only": "said yes only",
                  "do_only": "moved prices only", "neither": "neither"}

GAMES_COLUMNS = ("game_id", "condition", "condition_name", "family", "seed", "say", "do", "outcome",
                 "nash", "monopoly", "deal_price", "spy_start", "rounds")
ROUNDS_COLUMNS = ("game_id", "round", "firm", "price", "reply")


def outcome(say, do):
    if say and do:
        return "say_do"
    if say:
        return "say_only"
    if do:
        return "do_only"
    return "neither"


def _write_csv(path, columns, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def _read_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def export_viz(logs, label_rows, viz_dir, texts, prereg_path, source_checksum, generated_at):
    viz_dir = Path(viz_dir)
    viz_dir.mkdir(parents=True, exist_ok=True)
    by_id = {g["game_id"]: g for g in logs}
    games = []
    for lab in label_rows:
        g = by_id[lab["game_id"]]
        games.append({
            "game_id": g["game_id"], "condition": g["condition"], "condition_name": CONDITION_NAMES[g["condition"]],
            "family": g["family"], "seed": g["seed"], "say": lab["verbal"], "do": lab["behavioral"],
            "outcome": outcome(lab["verbal"], lab["behavioral"]), "nash": g["nash_price"],
            "monopoly": g["monopoly_price"], "deal_price": g["deal_price"], "spy_start": g["spy_start"],
            "rounds": len(g["rounds"]),
        })
    rounds = []
    for lab in label_rows:
        g = by_id[lab["game_id"]]
        for r in g["rounds"]:
            for f in sorted(r["firms"]):
                fr = r["firms"][f]
                rounds.append({"game_id": g["game_id"], "round": r["round"], "firm": f, "price": fr["price"],
                               "reply": fr["response_to_message"] if r["round"] == g["spy_start"] else ""})
    messages = []
    if logs:
        deal = logs[0]["deal_price"]
        for c in CONDITIONS:
            msg = build_condition(c, texts, deal).message
            if msg is not None:
                messages.append({"condition": c, "text": msg})
    meta = {"synthetic": False, "source_checksum": source_checksum,
            "prereg_hash": hashlib.sha256(Path(prereg_path).read_bytes()).hexdigest(),
            "generated_at": generated_at}
    _write_csv(viz_dir / "games.csv", GAMES_COLUMNS, games)
    _write_csv(viz_dir / "rounds.csv", ROUNDS_COLUMNS, rounds)
    _write_csv(viz_dir / "messages.csv", ("condition", "text"), messages)
    (viz_dir / "meta.json").write_text(json.dumps(meta, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    data = {"games": games, "rounds": rounds, "messages": messages, "meta": meta}
    (viz_dir / "data.js").write_text("window.MM_DATA = " + json.dumps(data, sort_keys=True) + ";\n",
                                     encoding="utf-8")


def check_consistency(labels_csv, games_csv, runs_dir):
    """List of problems (empty when viz/data/games.csv matches labels.csv and runs/)."""
    problems = []
    labels = {r["game_id"]: r for r in _read_csv(labels_csv)}
    games = {r["game_id"]: r for r in _read_csv(games_csv)}
    n_runs = len(list(Path(runs_dir).glob("*.json")))
    if not len(labels) == len(games) == n_runs:
        problems.append(f"row counts differ: labels {len(labels)}, games {len(games)}, runs {n_runs}")
    for gid in sorted(set(labels) | set(games)):
        if gid not in labels or gid not in games:
            problems.append(f"{gid}: present in only one of labels.csv and games.csv")
            continue
        lab, gam = labels[gid], games[gid]
        if gam["say"] != lab["verbal"] or gam["do"] != lab["behavioral"]:
            problems.append(f"{gid}: say/do differ from labels.csv")
        if gam["outcome"] != outcome(lab["verbal"] == "1", lab["behavioral"] == "1"):
            problems.append(f"{gid}: outcome does not match say/do")
    return problems


def make_game_grid(games_csv, out_pdf):
    """Figure 1: one cell per game, rows = conditions, columns = family x seed, color = outcome."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch, Rectangle

    games = _read_csv(games_csv)
    families = sorted({g["family"] for g in games})
    seeds = {f: sorted({int(g["seed"]) for g in games if g["family"] == f}) for f in families}
    columns = [(f, s) for f in families for s in seeds[f]]
    rows = [c for c in CONDITIONS if any(g["condition"] == c for g in games)] or list(CONDITIONS)
    cell = {(g["condition"], g["family"], int(g["seed"])): g["outcome"] for g in games}

    fig, ax = plt.subplots(figsize=(1.2 + 0.42 * max(len(columns), 1), 0.9 + 0.42 * len(rows)))
    for i, cond in enumerate(rows):
        for j, (fam, seed) in enumerate(columns):
            out = cell.get((cond, fam, seed))
            face = OUTCOME_COLORS[out] if out else "#ffffff"
            ax.add_patch(Rectangle((j, len(rows) - 1 - i), 0.9, 0.9, facecolor=face, edgecolor="#2a313a",
                                   linewidth=0.5))
    ax.set_xlim(-0.1, max(len(columns), 1))
    ax.set_ylim(-0.1, len(rows))
    ax.set_yticks([len(rows) - 1 - i + 0.45 for i in range(len(rows))])
    ax.set_yticklabels([CONDITION_NAMES[c] for c in rows], fontsize=7)
    ax.set_xticks([j + 0.45 for j in range(len(columns))])
    ax.set_xticklabels([f"{f}\ns{s}" for f, s in columns], fontsize=5)
    ax.tick_params(length=0)
    for side in ax.spines.values():
        side.set_visible(False)
    ax.set_aspect("equal")
    ax.legend(handles=[Patch(facecolor=OUTCOME_COLORS[k], label=OUTCOME_LABELS[k]) for k in OUTCOME_COLORS],
              loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, fontsize=6, frameon=False)
    fig.tight_layout()
    Path(out_pdf).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_pdf, format="pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)
