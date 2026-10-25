# Remaining runs: what is left, in what order, at what cost (2026-10-26)
Everything below has working code and a passing dry run (`python3 -m tools.run_all --dry --exploratory --think --o1 --workers 4`,
exit 0, no key). Nothing here was run for real. 2026-10-26: GO given (D37, at most 3 USD of new spend), but no OPENROUTER_API_KEY was available on the machine, so nothing ran (OPEN_ISSUES #28).

## Not run yet
| Step | Config | Games (after the declared Llama-only deviation) | Estimate at the observed rate | Planning rate 0.25 USD/game | Config cap |
|---|---|---|---|---|---|
| Rule monitor (R31-R32, H6) | configs/espion_monitor.yaml | 15 Llama (B_MON, C_MON, D_MON x 5 seeds) | 15 x 0.0121 = 0.18 USD | 3.75 USD | 7.5 USD |
| Ethics sentence (R33-R34, H7) | configs/espion_ethics.yaml | 5 Llama (B_ETH x 5 seeds) | 5 x 0.0121 = 0.06 USD | 1.25 USD | 2.5 USD |
| O1, seeds 6-10 (core, diagnostic) | configs/run_all.yaml `o1_seeds` | 20 Llama (B, B_T, C, D x 5 seeds) | 20 x 0.0121 = 0.24 USD | 5.00 USD | 10 USD (`o1_budget_usd`) |
| Memory arm (exploratory) | configs/exploratory/espion_mem.yaml | 15 Llama | 15 x 0.0121 = 0.18 USD | 3.75 USD | 5 USD |
| THINK arm, gpt-oss-120b (exploratory) | configs/exploratory/espion_think.yaml | 30 (family openai) | no observed cost for this model | 7.50 USD | 1.5 USD (the cap stops it first) |
| Total | | 85 games | 0.66 USD + THINK (at most 1.5) | 21.25 USD | global cap 30 USD (configs/run_all.yaml) |

- Observed rate: mean cost_usd per game in runs/ (Llama 0.0121 over 32 logs, Haiku 0.0238 over 12 logs). The planning rate
  0.25 USD/game is the conservative figure used to size the caps (QUESTIONS #17, from the Sonnet billing in QUESTIONS #27).
- The caps stop each step before its config cap and the whole pipeline before 30 USD (spend in logs + the ledger
  runs/_spend.jsonl, OPEN_ISSUES #8). Finished games are skipped on a rerun.
- Prices: configs/prices.yaml (Llama 0.10/0.32, Haiku 1.00/5.00, gpt-oss-120b 0.15/0.60 USD per 1M tokens in/out).

## Commands, in order (repo root)
```
python3 -m pytest -q                                   # must be green first
export OPENROUTER_API_KEY=...                          # in the shell or the repo-root .env (never committed)
python3 -m tools.run_all --continue-passing-families --workers 4
#   resumes: smoke, pilot, gate and core are already logged and skipped; runs monitor, ethics, then scoring
python3 -m tools.run_all --continue-passing-families --exploratory --think --o1 --workers 4
#   adds the memory arm, the THINK arm and O1 (last)
python3 -m tools.reproduce runs results --deviations run_all_deviations.json --viz-dir viz/data --figures-dir figures
python3 -m tools.validate_e runs --config espion_pilot
```
`--continue-passing-families` keeps the declared deviation (Llama only after Haiku failed the E gate, QUESTIONS #24/#27, D29).
Without it the pipeline stops at the gate with plan B, as preregistered.

## With N USD of credit, run first
| Credit | Run | Why |
|---|---|---|
| under 1 USD | monitor, then ethics (first command) | they test the frozen addendum hypotheses H6 and H7; about 0.24 USD at the observed rate |
| 1 to 2 USD | + O1 and the memory arm (second command without --think) | more seeds for the core, then the exploratory memory arm; about 0.42 USD more |
| 2 USD or more | everything (second command as written) | the THINK arm is capped at 1.5 USD by its config |

## Haiku exploratory runs (optional, OPEN_ISSUES #28)
Haiku failed the positive control, so its games are exploratory only. Two routes:
- OpenRouter BYOK (decision D23): the Anthropic key stays in OpenRouter's settings; nothing to change here.
- Direct Anthropic API (new, mock-tested only): mark the family `client: anthropic` in a copy of the config and export
  ANTHROPIC_API_KEY. This departs from D23 (the key would live in the shell), so it is an owner decision (QUESTIONS #33).
  The model id mapping (anthropic/claude-haiku-4.5 -> claude-haiku-4-5) must be checked against Anthropic's model list
  before the first real call; no test ever called the real API.
At the observed Haiku rate (0.0238 USD/game), the 20 Haiku games of B, B_T, C, D cost about 0.48 USD.
