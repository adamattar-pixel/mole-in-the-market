"""R12: complete, immutable game logs in runs/."""

REQUIRED_FIELDS = ("game_id", "condition", "seed", "models", "family", "config_hash", "git_commit",
                   "cost_usd", "mock", "spy_start", "n_rounds", "nash_price", "monopoly_price",
                   "deal_price", "rounds")


def config_hash(cfg):
    raise NotImplementedError


def current_git_commit():
    raise NotImplementedError


def write_game_log(log, runs_dir):
    raise NotImplementedError


def load_logs(runs_dir):
    raise NotImplementedError
