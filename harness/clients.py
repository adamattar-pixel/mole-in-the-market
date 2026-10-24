"""Model clients. MockClient is for tests and dry runs only; real runs use OpenRouterClient. R17 budget."""


class BudgetExceeded(RuntimeError):
    pass


class MissingAPIKey(RuntimeError):
    pass


class BudgetTracker:
    def __init__(self, cap_usd):
        raise NotImplementedError

    def add(self, cost_usd):
        raise NotImplementedError


class MockClient:
    is_mock = True

    def __init__(self, reply_fn, cost_per_call=0.0):
        raise NotImplementedError

    def complete(self, messages, model, seed):
        raise NotImplementedError


class OpenRouterClient:
    is_mock = False

    def __init__(self, timeout=60):
        raise NotImplementedError

    def complete(self, messages, model, seed):
        raise NotImplementedError
