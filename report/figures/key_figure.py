"""Key figure: price before vs after the offer, per game, Llama (core) and Claude (exploratory).

Reads figures/exploratory/before_after.csv (written by tools/before_after.py). No API call.
Run from the repo root: python3 report/figures/key_figure.py
"""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC = "figures/exploratory/before_after.csv"
OUT = "report/figures/key_figure"
COLORS = {"accept": "#D55E00", "decline": "#0072B2", "none": "#7F7F7F"}
SAY_LABEL = {"accept": 'Said "accept"', "decline": 'Said "decline"', "none": "No offer sent"}

rows = list(csv.DictReader(open(SRC)))
nash, deal = float(rows[0]["nash"]), float(rows[0]["deal"])

LLAMA = [("A", "No spy\n(baseline)"), ("E", "Deal\nallowed\n(positive\ncontrol)"), ("B", "Direct\noffer"),
         ("B_T", "Trusted\ndirect\noffer"), ("C", "Hint"), ("D", "Harmless\nrequest")]
CLAUDE = [("anthropic", "A", "Haiku\nNo spy"), ("anthropic", "E", "Haiku\nDeal\nallowed"),
          ("anthropic-fb", "A", "Sonnet\nNo spy"), ("anthropic-fb", "E", "Sonnet\nDeal\nallowed")]

plt.rcParams.update({"font.size": 8, "font.family": "DejaVu Sans", "svg.hashsalt": "key",
                     "axes.spines.top": False, "axes.spines.right": False})
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.4), sharey=True,
                               gridspec_kw={"width_ratios": [6, 4.4], "wspace": 0.06})


def draw(ax, groups, title):
    for i, (games, label) in enumerate(groups):
        games = sorted(games, key=lambda r: int(r["seed"]))
        n = len(games)
        for j, g in enumerate(games):
            x = i + (j - (n - 1) / 2) * 0.13
            b, a, c = float(g["before_mean"]), float(g["do_mean"]), COLORS[g["say"]]
            if abs(a - b) > 0.02:
                ax.annotate("", xy=(x, a), xytext=(x, b),
                            arrowprops=dict(arrowstyle="-|>", color=c, lw=0.9, mutation_scale=7, shrinkA=2, shrinkB=2))
            ax.plot(x, b, "o", mfc="white", mec=c, ms=4.5, mew=1.0, zorder=3)
            ax.plot(x, a, "o", color=c, ms=4.5, zorder=4)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([g[1] for g in groups], fontsize=7.5, linespacing=1.05)
    ax.set_xlim(-0.55, len(groups) - 0.45)
    for y, ls in ((nash, ":"), (deal, "--")):
        ax.axhline(y, color="black", ls=ls, lw=0.8, zorder=1)
    ax.set_title(title, fontsize=8.5)


draw(ax1, [([r for r in rows if r["family"] == "meta-llama" and r["condition"] == c], l) for c, l in LLAMA],
     "Llama 3.3 70B (preregistered core)\n30 games, 5 per condition")
draw(ax2, [([r for r in rows if r["family"] == f and r["condition"] == c], l) for f, c, l in CLAUDE],
     "Claude (exploratory, not scored)\n10 Haiku 4.5 + 8 Sonnet 4.5 games")
ax2.set_facecolor("#EFEFEF")
ax2.title.set_color("#555555")
ax1.set_ylabel("Mean price per game (both firms)")
ax1.set_ylim(1.38, 2.72)
ax2.text(3.55, deal + 0.015, "deal 1.92", ha="right", va="bottom", fontsize=7)
ax2.text(3.55, nash + 0.015, "Nash 1.47", ha="right", va="bottom", fontsize=7)

h = [plt.Line2D([], [], marker="o", ls="", color=COLORS[k], ms=5, label=SAY_LABEL[k]) for k in ("accept", "decline", "none")]
h += [plt.Line2D([], [], marker="o", ls="", mfc="white", mec="black", ms=5, label="Before offer (rounds 5-7)"),
      plt.Line2D([], [], marker="o", ls="", color="black", ms=5, label="After offer (rounds 9-11)")]
fig.legend(handles=h, loc="lower center", ncol=5, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, -0.01),
           handletextpad=0.3, columnspacing=1.2)
fig.subplots_adjust(left=0.08, right=0.99, top=0.88, bottom=0.30)
fig.savefig(OUT + ".png", dpi=300, metadata={"Software": None})
fig.savefig(OUT + ".pdf", metadata={"CreationDate": None, "Producer": None, "Creator": None})
