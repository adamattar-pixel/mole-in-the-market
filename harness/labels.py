"""R14: labels.csv, one line per game."""

LABEL_COLUMNS = ("game_id", "family", "seed", "condition", "offer_form", "trust_label",
                 "verbal", "behavioral", "false_positive", "base_rate")


def make_labels(logs, n_draws=1000, seed=0):
    raise NotImplementedError


def write_labels_csv(rows, path):
    raise NotImplementedError
