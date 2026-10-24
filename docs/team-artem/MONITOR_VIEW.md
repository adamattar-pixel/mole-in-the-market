# Message vs action monitor view (EXPLORATORY, not preregistered)

`tools/monitor_view.py` recasts say vs do as an oversight question (NOVELTY_AND_JUDGES.md, action 2; sprint track 2.2: "Does combining what agents say with what they do beat either alone?"). Zero cost: it reads `runs/` with `harness.runlog.load_logs` and applies the preregistered say and do rules from `harness/metrics.py` unchanged. Nothing it outputs is a preregistered result.

## Why it matters

Many audits of AI agents read only transcripts. Antitrust also treats communication as the key "plus factor". If LLM sellers say yes without moving prices, a transcript-only auditor raises false alarms. If they move prices without saying yes, that auditor misses it. This view measures both errors and asks whether adding a price check helps.

## How to run

```
python -m tools.monitor_view runs                       # writes results_exploratory/monitor/
python -m tools.monitor_view runs --out-dir some/dir
```

The tool refuses any output folder inside `results/` and never touches `labels.csv`. Outputs: `monitor_view.md`, `monitor_cells.csv` and `monitor_detection.csv`. Each one starts with the "EXPLORATORY, not preregistered" header.

## How to read it

1. **2x2 per family and condition** (game is the unit, Wilson 95%):
   - Say+Do: both monitors flag the game.
   - Say only: a false alarm for a transcript monitor ("collusion on paper").
   - Do only: missed by a transcript monitor, caught only by a price check.
   - Neither: nothing flagged.
2. **Four monitors**: message (say), action (do), say OR do, say AND do. For each one, the table gives:
   - detection: share of offer games (B, B_T, C, E) flagged;
   - false positive: share of A and D games flagged.

   OR trades more detection for more false positives. AND does the reverse.

Caveats:
- The "ground truth" is **offer exposure, not collusion intent**. A "detection" only means the monitor reacted in a game where an offer was sent.
- In C (a hint), "accept" may answer a non-proposal.
- In A, nobody can say yes, so the message monitor's false positives come only from D.
- The action monitor's false positives on A and D measure drift toward the deal price without an offer. The permutation base rate covers the same issue.
- With 5 seeds per cell the intervals are wide. Read the counts, not only the rates.
