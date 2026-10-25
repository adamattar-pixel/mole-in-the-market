# OPEN_ISSUES - numbered backlog
One row per issue. Ids are never reused. Before working on one, claim it in ops/CLAIMS.md and set the status
to `in progress`. When done, set `done` with the commit or PR, and keep the row.
Status: `open`, `blocked` (waits on a person), `in progress`, `done`, `wontfix`. Owner `-` = not assigned yet.
Questions with a default already taken stay in ops/QUESTIONS.md; this file tracks the work they need.
Replay page items (#12-#16, #18, #19, #21, #22): Phase 8 is CUT (D17), so they are low priority and come after the report.

| # | Title | Owner | Status | Link |
|---|---|---|---|---|
| 1 | Model ids for the 2 families: fill the six step configs, the run_all fallbacks and configs/prices.yaml (real runs refused while `tbd`) | Adam | blocked | D10, QUESTIONS #7, RUNBOOK_REAL_RUNS.md step 2, docs/team-artem/MODEL_AND_COST.md |
| 2 | OpenRouter API key in the shell and GO for the first real run (smoke, pilot, E gate) | Artem | blocked | H2, RUNBOOK_REAL_RUNS.md |
| 3 | Affiliations placeholder "to be filled" in README.md:10, report/AUTHORS.md:3-4, report/SKELETON.md:17; fill or delete before submission | Artem, Adam | open | review m3 (pre-main review) |
| 4 | QUESTIONS #10: invalid price keeps the previous price (Nash in round 1); confirm or pick another rule | Artem | open | ops/QUESTIONS.md #10 |
| 5 | QUESTIONS #11, #17, #22: budget caps (smoke 1, pilot 5, core 10, monitor 7.5, ethics 2.5, global 30 USD) | Artem | open | ops/QUESTIONS.md, configs/run_all.yaml |
| 6 | QUESTIONS #12-#16, #18-#20: confirm the defaults taken (report skeleton, frozen addendum stands, literal readings) before the real runs | Artem | open | ops/QUESTIONS.md |
| 7 | QUESTIONS #21-#23: test(fix) on placeholder copies, run_all settings, validate_e --config; closed by merging PR #1 | Artem | in progress | docs/team-artem/OWNER_APPROVAL.md |
| 8 | Spend of dropped games (cap, timeout, HTTP error) is never logged, so run_all's "already spent" is too low; add an append-only spend ledger | Hoang | done | wip/phase-4-hoang: runs/_spend.jsonl, counted once with the game log |
| 9 | Standalone CLIs `sensitivity`, `monitor_view`, `score_detectors` do not filter by config or mock, so they pool smoke and O1 games with the pilot | Hoang | done | wip/phase-4-hoang: tools/cli_logs.py keeps pilot and core on an espion_* folder; hand-built test logs stay unfiltered (locked CLI tests) |
| 10 | `python tools/X.py` crashes with `ModuleNotFoundError: No module named 'harness'`; only `python -m tools.X` works. Fix the entry points or document `-m` everywhere | Hoang | done | wip/phase-4-hoang: each tool adds the repo root to the path when run as a script |
| 11 | `python -m tools.price_paths --help`: options (`--out-dir`, `--memory-runs`, `--game-id`, `--layout`, ...) have no help text | Hoang | done | wip/phase-4-hoang: tools/price_paths.py help strings |
| 12 | Replay page: at the offer round the speech bubble covers the mole and the price labels | Artem | done | viz/app.js, docs/viz/DESIGN.md |
| 13 | Replay page: sparse scene with tiny price bars | Artem | done | viz/app.js |
| 14 | Replay page: the meaning of the scene sits in small grey text | Artem | done | viz/app.js, viz/style.css |
| 15 | Replay page: labels "No spy" vs "Deal allowed (control)" confuse readers. The names are asserted by a locked test (tests/test_R22_R27_viz_export.py:77), so a change needs an owner-approved test(fix); done in the page only (viz/app.js display names), export names unchanged | Artem | done | harness/vizexport.py:12 |
| 16 | Replay page: the price chart is 112px high on mobile | Artem | done | viz/style.css |
| 17 | docs/context/contexte_projet_v7.md is a French internal planning note in the public repo, incl. speculation about the judges' scoring. Keep public before judging, or move out (never edited, so moving it is the owner's call) | Artem | open | pre-main review, notes |
| 18 | viz/app.js:251 defines Do with the "Nash-to-deal gap"; the preregistration and the code use the Nash-to-monopoly gap. Fix the wording | Artem | done | pre-main review m1 |
| 19 | viz/demo/meta.json:3 (and viz/demo/data.js) records the prereg hash of a CRLF copy, so it does not match the frozen file. Add `.gitattributes` with `* text=auto eol=lf` (or normalize before hashing), then regenerate viz/demo | Hoang, Adam (Claude) | done | .gitattributes added by both branches (same file); LF writes in the reproduce chain and viz/demo regenerated on wip/phase-4-adam-numbers, merged into wip/phase-4-final; remaining CRLF writes in docs/adam/REPRO_CHECK.md |
| 20 | ops/HANDOFF.md is stale (254 passed, "R28-R36 no code") | - | done | dated historical note added on `artem-ops-reorg`; current state in ops/STATE.md |
| 21 | tools/make_demo_data.py:33-36 guards output folders with a denylist (`--out viz`, `figures/`, `report/` pass); switch to an allowlist (viz/demo or a temp dir) | Hoang | done | wip/phase-4-hoang: only a viz/demo* folder is allowed |
| 22 | viz/app.js:103, 265: `g.outcome` and the condition go into markup without `esc()` (local data, low risk) | Artem | done | pre-main review m6 |
| 23 | Optional 3 to 5 minute video demo | - | open | docs/apart/Guidelines.md:40, report/SUBMISSION_CHECKLIST.md:15 |
| 24 | `python -m tools.validate_e runs` (no --config) pools smoke and pilot A/E games: on the real runs Haiku prints PASS 0.277 while the preregistered pilot-only gate is FAIL 0.111. Default is locked R13; add a visible warning | Adam (Claude) | done | wip/phase-4-final: WARNING line naming the pooled configs and `--config espion_pilot` |
| 25 | results/defenses.md showed "Collusion removed" = 0 and 0/0 cells for the monitor and ethics, which never ran (credit cap); no "not run" mark | Adam (Claude) | done | wip/phase-4-final: tools/score_defenses.py prints a NOT RUN line and n/a cells; JSON unchanged. Committed results/defenses.md NOT regenerated (QUESTIONS #31) |
| 26 | Standalone score_detectors, sensitivity, monitor_view keep the games that run_all_deviations.json excludes (real runs: 40 games incl. 10 Haiku pilot vs 30 in results/detectors.json) | Adam (Claude) | done | wip/phase-4-final: --deviations option (off by default); `score_detectors runs out --deviations run_all_deviations.json` gives byte-identical detectors.json/.md to results/ |
