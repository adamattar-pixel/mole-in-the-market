"""R22 viz export, R23 consistency with labels.csv, R27 report figure (game grid)."""

CONDITION_NAMES = {}

OUTCOME_COLORS = {}


def outcome(say, do):
    raise NotImplementedError


def export_viz(logs, label_rows, viz_dir, texts, prereg_path, source_checksum, generated_at):
    raise NotImplementedError


def check_consistency(labels_csv, games_csv, runs_dir):
    raise NotImplementedError


def make_game_grid(games_csv, out_pdf):
    raise NotImplementedError
