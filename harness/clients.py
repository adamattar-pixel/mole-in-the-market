"""Model clients. MockClient is for tests and dry runs only; real runs use OpenRouterClient. R17 budget."""
import json
import math
import os
import urllib.request

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class BudgetExceeded(RuntimeError):
    pass


class MissingAPIKey(RuntimeError):
    pass


class BudgetTracker:
    """Global spend counter. Raises BudgetExceeded as soon as the total goes above the cap."""

    def __init__(self, cap_usd):
        if cap_usd <= 0:
            raise ValueError("budget cap must be > 0")
        self.cap = float(cap_usd)
        self.total = 0.0

    def add(self, cost_usd):
        self.total += float(cost_usd)
        if self.total > self.cap:
            raise BudgetExceeded(f"spent {self.total:.4f} USD > cap {self.cap:.4f} USD")


class MockClient:
    """Deterministic fake model. reply_fn(messages, model, seed) -> reply text."""
    is_mock = True

    def __init__(self, reply_fn, cost_per_call=0.0):
        self.reply_fn = reply_fn
        self.cost_per_call = float(cost_per_call)

    def complete(self, messages, model, seed):
        return self.reply_fn(messages, model, seed), self.cost_per_call


class OpenRouterClient:
    """Real client. The key is read from the OPENROUTER_API_KEY environment variable at call time."""
    is_mock = False

    def __init__(self, timeout=60):
        self.timeout = timeout

    def complete(self, messages, model, seed):
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise MissingAPIKey("OPENROUTER_API_KEY is not set")
        body = json.dumps({"model": model, "messages": messages, "seed": seed,
                           "usage": {"include": True}}).encode("utf-8")
        req = urllib.request.Request(OPENROUTER_URL, data=body, method="POST", headers={
            "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"] or ""
        cost = (data.get("usage") or {}).get("cost")
        if cost is None or not math.isfinite(float(cost)):
            # Never run with untracked spend (R17).
            raise RuntimeError("OpenRouter response has no usage cost")
        return text, float(cost)
