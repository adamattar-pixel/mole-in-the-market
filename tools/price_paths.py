"""Report figure: price paths per model family, plus the page 1 excerpt of one game.

Descriptive, from the logs only (no API key, no network). For each family and condition: the mean price
per round (both firms, then across seeds), with a min to max band over seeds, the Nash and deal (joint
monopoly) prices, the spy round and the 3-round "do" window (PREREGISTRATION.md). The optional memory arm
(docs/team-artem/MEMORY_ARM.md) is EXPLORATORY and drawn dashed, labelled as such.

Usage:
  python -m tools.price_paths runs [--out-dir figures/exploratory] [--memory-runs runs_exploratory/memory]
                              [--game-id ID] [--include-mock] [--all-configs]

Writes price_paths.pdf, and excerpt.md when --game-id is given (also printed). Like tools/reproduce.py,
the default keeps only real games (mock false) from the preregistered configs; --include-mock and
--all-configs are for dry runs and diagnostics.
"""
import sys
from pathlib import Path as _BootPath
if __name__ == "__main__" and __package__ in (None, ""):
    sys.path.insert(0, str(_BootPath(__file__).resolve().parent.parent))

import argparse
from pathlib import Path

from harness.conditions import CONDITIONS, load_prereg_texts
from harness.runlog import load_logs
from harness.vizexport import CONDITION_NAMES
from tools.reproduce import PREREG_CONFIGS, filter_logs

DEFAULT_OUT_DIR = "figures/exploratory"
MEMORY_CONFIGS = ("espion_mem",)
MEMORY_SUFFIX = "_mem"

# Categorical slots in fixed condition order (validated palette, see docs/team-artem/PRICE_PATHS.md).
COLORS = {"A": "#2a78d6", "E": "#eb6834", "B": "#1baf7a", "B_T": "#eda100", "C": "#e87ba4", "D": "#008300"}
MARKERS = {"A": "o", "E": "s", "B": "^", "B_T": "v", "C": "D", "D": "P"}


def arm_of(log):
    return log["condition"] + (MEMORY_SUFFIX if log.get("memory") else "")


def _base(arm):
    return arm[:-len(MEMORY_SUFFIX)] if arm.endswith(MEMORY_SUFFIX) else arm


def arm_label(arm):
    name = CONDITION_NAMES[_base(arm)]
    return f"{name} (memory arm, exploratory)" if arm.endswith(MEMORY_SUFFIX) else name


def ordered_arms(family_paths):
    order = list(CONDITIONS) + [c + MEMORY_SUFFIX for c in CONDITIONS]
    return [a for a in order if a in family_paths]


def do_window(spy_start):
    w = int(load_prereg_texts()["behavioral_window"])
    return spy_start + 1, spy_start + w


def _game_means(log):
    return {r["round"]: (r["firms"]["0"]["price"] + r["firms"]["1"]["price"]) / 2 for r in log["rounds"]}


def price_paths(logs):
    """{family: {arm: {round, mean, lo, hi, n}}}: per round, the mean over games of the two-firm mean."""
    grouped = {}
    for g in logs:
        grouped.setdefault(g["family"], {}).setdefault(arm_of(g), []).append(_game_means(g))
    out = {}
    for fam in sorted(grouped):
        out[fam] = {}
        for arm, games in grouped[fam].items():
            rounds = sorted({r for gm in games for r in gm})
            vals = [[gm[r] for gm in games if r in gm] for r in rounds]
            out[fam][arm] = {"round": rounds, "mean": [sum(v) / len(v) for v in vals],
                             "lo": [min(v) for v in vals], "hi": [max(v) for v in vals],
                             "n": [len(v) for v in vals]}
    return out


def reference_lines(logs):
    """{family: {nash, monopoly, deal, spy_start}}. Prices must agree inside a family. spy_start is one int
    (the frozen design); a family mixing spy rounds (never in the frozen configs) gets a sorted tuple and
    each spy round and do window is drawn."""
    refs, spy = {}, {}
    for g in logs:
        ref = {"nash": g["nash_price"], "monopoly": g["monopoly_price"], "deal": g["deal_price"]}
        if refs.setdefault(g["family"], ref) != ref:
            raise ValueError(f"games of family {g['family']} disagree on Nash, monopoly or deal price")
        spy.setdefault(g["family"], set()).add(g["spy_start"])
    for fam, starts in spy.items():
        refs[fam]["spy_start"] = next(iter(starts)) if len(starts) == 1 else tuple(sorted(starts))
    return refs


def _spy_starts(ref):
    s = ref["spy_start"]
    return list(s) if isinstance(s, tuple) else [s]


LAYOUTS = ("grid", "overlay")
REF_COLOR = "#8a8a82"
N_BOOT = 2000
BOOT_SEED = 0


def grid_columns(paths):
    """Condition columns of the small multiples: every non-reference arm present in any family, in order.
    No spy (A, A_mem) is the reference drawn in every panel, never a column."""
    present = {a for fam in paths.values() for a in fam}
    cols = [a for a in list(CONDITIONS) + [c + MEMORY_SUFFIX for c in CONDITIONS]
            if a in present and _base(a) != "A"]
    return cols or [a for a in ("A", "A" + MEMORY_SUFFIX) if a in present]


def reference_arm(arm, family_arms):
    """No spy run with the same prompt (A_mem for a memory arm when present), else the frozen No spy."""
    if arm.endswith(MEMORY_SUFFIX) and "A" + MEMORY_SUFFIX in family_arms:
        return "A" + MEMORY_SUFFIX
    return "A" if "A" in family_arms else None


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _draw_refs(ax, ref):
    for start in _spy_starts(ref):
        lo_w, hi_w = do_window(start)
        ax.axvspan(lo_w - 0.5, hi_w + 0.5, color="#d9d9d4", alpha=0.6, linewidth=0, zorder=0,
                   label=f'"Do" window (rounds {lo_w} to {hi_w})')
        ax.axvline(start, color="#55554f", linewidth=1, linestyle=":", zorder=1,
                   label=f"Spy message (round {start})")
    ax.axhline(ref["deal"], color="#1f1f1d", linewidth=1, linestyle="--", zorder=1,
               label=f"Deal price = joint monopoly ({ref['deal']:.2f})")
    ax.axhline(ref["nash"], color=REF_COLOR, linewidth=1, linestyle="--", zorder=1,
               label=f"Nash price ({ref['nash']:.2f})")


def _style(ax):
    from matplotlib.ticker import MaxNLocator
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.tick_params(labelsize=6)
    ax.grid(axis="y", color="#ececea", linewidth=0.5)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def _plot_arm(ax, p, arm, color=None, thin=False):
    base = _base(arm)
    mem = arm != base
    color = color or COLORS[base]
    ax.fill_between(p["round"], p["lo"], p["hi"], color=color, alpha=0.05 if mem else (0.12 if thin else 0.15),
                    linewidth=0, zorder=2)
    ax.plot(p["round"], p["mean"], color=color, linewidth=1.0 if thin else 1.6,
            linestyle="--" if mem else "-", marker=None if thin else MARKERS[base], markersize=3.5,
            markerfacecolor="white" if mem else color, zorder=3, label=arm_label(arm))


def _collect(ax, labels, handles):
    for h, lab in zip(*ax.get_legend_handles_labels()):
        if lab not in labels:
            labels.append(lab)
            handles.append(h)


def _save(fig, out_pdf):
    Path(out_pdf).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_pdf, format="pdf", metadata={"CreationDate": None, "ModDate": None})


def make_price_paths(paths, refs, out_pdf, note=None, layout="grid"):
    """layout "grid" (default): small multiples, rows = family, columns = condition, No spy as a thin grey
    reference in every panel. layout "overlay": one panel per family with every condition.
    Returns the legend labels and panel titles (full names, never a bare condition letter)."""
    if layout not in LAYOUTS:
        raise ValueError(f"unknown layout {layout!r}, expected one of {LAYOUTS}")
    plt = _plt()
    fams = list(paths)
    labels, handles, titles = [], [], []
    if layout == "overlay":
        fig, axes = plt.subplots(1, max(len(fams), 1), figsize=(4.2 * max(len(fams), 1) + 0.4, 3.9),
                                 sharey=True, squeeze=False)
        for ax, fam in zip(axes[0], fams):
            _draw_refs(ax, refs[fam])
            for arm in ordered_arms(paths[fam]):
                _plot_arm(ax, paths[fam][arm], arm)
            n_seeds = max(max(p["n"]) for p in paths[fam].values())
            ax.set_title(f"Family {fam} (up to {n_seeds} seeds per condition)", fontsize=8)
            ax.set_xlabel("Round", fontsize=7)
            _style(ax)
            _collect(ax, labels, handles)
        axes[0][0].set_ylabel("Mean price, both firms (band: min to max over seeds)", fontsize=7)
        ncol, legend_h = 3, 0.06 + 0.035 * ((len(labels) + 2) // 3)
    else:
        cols = grid_columns(paths)
        fig, axes = plt.subplots(max(len(fams), 1), len(cols), figsize=(0.4 + 2.15 * len(cols),
                                 0.9 + 2.0 * max(len(fams), 1)), sharey=True, sharex=True, squeeze=False)
        for i, fam in enumerate(fams):
            for j, arm in enumerate(cols):
                ax = axes[i][j]
                _draw_refs(ax, refs[fam])
                ref_arm = reference_arm(arm, paths[fam]) if _base(arm) != "A" else None
                if ref_arm is not None:
                    _plot_arm(ax, paths[fam][ref_arm], ref_arm, color=REF_COLOR, thin=True)
                if arm in paths[fam]:
                    _plot_arm(ax, paths[fam][arm], arm)
                    n = max(paths[fam][arm]["n"])
                    title = f"{arm_label(arm)}\nfamily {fam}, {n} seed{'s' if n != 1 else ''}"
                else:
                    ax.text(0.5, 0.5, "not run", transform=ax.transAxes, ha="center", va="center",
                            fontsize=7, color="#55554f")
                    title = f"{arm_label(arm)}\nfamily {fam}"
                ax.set_title(title, fontsize=6.5)
                if i == len(fams) - 1:
                    ax.set_xlabel("Round", fontsize=6.5)
                if j == 0:
                    ax.set_ylabel("Mean price, both firms", fontsize=6.5)
                _style(ax)
                _collect(ax, labels, handles)
                if arm_label(arm) not in titles:
                    titles.append(arm_label(arm))
        ncol = 4
        legend_h = (0.2 + 0.13 * ((len(labels) + ncol - 1) // ncol)) / fig.get_figheight()
        fig.legend(handles, labels, loc="lower center", ncol=ncol, fontsize=6, frameon=False,
                   bbox_to_anchor=(0.5, 0.0))
        fig.text(0.01, 0.005, "Bands: min to max over seeds. Grey: No spy, same rounds.", fontsize=5.5,
                 color="#55554f")
    if layout == "overlay" and labels:
        fig.legend(handles, labels, loc="lower center", ncol=ncol, fontsize=6, frameon=False,
                   bbox_to_anchor=(0.5, 0.0))
    if note:
        fig.suptitle(note, fontsize=8, color="#b42318")
    fig.tight_layout(rect=(0, legend_h, 1, 1))
    _save(fig, out_pdf)
    plt.close(fig)
    return labels + [t for t in titles if t not in labels]


def window_mean(log, first, last):
    """Mean price of both firms over rounds first..last, or None if a round is missing."""
    by_round = {r["round"]: r for r in log["rounds"]}
    if any(t not in by_round for t in range(first, last + 1)):
        return None
    vals = [(by_round[t]["firms"]["0"]["price"] + by_round[t]["firms"]["1"]["price"]) / 2
            for t in range(first, last + 1)]
    return sum(vals) / len(vals)


def _quantile(sorted_vals, q):
    """Linear interpolation between order statistics (numpy's default rule)."""
    pos = q * (len(sorted_vals) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def price_shift(logs, n_boot=N_BOOT, seed=BOOT_SEED):
    """EXPLORATORY. Per family and condition: mean do-window price minus the No spy mean over the same rounds,
    with a percentile bootstrap 95% interval (games resampled with replacement in each group, seeded).
    {family: {arm: {shift, lo, hi, n, n_ref, ref}}}. Games whose window is incomplete are left out."""
    import random
    refs = reference_lines(logs)
    out = {}
    for fam in sorted(refs):
        if isinstance(refs[fam]["spy_start"], tuple):
            raise ValueError(f"family {fam} mixes spy rounds: no common do window")
        first, last = do_window(refs[fam]["spy_start"])
        groups = {}
        for g in logs:
            if g["family"] == fam:
                m = window_mean(g, first, last)
                if m is not None:
                    groups.setdefault(arm_of(g), []).append(m)
        out[fam] = {}
        for arm in ordered_arms(groups):
            ref_arm = reference_arm(arm, groups) if _base(arm) != "A" else None
            if ref_arm is None:
                continue
            x, r = groups[arm], groups[ref_arm]
            rng = random.Random(f"{seed}|{fam}|{arm}")
            draws = sorted(sum(rng.choice(x) for _ in x) / len(x) - sum(rng.choice(r) for _ in r) / len(r)
                           for _ in range(n_boot))
            out[fam][arm] = {"shift": sum(x) / len(x) - sum(r) / len(r), "lo": _quantile(draws, 0.025),
                             "hi": _quantile(draws, 0.975), "n": len(x), "n_ref": len(r), "ref": ref_arm}
    return out


def make_price_shift(shift, out_pdf, note=None, refs=None):
    """Dot and whisker per family: do-window shift vs No spy, bootstrap 95% interval. Returns row labels."""
    plt = _plt()
    fams = list(shift)
    rows = [a for a in list(CONDITIONS) + [c + MEMORY_SUFFIX for c in CONDITIONS]
            if any(a in shift[f] for f in fams)]
    fig, axes = plt.subplots(1, max(len(fams), 1), figsize=(0.9 + 2.9 * max(len(fams), 1),
                             0.9 + 0.32 * max(len(rows), 1)), sharey=True, sharex=True, squeeze=False)
    labels = [arm_label(a) for a in rows]
    for ax, fam in zip(axes[0], fams):
        ax.axvline(0, color=REF_COLOR, linewidth=0.8, zorder=1)
        for i, arm in enumerate(rows):
            y = len(rows) - 1 - i
            e = shift[fam].get(arm)
            if e is None:
                ax.text(0, y, "not run", fontsize=5.5, color="#55554f", va="center", ha="center")
                continue
            base = _base(arm)
            ax.plot([e["lo"], e["hi"]], [y, y], color=COLORS[base], linewidth=1.6, zorder=2,
                    solid_capstyle="round")
            ax.plot([e["shift"]], [y], marker=MARKERS[base], markersize=5, color=COLORS[base],
                    markerfacecolor="white" if arm != base else COLORS[base], zorder=3)
        title = f"Family {fam}"
        if refs and fam in refs:
            title += f" (deal minus Nash = {refs[fam]['deal'] - refs[fam]['nash']:.2f})"
        ax.set_title(title, fontsize=7)
        ax.set_xlabel("Do-window price minus No spy (price units)", fontsize=6.5)
        ax.tick_params(labelsize=6)
        ax.grid(axis="x", color="#ececea", linewidth=0.5)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    axes[0][0].set_yticks(range(len(rows) - 1, -1, -1))
    axes[0][0].set_yticklabels(labels, fontsize=6.5)
    axes[0][0].set_ylim(-0.6, len(rows) - 0.4)
    fig.text(0.01, 0.005, "EXPLORATORY. Dot: mean shift; whisker: 95% bootstrap interval over games (seeded). "
             "Memory arms compared with the memory No spy when run.", fontsize=5, color="#55554f")
    if note:
        fig.suptitle(note, fontsize=8, color="#b42318")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    _save(fig, out_pdf)
    plt.close(fig)
    return labels


def find_game(logs, game_id):
    for g in logs:
        if g["game_id"] == game_id:
            return g
    raise KeyError(f"no game with id {game_id!r}")


def _fence(text):
    run = longest = 0
    for ch in text:
        run = run + 1 if ch == "`" else 0
        longest = max(longest, run)
    return "`" * max(3, longest + 1)


def excerpt_md(log):
    """Spy message, both replies in the spy round (verbatim) and prices for spy_start-1 .. spy_start+3."""
    texts = load_prereg_texts()
    s = log["spy_start"]
    lo_w, hi_w = do_window(s)
    tol = texts["behavioral_gap_fraction"] * (log["monopoly_price"] - log["nash_price"])
    by_round = {r["round"]: r for r in log["rounds"]}
    name = arm_label(arm_of(log))
    lines = [f"# Excerpt: game {log['game_id']}", "",
             f"Condition: {name} | family {log['family']} | seed {log['seed']}"
             + (" | MOCK GAME (dry run): not a result" if log.get("mock") is not False else ""), "",
             f"Deal price (joint monopoly): {log['deal_price']:.3f} | Nash price: {log['nash_price']:.3f} | "
             f"do tolerance: +/- {tol:.3f}", "",
             f"## Spy message (round {s}, same text to both firms)", ""]
    msg = log.get("message")
    lines += ["(no message)" if msg is None else f"> {msg}", ""]
    spy_round = by_round.get(s)
    for f in ("0", "1"):
        lines += [f"## Firm {f} reply in round {s} (verbatim)", ""]
        reply = None if spy_round is None else spy_round["firms"][f].get("reply")
        if reply is None:
            lines += ["(not logged)", ""]
        else:
            fence = _fence(reply)
            lines += [fence, reply, fence, ""]
    lines += ["## Prices", "",
              "| Round | Firm 0 price | Firm 1 price | Firm 0 reply field | Firm 1 reply field | Note |",
              "|---|---|---|---|---|---|"]
    for t in range(s - 1, hi_w + 1):
        if t not in by_round:
            continue
        f0, f1 = by_round[t]["firms"]["0"], by_round[t]["firms"]["1"]
        note = "before the spy message" if t < s else "spy message" if t == s else "do window"
        lines.append(f"| {t} | {f0['price']:.3f} | {f1['price']:.3f} | {f0['response_to_message']} | "
                     f"{f1['response_to_message']} | {note} |")
    lines += ["", f"Generated by tools/price_paths.py from the game log (do window: rounds {lo_w} to {hi_w})."]
    return "\n".join(lines) + "\n"


def load_arms(runs_dir, memory_dir, include_mock=False, all_configs=False):
    main_logs, _ = filter_logs(load_logs(runs_dir), None if all_configs else PREREG_CONFIGS, include_mock)
    if any(g.get("memory") for g in main_logs):
        raise ValueError("main runs folder holds memory arm logs: pass them with --memory-runs")
    if memory_dir is None:
        return main_logs
    mem_logs, _ = filter_logs(load_logs(memory_dir), None if all_configs else MEMORY_CONFIGS, include_mock)
    if not all(g.get("memory") for g in mem_logs):
        raise ValueError("memory runs folder holds logs without memory: true")
    return main_logs + mem_logs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("runs_dir", help="folder of game logs (*.json)")
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help="folder for price_paths.pdf and excerpt.md")
    ap.add_argument("--memory-runs", default=None, help="exploratory memory-arm logs, drawn dashed")
    ap.add_argument("--game-id", default=None, help="also write excerpt.md for this game id")
    ap.add_argument("--include-mock", action="store_true", help="keep mock (dry run) games")
    ap.add_argument("--all-configs", action="store_true", help="keep every config, including smoke and O1")
    ap.add_argument("--layout", choices=LAYOUTS, default="grid", help="figure layout: grid (one panel per cell) or overlay")
    a = ap.parse_args(argv)
    logs = load_arms(a.runs_dir, a.memory_runs, a.include_mock, a.all_configs)
    out = Path(a.out_dir)
    if not logs:
        raise SystemExit("no games to plot (real games only by default, see --include-mock and --all-configs)")
    note = "MOCK GAMES (dry run): not a result" if any(g.get("mock") is not False for g in logs) else None
    refs = reference_lines(logs)
    make_price_paths(price_paths(logs), refs, out / "price_paths.pdf", note, layout=a.layout)
    print(f"wrote {out / 'price_paths.pdf'}")
    try:
        shift = price_shift(logs)
    except ValueError as exc:
        print(f"price_shift.pdf not written: {exc}")
    else:
        make_price_shift(shift, out / "price_shift.pdf", note, refs=refs)
        print(f"wrote {out / 'price_shift.pdf'}")
    if a.game_id:
        md = excerpt_md(find_game(logs, a.game_id))
        (out / "excerpt.md").write_text(md, encoding="utf-8")
        print(md, end="")


if __name__ == "__main__":
    main()
