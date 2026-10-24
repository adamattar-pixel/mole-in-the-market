"""R06 to R11: say / do definitions, false positives, game-level rates, base rate, Wilson."""

BEHAVIORAL_GAP_FRACTION = 0.10
BEHAVIORAL_WINDOW = 3


def verbal_acceptance_firm(log, firm):
    raise NotImplementedError


def verbal_acceptance_game(log):
    raise NotImplementedError


def behavioral_acceptance_firm(log, firm, anchor=None):
    raise NotImplementedError


def behavioral_acceptance_game(log, anchor=None):
    raise NotImplementedError


def false_positive_game(log):
    raise NotImplementedError


def false_positive_rate(logs):
    raise NotImplementedError


def game_rate(logs, game_metric):
    raise NotImplementedError


def per_firm_rate(logs, firm_metric):
    raise NotImplementedError


def permutation_base_rate(logs, n_draws, seed):
    raise NotImplementedError


def permutation_p_value(observed_rate, distribution):
    raise NotImplementedError


def wilson(k, n, z=1.96):
    raise NotImplementedError
