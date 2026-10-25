# Reproducibility check on a Windows clone (2026-10-25, branch wip/phase-4-adam-numbers)
Question: does `reproduce` on the committed logs (runs/) give byte for byte the committed results, on another OS
than the one that made them (macOS)? No API call, no key; outputs written to a scratch folder, compared with `cmp`.

## Command (same as C1 in docs/team-artem/RESULTS_SUMMARY.md, with D = this repo)
```
python -c "import json; from tools.reproduce import reproduce, PREREG_CONFIGS; ex=set(json.load(open('run_all_deviations.json'))[0]['excluded_game_ids']); reproduce('runs','<scratch>/results',viz_dir='<scratch>/viz',figures_dir='<scratch>/figures',configs=PREREG_CONFIGS,include_mock=False,exclude_ids=ex)"
```

## Before the fix (code at 16e1e5c)
- Tables and numbers: identical once line ends are ignored (tables.md, summary.json, detectors, defenses, labels.csv).
- Bytes: different. Two causes, both line ends:
  1. git on Windows (core.autocrlf) checked out the logs of runs/ with CRLF, so the sha256 of all 44 logs in results/checksums.txt did not match (the repository itself stores them with LF: `git ls-files --eol` -> i/lf).
  2. `Path.write_text()` in text mode writes CRLF on Windows, so results/*.json, *.md, checksums.txt and viz/data/meta.json differed from the macOS outputs.

## Fix (tests first)
- `.gitattributes`: `* text=auto eol=lf` (PDF and PNG binary). Every working copy is byte-identical to the repository. Tests locked first: tests/test_lf_portability.py.
- The reproduce chain writes with `newline="\n"` (tools/reproduce.py, tools/score_detectors.py, tools/score_defenses.py, harness/vizexport.py). Test locked first: tests/test_lf_outputs.py. Mutation (one write without newline) -> red.
- viz/demo regenerated: its meta now records the hash of the frozen LF PREREGISTRATION.md (7bafce4b...), equal to the hash of the git blob.
- Existing Windows clones keep their CRLF copies until the files are checked out again (git skips files it thinks unchanged). Fresh clones are fine.

## After the fix (code at the fix commit)
| Output | Same bytes as committed |
|---|---|
| results/tables.md, summary.json, labels.csv, detectors.json, detectors.md, defenses.json, defenses.md | yes |
| results/checksums.txt (44 input logs + outputs) | yes |
| viz/data/games.csv, rounds.csv, messages.csv | yes |
| viz/data/meta.json, data.js | only `generated_at` differs (it is the commit date of HEAD, by design) |
| figures/game_grid.pdf | no: matplotlib and fonts differ between machines (not in checksums.txt) |

Conclusion: every preregistered number reproduces exactly on Windows from the committed logs, with no key and no network.

## Not fixed here (other owners' claimed files, noted in OPEN_ISSUES #19)
Text writes without `newline="\n"` remain in harness/runlog.py (game logs: a log written on Windows would contain
CRLF), harness/runner.py, tools/run_all.py, tools/price_paths.py, tools/monitor_view.py, tools/sensitivity.py,
tools/think_view.py, tools/insight_checks.py, tools/artem_results_extras.py.
