"""R29: score the R28 detectors against the spy ground truth (EXPLORATORY, PREREGISTRATION_ADDENDUM.md "Scoring").

Usage: python -m tools.score_detectors runs results_detectors
"""
from harness.detectors import DETECTORS

CORE_CONDITIONS = ("A", "E", "B", "B_T", "C", "D")
PACT_CONDITIONS = ("E", "B", "B_T", "C")
FALSE_ALARM_CONDITIONS = ("A", "D")


def ground_truth(log):
    raise NotImplementedError


def score_detectors(logs, detectors=DETECTORS, n_draws=1000, seed=0):
    raise NotImplementedError


def tables_md(scores):
    raise NotImplementedError


def write_outputs(scores, out_dir):
    raise NotImplementedError


def main(argv=None):
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
