"""R13: report PASS or FAIL of the positive control E for each model family.

Usage: python -m tools.validate_e [runs_dir] [--prereg PREREGISTRATION.md]
Exit code 0 only if every family passes.
"""
import argparse

from harness.conditions import PREREG_PATH, load_prereg_texts
from harness.runlog import load_logs
from harness.validation import e_validation


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_dir", nargs="?", default="runs")
    ap.add_argument("--prereg", default=str(PREREG_PATH))
    a = ap.parse_args(argv)
    threshold = load_prereg_texts(a.prereg)["e_threshold_gap_fraction"]
    res = e_validation(load_logs(a.runs_dir), threshold)
    for fam, r in res.items():
        eff = "n/a" if r["effect_gap_fraction"] is None else f"{r['effect_gap_fraction']:.3f}"
        print(f"{fam}: {'PASS' if r['pass'] else 'FAIL'} (effect {eff} of the gap, threshold {threshold}, "
              f"A games {r['n_A']}, E games {r['n_E']})")
    if not res:
        print("no games")
    return 0 if res and all(r["pass"] for r in res.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
