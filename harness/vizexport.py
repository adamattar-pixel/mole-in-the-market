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


def excluded_family_summary(excluded_logs, threshold_gap_fraction):
    """Per family dropped at the E gate: game count, model ids and the gate result (positive control), so the
    page can show why the family is missing instead of hiding it."""
    from harness.validation import e_validation
    gate = e_validation(excluded_logs, threshold_gap_fraction)
    out = {}
    for fam, res in gate.items():
        gs = [g for g in excluded_logs if g["family"] == fam]
        models = sorted({m for g in gs for m in (g.get("models") or {}).values()})
        out[fam] = {"n_games": len(gs), "models": models, "e_validation": res}
    return out


def export_viz(logs, label_rows, viz_dir, texts, prereg_path, source_checksum, generated_at, synthetic=False,
               excluded_families=None):
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
    meta = {"synthetic": bool(synthetic), "source_checksum": source_checksum,
            "prereg_hash": hashlib.sha256(Path(prereg_path).read_bytes()).hexdigest(),
            "generated_at": generated_at}
    if excluded_families:
        meta["excluded_families"] = excluded_families
    _write_csv(viz_dir / "games.csv", GAMES_COLUMNS, games)
    _write_csv(viz_dir / "rounds.csv", ROUNDS_COLUMNS, rounds)
    _write_csv(viz_dir / "messages.csv", ("condition", "text"), messages)
    (viz_dir / "meta.json").write_text(json.dumps(meta, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    data = {"games": games, "rounds": rounds, "messages": messages, "meta": meta}
    (viz_dir / "data.js").write_text("window.MM_DATA = " + json.dumps(data, sort_keys=True) + ";\n",
                                     encoding="utf-8")


def check_consistency(labels_csv, games_csv, runs_dir, n_excluded=0):
    """List of problems (empty when viz/data/games.csv matches labels.csv and runs/ minus excluded games)."""
    problems = []
    labels = {r["game_id"]: r for r in _read_csv(labels_csv)}
    games = {r["game_id"]: r for r in _read_csv(games_csv)}
    n_runs = len(list(Path(runs_dir).glob("*.json"))) - n_excluded
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


FIGURE_CONDITION_NAMES = {"A": "No spy (baseline)", "E": "Deal allowed (positive control)", "B": "Direct offer",
                          "B_T": "Trusted direct offer", "C": "Hint", "D": "Harmless request"}

FAILED_CONTROL_NOTE = "failed positive control, exploratory"


def make_game_grid(games_csv, out_pdf, failed_families=()):
    """Figure 1: one row per family, one column group per condition (one cell per seed), color = outcome.

    failed_families: families whose positive control E failed (R13); their row label says so.
    Layout is in inches with fixed font sizes (8 pt), so labels never overlap and the width stays near
    one page column per condition group; no tight_layout, which keeps two runs byte-identical.
    """
    import textwrap

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch, Rectangle

    games = _read_csv(games_csv)
    failed = set(failed_families)
    families = sorted({g["family"] for g in games}) or [""]
    conds = [c for c in CONDITIONS if any(g["condition"] == c for g in games)] or list(CONDITIONS)
    seeds = {c: sorted({int(g["seed"]) for g in games if g["condition"] == c}) or [1] for c in conds}
    cell = {(g["condition"], g["family"], int(g["seed"])): g["outcome"] for g in games}

    fs = 8
    cw, gap = 0.16, 0.10          # cell width and gap between condition groups (inches)
    rh = 0.30                     # row height
    groups_w = sum(cw * len(seeds[c]) for c in conds) + gap * (len(conds) - 1)
    char_in = fs * 0.62 / 72      # generous average glyph width at fs
    row_labels = [f if f not in failed else f + "\n(" + FAILED_CONTROL_NOTE + ")" for f in families]
    row_labels = ["\n".join(textwrap.fill(part, 22) for part in lab.split("\n")) for lab in row_labels]
    left = 0.2 + char_in * max(len(line) for lab in row_labels for line in lab.split("\n"))
    head_lines = {c: textwrap.wrap(FIGURE_CONDITION_NAMES[c], max(6, int((cw * len(seeds[c]) + gap) / char_in)))
                  for c in conds}
    head_h = 0.05 + max(len(v) for v in head_lines.values()) * fs * 1.25 / 72
    seed_h = fs * 1.6 / 72
    legend_h = 2 * fs * 1.9 / 72 + 0.1
    max_lines = max(lab.count("\n") + 1 for lab in row_labels)
    rh = max(rh, max_lines * fs * 1.25 / 72 + 0.06)
    grid_h = rh * len(families)
    width = max(left + groups_w + 0.15, 4.6)
    height = head_h + seed_h + grid_h + legend_h + 0.1

    fig = plt.figure(figsize=(width, height))
    ax = fig.add_axes([left / width, (legend_h + 0.05) / height, groups_w / width, (grid_h + seed_h) / height])
    ax.set_xlim(0, groups_w)
    ax.set_ylim(-seed_h, grid_h)
    ax.axis("off")
    x = 0.0
    pad = 0.015
    for c in conds:
        gw = cw * len(seeds[c])
        ax.text(x + gw / 2, grid_h + 0.04, "\n".join(head_lines[c]), ha="center", va="bottom", fontsize=fs,
                linespacing=1.1, clip_on=False)
        for k, s in enumerate(seeds[c]):
            ax.text(x + k * cw + cw / 2, -seed_h / 2, f"s{s}", ha="center", va="center", fontsize=fs - 1.5,
                    color="#555555")
            for i, fam in enumerate(families):
                out = cell.get((c, fam, s))
                y = grid_h - (i + 1) * rh
                ax.add_patch(Rectangle((x + k * cw + pad, y + pad), cw - 2 * pad, rh - 2 * pad,
                                       facecolor=OUTCOME_COLORS[out] if out else "#ffffff",
                                       edgecolor="#2a313a", linewidth=0.5))
        x += gw + gap
    for i, lab in enumerate(row_labels):
        y = grid_h - (i + 0.5) * rh
        ax.text(-0.08, y, lab, ha="right", va="center", fontsize=fs, linespacing=1.1, clip_on=False,
                style="italic" if families[i] in failed else "normal",
                color="#9b1c1c" if families[i] in failed else "black")
    fig.legend(handles=[Patch(facecolor=OUTCOME_COLORS[k], edgecolor="#2a313a", linewidth=0.5,
                              label=OUTCOME_LABELS[k]) for k in OUTCOME_COLORS],
               loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=2, fontsize=fs, frameon=False,
               handlelength=1.4, columnspacing=1.5)
    Path(out_pdf).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_pdf, format="pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)
