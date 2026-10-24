# Changelog
All notable changes to this project. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
The project has no version numbers; sections are named after the git tags. All dates are 2026-10-24
(sprint day 2) unless noted. Requirement ids (Rxx) are in SPEC.md, decisions (Dxx) in ops/DECISIONS.md.

## [Unreleased]
On `wip/phase-4`, PR #1 (`artem-owner-approval`) and `artem-ops-reorg`. No real run yet (H2).

### Added
- Exploratory analyses, tests first: seller memory arm (opt-in, writes `runs_exploratory/memory/`), say/do sensitivity grid (`tools/sensitivity.py`), message vs action monitor table (`tools/monitor_view.py`), price path and do-window price shift figures (`tools/price_paths.py`).
- Client settings: temperature, reasoning control and provider provenance in every log.
- R28-R30: rule-based detectors D1 price level, D2 message, D3 lag dependence, scored against the spy ground truth with Wilson intervals; `reproduce` writes the detector tables.
- R31-R35: rule monitor with matched B_MON, C_MON, D_MON configs; ethics condition B_ETH; defenses comparison on matched triples; real addendum runs refused unless the addendum is FROZEN.
- R36: `tools/run_all`, the one-command pipeline (E gate with one fallback then plan B, global budget, resume, `--dry`, `--exploratory`, `--o1`), `tools/score_defenses.py`, and RUNBOOK_REAL_RUNS.md.
- Report skeleton with headings and `[RESULT: ...]` placeholders, no prose (D21).
- Team docs in docs/team-artem/: independent audit passes 1 and 2, pre-run review, related work, novelty, model choice and cost, competitor scan.
- `validate_e --config` filter (QUESTIONS #23).
- Provider routing: optional per-family `provider` block (OpenRouter routing object), logged as `provider_routing`, checked on resume and across pooled steps; real configs pin Llama 3.3 to Novita bf16 and Anthropic models to Anthropic (docs/team-artem/FIXES_CLIENT.md).
- EXPLORATORY THINK arm: gpt-oss-120b with logged raw reasoning traces, `<think>`-safe reply parsing from content only, `tools/think_view.py` heuristic keyword coder and trace export, `run_all --think`, 4-game showcase config (docs/team-artem/THINK_ARM.md).
- Cost guard: each real call is charged max(reported cost, tokens x price from `configs/prices.yaml`); a model with no price is refused.
- ops/ folder: STATE.md (single resume point), CLAIMS.md (coordination board, branch and PR rules), OPEN_ISSUES.md (backlog), README.md (map), and `tools/check_ops.py`. This changelog.

### Changed
- `reproduce` excludes mock and non-core games by default and reports the exclusions.
- Abstract rule in R19 `check_submission`: 150 to 250 words (live sprint page), via an owner-approved test(fix).
- Locked tests that asserted the `tbd` placeholder state now run on placeholder copies of the configs (owner-approved test(fix), QUESTIONS #21).
- Process docs moved to ops/: PROGRESS, PLAN, QUESTIONS, AUDIT, TRACEABILITY, HANDOFF, and docs/context/DECISIONS.md. HANDOFF.md is now a historical snapshot. CLAUDE.md addresses the owner (Artem) in English and points to ops/.

### Fixed
- Review majors M1-M4: per-config budget kept across reruns; resume refused when logged games used other settings; run_all keeps each step's family settings and checks pooled steps match; `reproduce` writes the defenses tables. Minors m2 (reasoning effort `max`, effort with max_tokens refused) and m4 (real-mode root = repo).
- Family label `<provider>-fb` accepted for fallbacks.

## [handoff-artem-1]
### Changed
- Ownership handed from Adam Attar to Artem (D22): HANDOFF.md, ownership and identity rules in CLAUDE.md and CONTRIBUTING.md, README authors and run commands, report/AUTHORS.md.

## [addendum-frozen]
### Added
- Gap tests for phases 0-3 and docs/context/TEST_ORDER_REPORT.md; spy_start below 1 rejected.
- Phase 4 without API: dry, smoke, pilot and core configs, a deterministic mock client, `tools/run.py`, cost per game, guards (mock never writes to runs/, real runs refused while model ids are `tbd`).
- R19 `tools/check_submission.py` (abstract, appendix title, authors, title, links).
- R24-R25 replay page (viz/index.html for real data, viz/demo.html with a DEMO DATA banner), offline page checker, synthetic demo data.
- Post-freeze plan: SPEC R28-R36, decisions D16-D21, Phase 8 cut (D17).
- PREREGISTRATION_ADDENDUM.md (monitor rule, ethics sentence, detector definitions and thresholds, H5-H7), frozen at 8b7b5a1.

## [prereg-frozen]
### Changed
- PREREGISTRATION.md frozen on the owner's order (D15) at d5e7ebc; only status words changed. Hash recorded in e95853a.

## [gate-3]
### Added
- R12-R17: write-once game logs (model, seed, config hash, git commit), mock and OpenRouter clients, budget tracker with a global stop, game runner with real-run guards, E validation script, `labels.csv`, `reproduce` (tables, summary, checksums; no key, no network).
- R22, R23, R27: viz data export, consistency check, game grid figure.
- CONTRIBUTING.md and the wip push rules (D12); owner decisions D1-D14 logged and QUESTIONS 1-9 answered.
### Fixed
- Approved test(fix) cef08e3: the invalid-reply pipeline test expects 2 invalid responses (D3).

## [gate-2]
### Added
- R01-R11 from tests locked at 5c52047: logit and linear demand with Nash and joint monopoly prices; scripted spy (one message at spy_start); conditions from the preregistration texts (B and B_T differ only by the label); response validation; say/do definitions, false positives, game-level rates, permutation base rate, Wilson intervals.
- PROPOSED preregistration texts, definition details and E threshold (not frozen at that point).

## [gate-0]
### Added
- pytest runner, requirements.txt, pyproject.toml, harness package skeleton; questions on file inconsistencies (QUESTIONS 1-8).

## [preexisting-baseline]
### Added
- Scaffolding only: CLAUDE.md, SPEC.md, PLAN.md, a PREREGISTRATION.md draft, audit and traceability files, Apart sprint docs, CI workflow, commit-msg hook, `/audit` and `/gate` commands. No harness code (the harness was written during the sprint, D4).

[Unreleased]: https://github.com/adamattar-pixel/mole-in-the-market/compare/handoff-artem-1...wip/phase-4
[handoff-artem-1]: https://github.com/adamattar-pixel/mole-in-the-market/compare/addendum-frozen...handoff-artem-1
[addendum-frozen]: https://github.com/adamattar-pixel/mole-in-the-market/compare/prereg-frozen...addendum-frozen
[prereg-frozen]: https://github.com/adamattar-pixel/mole-in-the-market/compare/gate-3...prereg-frozen
[gate-3]: https://github.com/adamattar-pixel/mole-in-the-market/compare/gate-2...gate-3
[gate-2]: https://github.com/adamattar-pixel/mole-in-the-market/compare/gate-0...gate-2
[gate-0]: https://github.com/adamattar-pixel/mole-in-the-market/compare/preexisting-baseline...gate-0
[preexisting-baseline]: https://github.com/adamattar-pixel/mole-in-the-market/tree/preexisting-baseline
