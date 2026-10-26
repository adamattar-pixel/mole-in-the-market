# tools/: command-line tools

Everything you run with `python3 -m tools.<name>`: run games (`run.py`, `run_all.py`), rebuild every result from the logs (`reproduce.py`), score detectors and defenses (`score_detectors.py`, `score_defenses.py`), check the positive control (`validate_e.py`), and check the report and numbers (`check_numbers.py`, `check_submission.py`).

The main one is `reproduce.py`: it rebuilds all preregistered tables with no API key.
