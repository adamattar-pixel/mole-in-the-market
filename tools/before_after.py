"""Key report figure: per game, the mean price before the offer vs the mean price in the "do" window.

Descriptive, from the logs only (no API key, no network). One point per game: x = mean price of both firms
over rounds spy_start-3 .. spy_start-1, y = the same over the do window spy_start+1 .. spy_start+3
(PREREGISTRATION.md window). Color = game-level say, marker = condition, one panel per family, with lines at
the Nash and deal prices on both axes and y = x. A small seeded jitter is added for legibility only; the CSV
keeps the exact means next to the plotted positions.

Say per firm: "accept" if it accepts in any round from spy_start on, else "decline" if it declines, else
"none". Game say: the firms' common value, or "mixed" when they differ. (The preregistered game-level say
counts a game when at least one firm accepts, so "mixed" games with an accept are say = yes there.)

Usage:
  python -m tools.before_after RUNS [RUNS ...] [--exploratory DIR ...] [--out-dir figures/exploratory]
                               [--include-mock] [--all-configs] [--seed 0]

Writes before_after.pdf, before_after.png and before_after.csv. Like tools/price_paths.py, the main folders
keep only real games (mock false) from the preregistered configs by default; --exploratory folders keep any
config and are drawn with hollow markers, flagged "exploratory" in the legend.
"""
import argparse
import csv
import random
from pathlib import Path

from harness.conditions import CONDITIONS
from harness.runlog import load_logs
from harness.vizexport import CONDITION_NAMES
from tools.price_paths import (DEFAULT_OUT_DIR, MARKERS, REF_COLOR, _base, _plt, arm_label, arm_of, do_window,
                               reference_lines, window_mean)
from tools.reproduce import PREREG_CONFIGS, filter_logs

JITTER = 0.01  # price units, uniform in [-JITTER, JITTER] on each axis
JITTER_SEED = 0
SAYS = ("accept", "decline", "none", "mixed")
SAY_COLORS = {"accept": "#eb6834", "decline": "#2a78d6", "none": "#8a8a82", "mixed": "#eda100"}
SAY_LABELS = {"accept": "Say: accept (both firms)", "decline": "Say: decline (both firms)",
              "none": "Say: none (no reply to an offer)", "mixed": "Say: mixed (the two firms differ)"}
DEAL_COLOR = "#1f1f1d"
MOCK_NOTE = "MOCK GAMES (dry run): not a result"
EXPLORATORY_LABEL = "Hollow marker: exploratory arm (not preregistered)"
CSV_COLUMNS = ("game_id", "family", "condition", "condition_name", "arm", "seed", "say", "before_mean",
               "do_mean", "x_plotted", "y_plotted", "nash", "deal", "exploratory", "mock", "source")


def before_window(spy_start):
    first, last = do_window(spy_start)
    w = last - first + 1
    return spy_start - w, spy_start - 1


def firm_say(log, firm):
    replies = [r["firms"][firm]["response_to_message"] for r in log["rounds"] if r["round"] >= log["spy_start"]]
    if "accept" in replies:
        return "accept"
    return "decline" if "decline" in replies else "none"


def game_say(log):
    says = {firm_say(log, f) for f in sorted(log["rounds"][0]["firms"])} if log["rounds"] else {"none"}
    return says.pop() if len(says) == 1 else "mixed"


def game_points(logs, exploratory=False, source=""):
    """(points, skipped game ids). A game is skipped when a round of either window is missing."""
    points, skipped = [], []
    for g in logs:
        x = window_mean(g, *before_window(g["spy_start"]))
        y = window_mean(g, *do_window(g["spy_start"]))
        if x is None or y is None:
            skipped.append(g["game_id"])
            continue
        arm = arm_of(g)
        points.append({"game_id": g["game_id"], "family": g["family"], "condition": g["condition"],
                       "condition_name": CONDITION_NAMES[g["condition"]], "arm": arm, "seed": g["seed"],
                       "say": game_say(g), "x": x, "y": y, "nash": g["nash_price"], "deal": g["deal_price"],
                       "exploratory": bool(exploratory), "mock": g.get("mock") is not False, "source": source})
    order = {c: i for i, c in enumerate(CONDITIONS)}
    points.sort(key=lambda p: (p["family"], p["exploratory"], order.get(_base(p["arm"]), 99), p["arm"],
                               str(p["seed"]), p["game_id"]))
    return points, skipped


def jitter(points, seed=JITTER_SEED, scale=JITTER):
    """New point dicts with xj, yj: a uniform offset seeded by (seed, game id), so the order does not matter."""
    out = []
    for p in points:
        rng = random.Random(f"{seed}|{p['game_id']}|{int(p['exploratory'])}")
        out.append({**p, "xj": p["x"] + rng.uniform(-scale, scale), "yj": p["y"] + rng.uniform(-scale, scale)})
    return out


def _window_text(refs, fam):
    s = refs[fam]["spy_start"]
    if isinstance(s, tuple):
        return "the 3 rounds before the offer", "the do window"
    b0, b1 = before_window(s)
    d0, d1 = do_window(s)
    return f"rounds {b0} to {b1}", f"rounds {d0} to {d1}"


def make_figure(points, out_pdf, out_png, mock=False, refs=None):
    """Points need xj, yj (see jitter). Returns {labels, panels, mock_stamp}: legend labels use full
    condition names, never a bare condition letter."""
    from matplotlib.lines import Line2D
    plt = _plt()
    fams = sorted({p["family"] for p in points})
    refs = refs or {f: {"nash": next(p["nash"] for p in points if p["family"] == f),
                        "deal": next(p["deal"] for p in points if p["family"] == f),
                        "spy_start": None} for f in fams}
    n = max(len(fams), 1)
    fig, axes = plt.subplots(1, n, figsize=(max(0.6 + 3.5 * n, 7.6), 4.6), squeeze=False)
    handles, labels = [], []

    def add(handle, label):
        if label not in labels:
            labels.append(label)
            handles.append(handle)

    for ax, fam in zip(axes[0], fams):
        pts = [p for p in points if p["family"] == fam]
        nash, deal = refs[fam]["nash"], refs[fam]["deal"]
        vals = [p["xj"] for p in pts] + [p["yj"] for p in pts] + [nash, deal]
        lo, hi = min(vals), max(vals)
        pad = 0.06 * (hi - lo or 1.0)
        lo, hi = lo - pad, hi + pad
        diag, = ax.plot([lo, hi], [lo, hi], color="#c4c4bd", linewidth=0.9, zorder=1)
        add(diag, "y = x (no change)")
        nash_l = ax.axvline(nash, color=REF_COLOR, linewidth=0.9, linestyle="--", zorder=1)
        ax.axhline(nash, color=REF_COLOR, linewidth=0.9, linestyle="--", zorder=1)
        add(nash_l, f"Nash price ({nash:.2f})")
        deal_l = ax.axvline(deal, color=DEAL_COLOR, linewidth=0.9, linestyle="--", zorder=1)
        ax.axhline(deal, color=DEAL_COLOR, linewidth=0.9, linestyle="--", zorder=1)
        add(deal_l, f"Deal price = joint monopoly ({deal:.2f})")
        for p in pts:
            c = SAY_COLORS[p["say"]]
            ax.plot([p["xj"]], [p["yj"]], linestyle="none", marker=MARKERS[_base(p["arm"])], markersize=6.5,
                    markeredgecolor=c, markerfacecolor="white" if p["exploratory"] else c,
                    markeredgewidth=1.3 if p["exploratory"] else 0.6, alpha=0.9, zorder=3)
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.set_aspect("equal", adjustable="box")
        bw, dw = _window_text(refs, fam) if refs[fam].get("spy_start") is not None else ("before", "after")
        ax.set_xlabel(f"Mean price before the offer ({bw})", fontsize=7)
        ax.set_ylabel(f'Mean price in the "do" window ({dw})', fontsize=7)
        ax.set_title(f"Family {fam} ({len(pts)} game{'s' if len(pts) != 1 else ''})", fontsize=8)
        ax.tick_params(labelsize=6.5)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        if mock:
            ax.text(0.5, 0.5, "MOCK", transform=ax.transAxes, ha="center", va="center", fontsize=40,
                    color="#b42318", alpha=0.18, rotation=30, zorder=5)
    present_says = {p["say"] for p in points}
    for say in SAYS:
        if say in present_says:
            add(Line2D([], [], linestyle="none", marker="o", markersize=6, color=SAY_COLORS[say]), SAY_LABELS[say])
    order = {c: i for i, c in enumerate(CONDITIONS)}
    arms = sorted({p["arm"] for p in points}, key=lambda a: (order.get(_base(a), 99), a))
    for arm in arms:
        add(Line2D([], [], linestyle="none", marker=MARKERS[_base(arm)], markersize=6, color="#55554f",
                   markerfacecolor="#55554f"), arm_label(arm))
    if any(p["exploratory"] for p in points):
        add(Line2D([], [], linestyle="none", marker="o", markersize=6, color="#55554f", markerfacecolor="white",
                   markeredgewidth=1.3), EXPLORATORY_LABEL)
    ncol = 4 if n > 1 else 3
    legend_h = (0.4 + 0.15 * ((len(labels) + ncol - 1) // ncol)) / fig.get_figheight()
    fig.legend(handles, labels, loc="lower center", ncol=ncol, fontsize=6, frameon=False, bbox_to_anchor=(0.5, 0.03))
    fig.text(0.01, 0.005, f"One point per game, mean of both firms. Seeded jitter of up to {JITTER} price units "
             "for legibility only (exact values in the CSV).", fontsize=5.5, color="#55554f")
    if mock:
        fig.suptitle(MOCK_NOTE, fontsize=8, color="#b42318")
    fig.tight_layout(rect=(0, legend_h, 1, 1))
    for path in (out_pdf, out_png):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_pdf, format="pdf", metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(out_png, format="png", dpi=200, metadata={"Software": None})
    plt.close(fig)
    return {"labels": labels, "panels": fams, "mock_stamp": bool(mock)}


def write_csv(points, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, lineterminator="\n")
        w.writeheader()
        for p in points:
            w.writerow({"game_id": p["game_id"], "family": p["family"], "condition": p["condition"],
                        "condition_name": p["condition_name"], "arm": p["arm"], "seed": p["seed"], "say": p["say"],
                        "before_mean": repr(p["x"]), "do_mean": repr(p["y"]), "x_plotted": repr(p["xj"]),
                        "y_plotted": repr(p["yj"]), "nash": repr(p["nash"]), "deal": repr(p["deal"]),
                        "exploratory": int(p["exploratory"]), "mock": int(p["mock"]), "source": p["source"]})


def load_points(runs_dirs, exploratory_dirs=(), include_mock=False, all_configs=False):
    logs, points, skipped = [], [], []
    for dirs, expl in ((runs_dirs, False), (exploratory_dirs or (), True)):
        for d in dirs:
            configs = None if (all_configs or expl) else PREREG_CONFIGS
            kept, _ = filter_logs(load_logs(d), configs, include_mock)
            pts, skip = game_points(kept, exploratory=expl, source=str(d))
            logs += kept
            points += pts
            skipped += skip
    ids = [g["game_id"] for g in logs]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise SystemExit(f"the same game id appears in several runs folders: {dup[:3]}")
    return logs, points, skipped


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("runs_dirs", nargs="+")
    ap.add_argument("--exploratory", action="append", default=[], metavar="DIR",
                    help="runs folder of an exploratory arm (hollow markers); repeatable")
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    ap.add_argument("--include-mock", action="store_true")
    ap.add_argument("--all-configs", action="store_true")
    ap.add_argument("--seed", type=int, default=JITTER_SEED, help="jitter seed")
    a = ap.parse_args(argv)
    logs, points, skipped = load_points(a.runs_dirs, a.exploratory, a.include_mock, a.all_configs)
    if not points:
        raise SystemExit("no games to plot (real games only by default, see --include-mock and --all-configs)")
    points = jitter(points, seed=a.seed)
    out = Path(a.out_dir)
    mock = any(p["mock"] for p in points)
    make_figure(points, out / "before_after.pdf", out / "before_after.png", mock=mock, refs=reference_lines(logs))
    write_csv(points, out / "before_after.csv")
    for name in ("before_after.pdf", "before_after.png", "before_after.csv"):
        print(f"wrote {out / name}")
    if skipped:
        print(f"skipped {len(skipped)} game(s) with an incomplete window: {', '.join(skipped)}")


if __name__ == "__main__":
    main()
