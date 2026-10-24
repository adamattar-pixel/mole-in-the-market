# RUNBOOK - first real runs (owner: Artem)

Copy-paste sequence for the first real run with `tools/run_all.py` (R36). Every real call costs money and
needs the owner's GO (hard stop H2). Run the commands from the repo root, on branch `artem`.
Nothing here needs PREREGISTRATION.md or PREREGISTRATION_ADDENDUM.md to change: both are FROZEN and
`run_all` refuses to start otherwise.

Costs below use the MODEL_AND_COST.md basis (15,000 input + 2,400 output tokens per game, conservative,
prices fetched 2026-10-24) for the earlier recommended pair (gpt-5.4 + Llama 3.3), raw / with the 3x
safety margin. Recompute them for Adam's pair (D10). Times are an
ESTIMATE (MODEL_AND_COST.md gives none): calls are sequential, 40 calls per game, assumed 1 to 3 s per call,
so about 1 to 2 min per game. Measure the real time on the smoke step and rescale.

## 0. Install and check (no key, no cost)

```
cd <repo> && git checkout artem && git status        # clean tree
python3 -m pip install -r requirements.txt
python3 -m pytest                                     # expect 653 passed
python3 -m tools.run_all --dry --exploratory --o1     # whole chain on the mock client, writes dry_runs/run_all/
```
The dry run must end with `run_all: done` and exit code 0 (`echo $?`). Its numbers are mock, never results.

## 1. API key: in the shell only, never in a file

```
read -s OPENROUTER_API_KEY && export OPENROUTER_API_KEY   # paste the key, press Enter (not echoed, not in history)
```
Never put the key in `.env`, a config, a commit or a chat. Open a new terminal = export it again.
Also set a spend limit on the OpenRouter account.

## 2. Model ids, temperature, reasoning (decision D10)

**Waiting on Adam: model ids (D10).** The step configs and the configs/run_all.yaml fallbacks hold `tbd`
placeholders, and a real run refuses them. Candidates, prices, reasoning and temperature support:
docs/team-artem/MODEL_AND_COST.md. `temperature: 1.0` is already set in every real config.

When Adam gives the ids:
1. Replace `family1-tbd`, `family2-tbd` (labels and ids) in the six step configs (`espion_smoke`, `espion_pilot`,
   `espion_core`, `espion_monitor`, `espion_ethics`, `exploratory/espion_mem`; the `families` blocks must be
   identical) and the two fallbacks in configs/run_all.yaml. The family label is the id prefix
   (`provider/model`); a fallback from the same provider is labelled `<provider>-fb`.
2. Add a `reasoning` key only for a model that reasons by default (FIXES_CLIENT.md decision 2).
3. Add or re-check every id in `configs/prices.yaml` (input / output USD per 1M from
   `https://openrouter.ai/api/v1/models`, with the fetch date). A model with no price is refused: each call
   is charged max(usage.cost, tokens x price), so a provider that under-reports cost still hits the caps.
4. Run the suite (all green, no test change needed) and commit BEFORE any real call, so every log's
   `git_commit` points at the real ids:
```
python3 -m pytest && python3 -m tools.run_all --dry
git diff configs/                                   # read it: families, fallback, prices
git add configs/ && git commit -m "Set model ids for real runs (D10)"
```
Also decide `budget_usd` in configs/run_all.yaml (global cap, PROPOSAL 30.0 USD) and the per-config caps
(QUESTIONS.md #11, #17).

## 3. Smoke (4 games: A, E x seed 1 x 2 families)

Cost: about 0.15 raw / 0.45 USD with margin (cap 1.0). Time: about 5 to 10 min.
```
time python3 -m tools.run_all --stop-after smoke
```
Check in the `[smoke]` lines, per family:
- cost per game: compare with MODEL_AND_COST.md for the chosen pair. Much higher means hidden reasoning or a
  price change: stop and look.
- invalid prices and invalid responses: near 0. Above about 0.05 makes "do" unreliable (QUESTIONS.md #10).
- served model and provider: the model you asked for (a dated version is fine), a provider listed.
- reasoning tokens: 0 (or None if the provider does not report them). If a family shows tokens > 0, add
  `reasoning: {effort: none}` to that family entry in the six configs, commit, and only then go on.
- cost per call (`provenance`): `cost_reported` (usage.cost), `cost_computed` (tokens x configs/prices.yaml),
  `cost_charged` (the larger) and `cost_source`. `token_price` on many calls means usage.cost is below the
  list price: check the OpenRouter activity page, the caps already use the larger value.
Spot-check one log by hand and the OpenRouter activity page (spend should match the printed total):
```
python3 -c "import json,glob; g=json.load(open(sorted(glob.glob('runs/espion_smoke__*__E__s1.json'))[0])); \
f=g['rounds'][7]['firms']['0']; print(g['models'], g['temperature'], g['cost_usd'], f['provenance']['served_model'], \
f['provenance']['provider'], f['provenance'].get('cost_source'), f['reply'][:200])"
```

## 4. Pilot and E gate (20 games: A, E x 5 seeds x 2 families)

Cost: about 0.76 raw / 2.3 USD with margin (cap 5.0). Time: about 20 to 40 min.
```
time python3 -m tools.run_all --stop-after gate; echo "exit $?"
```
Read the `[gate]` lines: E is validated per family on the pilot games only (smoke excluded) when E beats A by
at least 0.25 of the Nash to monopoly gap (PREREGISTRATION.md). Use this output, not `tools.validate_e runs`,
which pools smoke and pilot (QUESTIONS.md #23).
- Both PASS: go to step 5.
- A family FAILS: run_all switches that family ONCE to its fallback and runs its pilot as
  `espion_pilot_fb` (10 games; cost depends on the fallback model, see MODEL_AND_COST.md).
  The replaced family's pilot games stay in runs/ (write-once) and are listed as "superseded" in the tables.
- Fallback also FAILS, or no fallback set: exit code 2 and the plan B message. Do NOT try a third model
  (the one change is used). Stop real runs, write the result in PROGRESS.md and QUESTIONS.md, tell Adam,
  and switch to plan B (PLAN.md: track 1.5, Pareto curve of restrictions, docs/context/contexte_projet_v7.md
  section 10). The failed E is itself a reportable result.

## 5. Core, monitor, ethics, then scoring (80 games, then offline)

Cost: core 40 games about 1.52 raw / 4.6 (cap 10), monitor 30 about 1.14 / 3.4 (cap 7.5), ethics 10 about
0.38 / 1.1 (cap 2.5). Time: about 1.5 to 3 h in total. Same command; finished games are skipped:
```
time python3 -m tools.run_all; echo "exit $?"
```
Or one step at a time: `--stop-after core`, then `--stop-after monitor`, `--stop-after ethics`, then no flag.
Outputs (scoring needs no key and no network; rerun it any time with the same command):
- `results/`: tables.md, summary.json, labels.csv, detectors.md/.json (R29-R30), defenses.md/.json (R32, R34), checksums.txt
- `viz/data/` (R22), `figures/game_grid.pdf` (R27, Figure 1)
Every report number comes from these files (CLAUDE.md rule 2).

## 6. Exploratory memory arm and views (optional, after step 5)

30 games (A, B, D with memory), about 1.3 raw / 4.0 USD with margin (cap 5.0; longer prompts, estimate).
Time: about 30 to 60 min.
```
time python3 -m tools.run_all --exploratory
```
Writes `runs_exploratory/memory/` (never runs/), `results_exploratory/memory/`, `results_exploratory/sensitivity.md`,
`results_exploratory/monitor/`, `figures/exploratory/price_paths.pdf` and `price_shift.pdf`. Report all of it as
EXPLORATORY, not preregistered (docs/team-artem/MEMORY_ARM.md).

O1 (seeds 6-10 on B, B_T, C, D, 40 games, about 1.52 / 4.6 USD, cap 10) only if everything above is done and
time is left (cut order in PLAN.md): `python3 -m tools.run_all --exploratory --o1`. Its tables go to
`results_o1/` (diagnostic); the preregistered `results/` never include O1.

## 7. If something stops

- Exit 3, "BUDGET CAP HIT": the game in progress was dropped (no log, its partial spend is real). Raise a
  cap only with the owner's OK, then rerun the same command: it resumes.
- Crash, network error, closed laptop: rerun the same command. Logs are write-once; finished games are skipped.
- Exit 1, "REFUSED": read the reason (key not exported, `tbd` id, families differ between configs, freeze
  status). Never edit the frozen files to get past it.

## 8. Runs freeze: Sunday Oct 25, 12:00 (noon)

No new real run after noon. Then:
```
python3 -m tools.run_all                       # final offline scoring (no new games, no cost)
git add runs/ runs_exploratory/ results/ results_exploratory/ viz/data/ figures/
git status                                     # no .env, no key anywhere
git commit -m "Freeze real runs"
git tag runs-frozen
```
Push is the owner's call. Write the report numbers only from `results/` (and label the exploratory ones).

## Totals (recommended pair, estimates)

| Step | Games | Raw USD | With 3x margin | Cap |
|---|---|---|---|---|
| Smoke | 4 | 0.15 | 0.45 | 1.0 |
| Pilot | 20 | 0.76 | 2.27 | 5.0 |
| Core | 40 | 1.52 | 4.55 | 10.0 |
| Monitor | 30 | 1.14 | 3.41 | 7.5 |
| Ethics | 10 | 0.38 | 1.14 | 2.5 |
| Main chain | 104 | 3.94 | 11.8 | global 30 (proposal) |
| + memory arm | 30 | ~1.3 | ~4.0 | 5.0 |
| + O1 | 40 | 1.52 | 4.55 | 10.0 |
| + fallback pilot, if used | 10 | 0.03 to 0.5 | 0.08 to 1.5 | pilot cap |
