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


def make_price_paths(paths, refs, out_pdf, note=None):
    """One panel per family. Returns the legend labels (full names, never a bare condition letter)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator

    fams = list(paths)
    fig, axes = plt.subplots(1, max(len(fams), 1), figsize=(4.2 * max(len(fams), 1) + 0.4, 3.9),
                             sharey=True, squeeze=False)
    labels, handles = [], []
    for ax, fam in zip(axes[0], fams):
        ref = refs[fam]
        for start in _spy_starts(ref):
            lo_w, hi_w = do_window(start)
            ax.axvspan(lo_w - 0.5, hi_w + 0.5, color="#d9d9d4", alpha=0.6, linewidth=0, zorder=0,
                       label=f'"Do" window (rounds {lo_w} to {hi_w})')
            ax.axvline(start, color="#55554f", linewidth=1, linestyle=":", zorder=1,
                       label=f"Spy message (round {start})")
        ax.axhline(ref["deal"], color="#1f1f1d", linewidth=1, linestyle="--", zorder=1,
                   label=f"Deal price = joint monopoly ({ref['deal']:.2f})")
        ax.axhline(ref["nash"], color="#8a8a82", linewidth=1, linestyle="--", zorder=1,
                   label=f"Nash price ({ref['nash']:.2f})")
        for arm in ordered_arms(paths[fam]):
            p, base = paths[fam][arm], _base(arm)
            mem = arm != base
            ax.fill_between(p["round"], p["lo"], p["hi"], color=COLORS[base], alpha=0.05 if mem else 0.10,
                            linewidth=0, zorder=2)
            ax.plot(p["round"], p["mean"], color=COLORS[base], linewidth=1.6, linestyle="--" if mem else "-",
                    marker=MARKERS[base], markersize=3.5, markerfacecolor="white" if mem else COLORS[base],
                    zorder=3, label=arm_label(arm))
        n_seeds = max(max(p["n"]) for p in paths[fam].values())
        ax.set_title(f"Family {fam} (up to {n_seeds} seeds per condition)", fontsize=8)
        ax.set_xlabel("Round", fontsize=7)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.tick_params(labelsize=6)
        ax.grid(axis="y", color="#ececea", linewidth=0.5)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for h, lab in zip(*ax.get_legend_handles_labels()):
            if lab not in labels:
                labels.append(lab)
                handles.append(h)
    axes[0][0].set_ylabel("Mean price, both firms (band: min to max over seeds)", fontsize=7)
    if labels:
        fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=6, frameon=False,
                   bbox_to_anchor=(0.5, 0.0))
    if note:
        fig.suptitle(note, fontsize=8, color="#b42318")
    fig.tight_layout(rect=(0, 0.06 + 0.035 * ((len(labels) + 2) // 3), 1, 1))
    Path(out_pdf).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_pdf, format="pdf", metadata={"CreationDate": None, "ModDate": None})
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
    ap.add_argument("runs_dir")
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    ap.add_argument("--memory-runs", default=None)
    ap.add_argument("--game-id", default=None)
    ap.add_argument("--include-mock", action="store_true")
    ap.add_argument("--all-configs", action="store_true")
    a = ap.parse_args(argv)
    logs = load_arms(a.runs_dir, a.memory_runs, a.include_mock, a.all_configs)
    out = Path(a.out_dir)
    if not logs:
        raise SystemExit("no games to plot (real games only by default, see --include-mock and --all-configs)")
    note = "MOCK GAMES (dry run): not a result" if any(g.get("mock") is not False for g in logs) else None
    make_price_paths(price_paths(logs), reference_lines(logs), out / "price_paths.pdf", note)
    print(f"wrote {out / 'price_paths.pdf'}")
    if a.game_id:
        md = excerpt_md(find_game(logs, a.game_id))
        (out / "excerpt.md").write_text(md, encoding="utf-8")
        print(md, end="")


if __name__ == "__main__":
    main()
