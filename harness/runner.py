"""Game loop and batch runner. R12 logs, R16 design validation, R17 budget stop."""


class RealRunRefused(RuntimeError):
    pass


def model_family(model_id):
    raise NotImplementedError


def validate_config(cfg):
    raise NotImplementedError


def expand_games(cfg):
    raise NotImplementedError


def run_game(cfg, spec, client, texts, budget, runs_dir, git_commit="test"):
    raise NotImplementedError


def run_batch(cfg, client, runs_dir, texts=None, prereg_path=None, git_commit=None):
    raise NotImplementedError
