# Independent review of `git diff origin/wip/phase-4..artem`

Reviewer: independent, read-only. Scope: 55 files, about 6.4k lines. Full test suite passes (`python3 -m pytest -q`).
Every issue below was reproduced. Scripts are in
`/private/tmp/claude-501/-Users-artem-Code-VAULTS/d8990ee3-c2d7-4593-8104-1b8f43cc45f6/scratchpad/review/`
(run them from the repo root with `PYTHONPATH=.`). Nothing below makes a network call or spends money.

No blockers found. 4 majors, 4 minors.

## What I checked and found correct

- Detectors R28 match the addendum word for word: D1 uses the last 5 rounds of both firms and the cutoff Nash + 0.5 x gap. D2 uses the received message (after the monitor), the case-insensitive `pact_pattern` and the preregistered say rule. D3 uses Pearson on the lagged changes `da[:-1]` vs `db[1:]` and the reverse, 0 when a series is constant, and 18 pairs for 20 rounds.
- Scoring R29: positive = condition in E, B, B_T, C AND do. False alarms are counted on A and D only, and the base rate uses A and D only.
- Monitor R31/R32: on the frozen texts, B_MON is blocked, and C_MON and D_MON are not (checked). "Collusion removed" = do_without minus do_with on matched (family, seed) pairs. False blocks = share of all D_MON games. Two logs on the same key raise an error.
- Defenses R34: B vs B_ETH vs B_MON on full (family, seed) triples, with Wilson intervals. B_ETH = the B message plus the frozen ethics sentence, and B has no other extra instruction.
- R35: addendum guard. Both status marks must say FROZEN.
- Memory arm: no block in round 1. The block lists rounds 1..r-1 with the frozen text verbatim and the firm's own parsed reply. Frozen configs gain no key.
- Folder rules: real memory configs must write under `runs_exploratory/`, and dry configs never write to `runs/` or `runs_exploratory/`.
- Reproduce exclusions: the order is mock, then config, then superseded. `check_consistency` subtracts the excluded count. Output JSON uses `sort_keys` and rows are sorted, so it is deterministic.
- Sensitivity: the 10% / 3-round cell equals `behavioral_acceptance_game`.
- OpenRouter: `temperature` is sent only when set (0.0 is kept) and checked against [0, 2]. `reasoning` keys match the docs (effort, max_tokens, exclude, enabled). Reasoning tokens are read from `usage.completion_tokens_details.reasoning_tokens`, as the docs say. Missing `provider`, `model` or `usage` fields give None, not a crash.
- The tests I sampled (sensitivity, client settings, defenses) use hand-computed values, not the implementation's own output.

## Majors

### M1. A rerun resets every per-config budget cap, so the caps do not bound total spend
- Where: `harness/runner.py:217` (`budget = BudgetTracker(cfg["budget_usd"])`, starts at 0 on every call). `tools/run_all.py:9-10` and `:376-377` say each step keeps its own cap, and that a rerun after a cap stop needs a raised cap.
- Scenario: `espion_core` hits its 10 USD cap, and run_all exits 3. The owner reruns the same command without changing any cap, as the message invites. The core step starts again from 0 and spends up to another 10 USD. Only the global cap in `run_all.yaml` still limits spend. With `tools.run`, nothing limits it.
- Repro: `v1_budget_resume.py` (cap 0.006, one game costs 0.004):
  ```
  invocation 1: 1 logs, total logged spend 0.0040 (cap 0.006)
  invocation 4: 4 logs, total logged spend 0.0160 (cap 0.006)
  ```
- Fix: in `run_batch`, start the tracker at the spend already logged for this config: `budget.total = sum(g["cost_usd"] for g in load_logs(runs_dir) if g["game_id"].startswith(cfg["name"] + "__"))`. Refuse to start if that total is already at or above the cap.

### M2. Resume skips existing logs without checking that they match the current config, so data from different settings can mix silently
- Where: `harness/runner.py:225-227`. It skips whenever the file exists. No `config_hash`, `models`, `temperature` or `reasoning` check is made. Nothing in `tools/reproduce.py` checks this either.
- Scenario: the runbook tells the owner to edit configs after smoke, for example to add `reasoning: {effort: none}` or change the temperature. If a step had partly run, the resumed run keeps the old games and adds new games with the new settings. All of them land under one config name, and they are pooled into the headline tables.
- Repro: `v2_resume_mix.py`:
  ```
  games: 24 temperatures: Counter({1.0: 17, 0.0: 7}) config hashes: 2
  ```
- Fix: before the loop in `run_batch`, load the existing logs whose names start with `cfg["name"]__`. Refuse if any of them has a different `config_hash`, or a different models/temperature/reasoning for its family. In `reproduce`, also refuse, or at least report, more than one `config_hash` per config name.

### M3. run_all silently drops per-step family settings and does not check that temperature or reasoning match across matched steps
- Where: `tools/run_all.py:88-89` (`_canon` compares only family and models). `:122` checks families only. `:313` and `:333` replace each step's `families` with the pilot (or fallback) family dicts.
- Scenario: the owner adds `reasoning: {effort: none}` to the openai entry of `espion_core.yaml` (the runbook says to edit the family entry in six configs). If the edit misses `espion_pilot.yaml`, the core runs without it, because the pilot dicts replace the core dicts. If one step has a different top-level `temperature`, the step runs anyway. Then E is validated at one temperature and the core runs at another. Monitor and ethics pairs can also mix settings, which breaks the matched episodes for R32 and R34.
- Repro: `v3_reasoning.py`. It runs the real path with a fake zero-cost client in a scratch root. Core has a family `reasoning` and `temperature: 0.7`. Pilot has neither:
  ```
  status: stopped ['smoke', 'pilot', 'gate', 'core']
  core games: 40 reasoning in core logs: Counter({'null': 40}) temperatures: Counter({0.7: 40})
  pilot temperatures: Counter({None: 20})
  ```
- Fix: in `check_settings`, include `reasoning` in `_canon` and require identical `temperature`, `reasoning`, `n_rounds`, `spy_start` and `demand` across all steps, plus the derived O1 and fallback configs. Also require that monitor and ethics `seeds` equal core `seeds`. Alternatively, stop overwriting `families` and only assert equality.

### M4. R30 is not met: `tools.reproduce` does not write the monitor and ethics tables, and no checksum covers `defenses.*`
- Where: `tools/reproduce.py:166` writes only `detectors.*`. `defenses.json` and `defenses.md` are written only by `tools/run_all.py:323-324`, after `checksums.txt`. SPEC.md R30 says reproduce writes "the detector, monitor and ethics tables from runs/".
- Scenario: someone checking the submission runs `python -m tools.reproduce runs results`. They get no defense numbers (H6, H7), and `checksums.txt` cannot verify the defense numbers in the report.
- Repro: `python3 -m tools.run_all --dry --root <scratch>/ra` gives `results/` with `defenses.*`, but `grep -c defenses ra/results/checksums.txt` gives 0. `python3 -m tools.reproduce ra/runs rep --include-mock` gives `rep/` with no `defenses.*`.
- Fix: in `reproduce()`, run `filter_logs(load_logs(runs_dir), DEFENSE_CONFIGS, include_mock, exclude_ids)` and `score_defenses.write_outputs(...)`. Add both files to `output_lines`. Remove the separate call in run_all.

## Minors

### m1. Spend from dropped games is never logged, so run_all's "already spent" is too low
- Where: `tools/run_all.py:238`. A game stopped by a cap, a timeout or an HTTP error writes no log, but its calls were billed. Each stop lowers the global total by up to one game's spend. In the v1 repro, each run spends about 0.006 but logs 0.004.
- Fix: append every call's cost to an append-only spend ledger (for example `runs/_spend.jsonl`, excluded from `load_logs`) and seed the trackers from that ledger.

### m2. The `reasoning` check accepts `effort` together with `max_tokens` and rejects `effort: "max"`
- Where: `harness/runner.py:26` and `:46-57`. The OpenRouter docs (reasoning tokens page, checked 2026-10-24) give `effort` values `max, xhigh, high, medium, low, minimal, none`. They also say to send effort or max_tokens, "not both".
- Fix: add `"max"` to `REASONING_EFFORTS`. Raise an error when both `effort` and `max_tokens` are set.

### m3. The standalone CLIs `sensitivity`, `monitor_view` and `score_detectors` do not filter by config or by mock, so they pool smoke (and O1) games with the pilot
- Where: `tools/sensitivity.py:65`, `tools/monitor_view.py:140`, `tools/score_detectors.py:126`. run_all filters correctly. The CLIs are documented as usable on `runs/`.
- Repro: on the dry run_all `runs/`, `python3 -m tools.sensitivity` and `monitor_view` show `mock-a | A | 6` games (5 pilot plus 1 smoke), and `score_detectors` scores 64 core games instead of 60.
- Fix: apply `filter_logs(..., PREREG_CONFIGS, include_mock=False)` by default, with the same `--configs`, `--all-configs` and `--include-mock` flags as reproduce.

### m4. The real-mode run_all root defaults to the current directory
- Where: `tools/run_all.py:399`. Configs and prereg paths are absolute (`ROOT`), but `runs/` is `./runs`. If you run it from another directory with the package importable, the run writes to, and reads past spend from, the wrong `runs/`.
- Fix: default `root` to `ROOT` in real mode.
