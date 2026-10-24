# RUNBOOK - first real runs (owner: Artem)

Copy-paste sequence for the first real run with `tools/run_all.py` (R36). Every real call costs money and
needs the owner's GO (hard stop H2). Run the commands from the repo root, on branch `artem`.
Nothing here needs PREREGISTRATION.md or PREREGISTRATION_ADDENDUM.md to change: both are FROZEN and
`run_all` refuses to start otherwise.

Models (decision D23): `anthropic/claude-haiku-4.5` (OpenRouter BYOK, Artem's Anthropic key) and
`meta-llama/llama-3.3-70b-instruct` (OpenRouter credits), temperature 1.0, no reasoning key. Costs below use the
MODEL_AND_COST.md basis (15,000 input + 2,400 output tokens per game, conservative, prices fetched 2026-10-24)
for this pair, raw / with the 3x safety margin (table: MODEL_AND_COST.md "Final choice"). Times are an
ESTIMATE (MODEL_AND_COST.md gives none): calls are sequential, 40 calls per game, assumed 1 to 3 s per call,
so about 1 to 2 min per game. Measure the real time on the smoke step and rescale. The times below are for
`--workers 1`; with `--workers N` (section "Parallel games") divide the step times by about N.

## Parallel games: `--workers N` (recommended `--workers 4`)

`python3 -m tools.run_all ... --workers 4` (also `python3 -m tools.run CONFIG --workers 4`) runs 4 games of a
step at the same time. Games are independent: the logs, tables and checksums are identical to `--workers 1`
(checked on the dry run: `diff -r` of two roots gives no difference). Default is 1 (one after the other).
- Recommended for OpenRouter: **4** (5 or 6 if no HTTP 429 shows up in the smoke). About 270 games x 1 to 2 min
  = 4.5 to 9 h sequential, about 1.2 to 2.3 h with 4 workers. Haiku is billed on Artem's Anthropic key (BYOK),
  so the Anthropic rate limit of that key applies: 4 workers send about 80 to 240 requests per minute. A low
  Anthropic tier (for example 50 requests per minute) gives 429s: use `--workers 2`, or check the tier first.
- HTTP 429 and 5xx are retried up to 5 times per call, waiting 2, 4, 8, 16 s (or the server's Retry-After,
  at most 60 s). Other errors are not retried. A failed request costs nothing in the trackers.
- Budget caps stay safe: no call is sent once a cap is crossed, so a cap can be passed by at most N calls in
  flight (sequential: 1 call). With Haiku at about 0.0007 USD per call that is under 0.01 USD at N = 6.
  When a cap is hit, the up-to-N games in progress are dropped (no log); their partial spend is real.
- A game that raises (for example a provider error after the retries) is printed as `FAILED (not logged)`
  with its game id; the other games of the step finish and are logged; run_all stops with exit 4 before the
  next step. Rerun the same command: finished games are skipped, the failed ones run again.
- Smoke first with `--workers 4` too, and watch the `[smoke]` lines and the OpenRouter activity page.

## 0. Install and check (no key, no cost)

```
cd <repo> && git checkout artem && git status        # clean tree
python3 -m pip install -r requirements.txt
python3 -m pytest                                     # expect 672 passed
python3 -m tools.run_all --dry --exploratory --o1     # whole chain on the mock client, writes dry_runs/run_all/
```
The dry run must end with `run_all: done` and exit code 0 (`echo $?`). Its numbers are mock, never results.

## 1. API key in a local .env, BYOK and credits

```
cp .env.example .env      # then open .env and paste the OpenRouter key after OPENROUTER_API_KEY=
git check-ignore .env     # must print .env (it is in .gitignore): never commit it
```
`tools/run.py` and `tools/run_all.py` load `.env` from the repo root at startup (harness/envfile.py): a
variable already set in the shell wins, values are never printed. Only `OPENROUTER_API_KEY` goes in `.env`.

Prerequisites on openrouter.ai (once, by the owner):
- **BYOK**: Settings > Integrations > Anthropic: add Artem's Anthropic key and set it to **"Never use shared
  capacity"**, so Claude Haiku 4.5 (and the Sonnet 4.5 fallback) is billed to that key and never silently to
  OpenRouter credits. The Anthropic key is NOT put in `.env`.
- **Credits**: the OpenRouter account needs credits: Llama 3.3 (and the Qwen fallback) are paid from them, and
  BYOK requests pay OpenRouter's small fee. Also set a spend limit on the OpenRouter account and on the
  Anthropic console.

## 2. Model ids, temperature, reasoning (decision D23, done)

The six step configs (`espion_smoke`, `espion_pilot`, `espion_core`, `espion_monitor`, `espion_ethics`,
`exploratory/espion_mem`) hold the D23 pair with `temperature: 1.0` and no `reasoning` key (Haiku 4.5 reasoning
is optional and off by default; Llama 3.3 has none). configs/run_all.yaml fallbacks: anthropic ->
`anthropic/claude-sonnet-4.5` (label `anthropic-fb`), meta-llama -> `qwen/qwen3-235b-a22b-2507` (label `qwen`).
All four models are priced in `configs/prices.yaml` (fetched 2026-10-24). Each call is charged
max(usage.cost, tokens x price): under BYOK usage.cost is about 0, so the token price is what hits the caps.
Still to decide: `budget_usd` in configs/run_all.yaml (global cap, PROPOSAL 30.0 USD) and the per-config caps
(ops/QUESTIONS.md #11, #17).

## 3. Smoke (4 games: A, E x seed 1 x 2 families, 160 calls)

Cost: about 0.059 raw (0.054 Haiku on the Anthropic key, 0.005 Llama on credits) / 0.18 USD with margin
(cap 1.0). Time: about 5 to 10 min.
```
time python3 -m tools.run_all --stop-after smoke; echo "exit $?"
```
Check in the `[smoke]` lines, per family:
- served model and provider: `anthropic/claude-haiku-4.5` (a dated version is fine) with provider Anthropic,
  and `meta-llama/llama-3.3-70b-instruct` with a provider listed.
- upstream inference cost (BYOK): for `anthropic`, a value close to the charged cost per game x 2 games (that is
  Anthropic's bill on the key). None or 0 for `anthropic` means BYOK was not used (check the BYOK setting).
  For `meta-llama` it is usually None (paid from credits).
- charged cost per game: close to 0.027 (Haiku) and 0.0023 (Llama). Much higher means hidden reasoning or a
  price change: stop and look.
- invalid prices and invalid responses: near 0. Above about 0.05 makes "do" unreliable (ops/QUESTIONS.md #10).
- served model and provider: the model you asked for (a dated version is fine), a provider listed.
- reasoning tokens: 0 (or None if the provider does not report them). If a family shows tokens > 0, add
  `reasoning: {effort: none}` to that family entry in the six configs, commit, and only then go on.
- cost per call (`provenance`): `cost_reported` (usage.cost, about 0 under BYOK), `cost_computed` (tokens x
  configs/prices.yaml), `cost_charged` (the larger), `cost_source` (`token_price` expected for Haiku) and
  `upstream_inference_cost` when OpenRouter reports it.
Spot-check one log by hand and the OpenRouter activity page (spend should match the printed total):
```
python3 -c "import json,glob; g=json.load(open(sorted(glob.glob('runs/espion_smoke__*__E__s1.json'))[0])); \
f=g['rounds'][7]['firms']['0']; print(g['models'], g['temperature'], g['cost_usd'], f['provenance']['served_model'], \
f['provenance']['provider'], f['provenance'].get('cost_source'), f['provenance'].get('cost_charged'), \
f['provenance'].get('upstream_inference_cost'), f['reply'][:200])"
```

## 4. Pilot and E gate (20 games: A, E x 5 seeds x 2 families)

Cost: about 0.29 raw / 0.88 USD with margin (cap 5.0). Time: about 20 to 40 min.
```
time python3 -m tools.run_all --stop-after gate; echo "exit $?"
```
Read the `[gate]` lines: E is validated per family on the pilot games only (smoke excluded) when E beats A by
at least 0.25 of the Nash to monopoly gap (PREREGISTRATION.md). Use this output, not `tools.validate_e runs`,
which pools smoke and pilot (ops/QUESTIONS.md #23).
- Both PASS: go to step 5.
- A family FAILS: run_all switches that family ONCE to its fallback and runs its pilot as
  `espion_pilot_fb` (10 games: Sonnet 4.5 about 0.81 raw / 2.4 with margin, Qwen3 about 0.03 / 0.08).
  The replaced family's pilot games stay in runs/ (write-once) and are listed as "superseded" in the tables.
- Fallback also FAILS, or no fallback set: exit code 2 and the plan B message. Do NOT try a third model
  (the one change is used). The only alternative to plan B is `--continue-passing-families` (below). Stop real runs, write the result in ops/PROGRESS.md and ops/QUESTIONS.md, tell Adam,
  and switch to plan B (ops/PLAN.md: track 1.5, Pareto curve of restrictions, docs/context/contexte_projet_v7.md
  section 10). The failed E is itself a reportable result.
- `--continue-passing-families` (off by default; owner decision, ops/QUESTIONS.md #24): instead of plan B, go
  on with only the families that passed E (primary or fallback), for example 2 families -> 1. This is a
  DECLARED DEVIATION from the preregistered plan: run_all prints `DEVIATION` lines on every run, records it
  in the returned summary and in `run_all_deviations.json` (repo root), and keeps the dropped family's pilot
  games out of the tables (they stay in runs/, counted as superseded). Report it in the paper as a deviation.
  Use the same flag on every later command, or the next run stops at the gate with plan B again:
  `time python3 -m tools.run_all --continue-passing-families --workers 4; echo "exit $?"`
  If no family passes, it is plan B anyway (exit 2).

## 5. Core, monitor, ethics, then scoring (80 games, then offline)

Cost: core 40 games about 0.59 raw / 1.76 (cap 10), monitor 30 about 0.44 / 1.32 (cap 7.5), ethics 10 about
0.15 / 0.44 (cap 2.5). Time: about 1.5 to 3 h in total. Same command; finished games are skipped:
```
time python3 -m tools.run_all; echo "exit $?"
```
Or one step at a time: `--stop-after core`, then `--stop-after monitor`, `--stop-after ethics`, then no flag.
Outputs (scoring needs no key and no network; rerun it any time with the same command):
- `results/`: tables.md, summary.json, labels.csv, detectors.md/.json (R29-R30), defenses.md/.json (R32, R34), checksums.txt
- `viz/data/` (R22), `figures/game_grid.pdf` (R27, Figure 1)
Every report number comes from these files (CLAUDE.md rule 2).

## 6. Exploratory memory arm and views (optional, after step 5)

30 games (A, B, D with memory), about 0.44 raw / 1.3 USD with margin (cap 5.0; longer prompts, estimate).
Time: about 30 to 60 min.
```
time python3 -m tools.run_all --exploratory
```
Writes `runs_exploratory/memory/` (never runs/), `results_exploratory/memory/`, `results_exploratory/sensitivity.md`,
`results_exploratory/monitor/`, `figures/exploratory/price_paths.pdf` and `price_shift.pdf`. Report all of it as
EXPLORATORY, not preregistered (docs/team-artem/MEMORY_ARM.md).

O1 (seeds 6-10 on B, B_T, C, D, 40 games, about 0.59 / 1.76 USD, cap 10) only if everything above is done and
time is left (cut order in ops/PLAN.md): `python3 -m tools.run_all --exploratory --o1`. Its tables go to
`results_o1/` (diagnostic); the preregistered `results/` never include O1.

## 7. If something stops

- Exit 3, "BUDGET CAP HIT": the game(s) in progress were dropped (no log, their partial spend is real; up to N
  games with `--workers N`). Raise a cap only with the owner's OK, then rerun the same command: it resumes.
- Exit 4, "FAILED (not logged)": some games raised (listed by game id); the others are logged. Rerun the same
  command to retry them. If the same games keep failing, read the error before going on.
- Crash, network error, closed laptop: rerun the same command. Logs are write-once; finished games are skipped.
- Exit 1, "REFUSED": read the reason (key missing from .env and the shell, `tbd` id, families differ between configs, freeze
  status). Never edit the frozen files to get past it.

## 8. Runs freeze: Sunday Oct 25, 12:00 (noon)

No new real run after noon. Then:
```
python3 -m tools.run_all                       # final offline scoring (no new games, no cost)
git add runs/ runs_exploratory/ results/ results_exploratory/ viz/data/ figures/
git status                                     # .env not listed (ignored), no key anywhere
git commit -m "Freeze real runs"
git tag runs-frozen
```
Push is the owner's call. Write the report numbers only from `results/` (and label the exploratory ones).

## Totals (D23 pair: Haiku 4.5 + Llama 3.3, estimates)

| Step | Games | Calls | Raw USD | With 3x margin | Cap |
|---|---|---|---|---|---|
| Smoke | 4 | 160 | 0.059 | 0.18 | 1.0 |
| Pilot | 20 | 800 | 0.29 | 0.88 | 5.0 |
| Core | 40 | 1,600 | 0.59 | 1.76 | 10.0 |
| Monitor | 30 | 1,200 | 0.44 | 1.32 | 7.5 |
| Ethics | 10 | 400 | 0.15 | 0.44 | 2.5 |
| Main chain | 104 | 4,160 | 1.52 | 4.57 | global 30 (proposal) |
| + memory arm | 30 | 1,200 | ~0.44 | ~1.3 | 5.0 |
| + O1 | 40 | 1,600 | 0.59 | 1.76 | 10.0 |
| + fallback pilot, if used | 10 | 400 | 0.03 (Qwen) to 0.81 (Sonnet) | 0.08 to 2.43 | pilot cap |

About 92% of the spend is Haiku, billed to the Anthropic key (BYOK); the rest is OpenRouter credits.
