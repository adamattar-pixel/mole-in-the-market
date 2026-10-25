# Numbers audit (R18) - 2026-10-25, branch wip/phase-4-adam-numbers
Tool: `tools/check_numbers.py` (new, tests first: locked de935f8, gap tests in tests/test_R18_gaps.py).
Question: does every result number written in the team's documents appear in the outputs of `reproduce`
(results/ and results_exploratory/)? This audit only READS the documents; it changes none of them.

## Command (from the repo root, code at e6675ef)
```
python -m tools.check_numbers <doc> --sources results results_exploratory --allow 0.10 10% 0.25 0.5 1.473 1.47293 0.45205 1.8798 1.9702 1.925 3.3 3.8
```
`--allow` lists numbers that are not results: frozen design constants (tolerance 0.10 = 10%, E threshold 0.25,
D1 fraction 0.5, Nash 1.473 / 1.47293, gap 0.45205, deal band 1.8798-1.9702, deal 1.925) and model versions
(Llama 3.3, Qwen 3.8).

## Result
| Document | Result numbers checked | Not found in the sources |
|---|---|---|
| docs/team-artem/RESULTS_SUMMARY.md | 204 | 9 |
| docs/team-artem/KEY_FIGURE.md | 14 | 1 |
| docs/team-artem/PAGE1_EXCERPT.md | 14 | 0 |
| report/SKELETON.md | 24 | 2 |

No invented number was found. Each number not found in the sources is classified below.

### A. Computed from the game's demand, checked independently here (correct)
Recomputed with harness/economics.py, LogitDemand(a=2, a0=0, mu=0.25, c=1, beta=100, alpha=1), both firms at the same price:
- RESULTS_SUMMARY.md:64 and :145 "15.98 at 2.50": profit at 2.50 = 15.9760 -> 15.98. Correct. (33.75 at 1.92: 33.7472 -> 33.75, found.)
- RESULTS_SUMMARY.md:142 "margin falls from 1.50 to 0.92": 1.92 - 1 = 0.92. Correct.
- RESULTS_SUMMARY.md:142 "would need 17.37 units": 15.98 / 0.92 = 17.37. Correct.
- report/SKELETON.md:166 "Wilson width up to 0.65 at n=5": widths at n = 5 are 0.4345 (k=0,5), 0.5882 (k=1,4), 0.6517 (k=2,3) -> up to 0.65. Correct.
These are correct but come from a hand computation, not from a `reproduce` output. If they go into the report,
either cite the computation in a footnote or add them to an exploratory output so R18 holds.

### B. Read from logs or traces, not from a `reproduce` output (cite the source in the report)
- RESULTS_SUMMARY.md:131 "one firm 2.49 in round 20": a price in a game log (runs/), not an aggregate.
- RESULTS_SUMMARY.md:144 "(like 1.91)": a quote from a model's reasoning trace.
- RESULTS_SUMMARY.md:130 "80/80 traces present": 40 + 40 traces of the two THINK games (extras.json lists 40 per game, the sum 80 is not written).
- RESULTS_SUMMARY.md:160 "do 2/3": archived Llama pilot, marked "not for tables" in the document itself.
- KEY_FIGURE.md:75 "14/40 firm-rounds at price 10": counted in the Llama E logs, not in an output file.

### C. Not result numbers (tool false positives, harmless)
- RESULTS_SUMMARY.md:191 "6.3 in wide": a figure size.
- report/SKELETON.md:143 "must equal 4.1": a reference to section 4.1 written without the word "section".

## Recommendation for the report
1. Run `python -m tools.check_numbers report/<draft>.md --sources results results_exploratory --allow <constants>` on every draft; it must exit 0 or every remaining line must be in class B or C with a cited source.
2. For class A numbers, add a footnote with the formula (or move them to an exploratory output).
3. For class B numbers, name the game id and round, or the trace, next to the number.
