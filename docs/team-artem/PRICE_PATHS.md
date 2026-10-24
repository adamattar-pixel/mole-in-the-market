# Price paths figure and page 1 excerpt (report material)

`tools/price_paths.py` builds two report items from the game logs only. It uses no API key, no network and no model call.

- `price_paths.pdf`: suggested Figure 2 (NOVELTY_AND_JUDGES.md, Presentation).
- `price_shift.pdf`: a compact EXPLORATORY summary of whether the offer moved prices.
- `excerpt.md`: the real excerpt for page 1.

## How to run

```
# preregistered games (real games from espion_pilot / espion_core only, same filter as tools/reproduce.py)
python3 -m tools.price_paths runs --out-dir figures/exploratory

# with the memory arm (EXPLORATORY) and a page 1 excerpt
python3 -m tools.price_paths runs --memory-runs runs_exploratory/memory \
    --game-id espion_core__<family>__B__s1 --out-dir figures/exploratory

# dry / mock runs (diagnostics only; the figure and the excerpt are stamped "MOCK ... not a result")
python3 -m tools.run configs/espion_dry.yaml --out-dir /tmp/dry
python3 -m tools.price_paths /tmp/dry --include-mock --all-configs --game-id espion_dry__mock-a__B__s1 --out-dir /tmp/figs
```

`--layout overlay` gives the older layout: one panel per family with every condition. It is hard to read with more than 4 lines. The default output folder is `figures/exploratory/`. The excerpt is also printed to stdout. Running it twice gives byte-identical files: the PDF has no creation or modification date, and there is no randomness.

## What the figure shows

- The default layout is small multiples. Each row is a model family (families are never pooled). Each column is a condition: Deal allowed (control), Direct offer, Trusted direct offer, Hint, Harmless request, then any memory arm conditions passed. The y axis is shared.
- Every panel shows "No spy" as a thin grey reference line with its band. For a memory arm panel, the reference is the memory arm No spy when it was run, else the frozen No spy (dashed grey).
- The panel's condition is drawn in its own color with its band. Panel titles give the full condition name, the family and the number of seeds. A family that did not run a condition shows "not run".
- Each line is one condition, labelled with its full name ("No spy", "Deal allowed (control)", "Direct offer", "Trusted direct offer", "Hint", "Harmless request"), never a bare letter. A memory arm run is drawn dashed with hollow markers and labelled "(memory arm, exploratory)".
- Line: for each round, take the mean of the two firms' prices in each game, then the mean over the games (seeds) of that condition.
- Band: the minimum to maximum of that per-game mean over seeds. It is a plain range, not a confidence interval. With 5 seeds a bootstrap interval would add little, and the range needs no random draws.
- The figure also marks:
  - the Nash price (grey dashed line);
  - the deal price, which equals the joint monopoly price (black dashed line);
  - the spy round `spy_start` (dotted vertical line);
  - the "do" window, shaded: rounds `spy_start+1` to `spy_start+behavioral_window`, with the window read from PREREGISTRATION.md.
  
  All reference values come from the logs.
- If a game ends early, a round only counts the games that reached it.
- Colors are categorical slots in fixed condition order, checked for colorblind separation. Each condition also has its own marker shape, so the lines can be told apart in grayscale.

This is a descriptive figure. It does not test anything. The preregistered numbers stay in `tools/reproduce.py` (tables, base rate, Wilson intervals). Describe the figure in the report as the mean price path per condition. Do not read a "do" result from it: "do" is a per-firm rule applied in every window round, and the figure shows means.

## What the price shift figure shows (EXPLORATORY)

`price_shift.pdf` has one panel per family and one row per condition, sharing the x axis. It answers "did the offer move prices?" in a single number per condition:

- For each game, take the mean price of both firms over the do window (rounds `spy_start+1` to `spy_start+3`).
- Average that over the condition's games, then subtract the same average over the No spy games (same rounds, same family). A memory arm uses the memory No spy when run.
- The dot is the shift, in price units. The panel title gives deal minus Nash for scale.
- The whisker is a 95% percentile bootstrap interval. Games are resampled with replacement inside the condition and inside No spy, 2000 draws. The seed is fixed per family and condition, so the output is deterministic.
- Games with an incomplete window are left out.
- A family that mixes spy rounds gets no figure: the CLI prints why.

With 5 seeds per group the interval is coarse. Use it as a picture, not a test. The preregistered "do" rate and base rate stay in `tools/reproduce.py`.

## What the excerpt shows

`excerpt.md` holds, for one game:

- the condition (full name), family and seed;
- the deal, Nash and "do" tolerance values;
- the spy message, verbatim from the log field `message`;
- both firms' raw replies in the spy round, verbatim from `rounds[].firms[].reply`, in code fences that survive backticks;
- a table of both prices and the parsed reply fields for rounds `spy_start-1` to `spy_start+3`.

Every number is read from the log. Pick the game id from `labels.csv` or `viz/data/games.csv`. Choosing a representative game is a human call and should be stated in the report (dual-use rule R21: excerpts, not a playbook).

## Tests

`tests/test_artem_price_paths.py`, `tests/test_artem_price_shift.py` and `tests/test_artem_price_shift_extra.py` use hand-built mini runs. They include hand-computed shift values, interval bounds, a zero-spread case and the quantile rule. The per-round mean, minimum and maximum are computed by hand in the test comments. The file also covers:

- games of unequal length;
- the memory arm kept as a separate arm;
- full-name legend labels;
- byte-identical PDFs with the API key unset;
- verbatim message and replies, the exact excerpt table rows and the fence escaping;
- the CLI filtering, and refusal to mix memory and frozen logs.
