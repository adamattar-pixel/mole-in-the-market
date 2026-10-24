"""Model clients. MockClient is for tests and dry runs only; real runs use OpenRouterClient. R17 budget."""
import json
import math
import os
import urllib.request
from pathlib import Path

import yaml

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
PRICES_PATH = Path(__file__).resolve().parent.parent / "configs" / "prices.yaml"


class BudgetExceeded(RuntimeError):
    pass


class MissingAPIKey(RuntimeError):
    pass


class MissingPrice(RuntimeError):
    pass


def _price(v):
    return not isinstance(v, bool) and isinstance(v, (int, float)) and math.isfinite(v) and v > 0


def load_prices(path=None):
    """configs/prices.yaml -> {model id: {"input": USD per 1M, "output": USD per 1M}}, every price > 0."""
    data = yaml.safe_load(Path(path or PRICES_PATH).read_text(encoding="utf-8"))
    out = {}
    for model, entry in (data.get("models") or {}).items():
        if not isinstance(entry, dict) or set(entry) != {"input", "output"} or not all(map(_price, entry.values())):
            raise ValueError(f"price of {model!r} must be {{input: USD per 1M > 0, output: USD per 1M > 0}}: {entry!r}")
        out[model] = {"input": float(entry["input"]), "output": float(entry["output"])}
    return out


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

    def complete(self, messages, model, seed, **settings):
        return self.reply_fn(messages, model, seed), self.cost_per_call


class OpenRouterClient:
    """Real client. The key is read from the OPENROUTER_API_KEY environment variable at call time.

    temperature and reasoning are sent only when not None (None = provider default, as before).
    After each call, last_call holds the provenance: served model, provider, raw usage, reasoning tokens.
    With a price table (load_prices), each call is charged max(usage.cost, tokens x price): under BYOK usage.cost
    is only OpenRouter's fee. last_call then adds cost_reported, cost_computed, cost_charged and cost_source
    ("usage_cost" or "token_price"). A model with no price is refused before the request.
    """
    is_mock = False

    def __init__(self, timeout=60, prices=None):
        self.timeout = timeout
        self.prices = prices
        self.last_call = None

    def complete(self, messages, model, seed, temperature=None, reasoning=None):
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise MissingAPIKey("OPENROUTER_API_KEY is not set")
        self.last_call = None
        if self.prices is not None and model not in self.prices:
            raise MissingPrice(f"no price for {model!r} in configs/prices.yaml: refused before any request (R17)")
        payload = {"model": model, "messages": messages, "seed": seed, "usage": {"include": True}}
        if temperature is not None:
            payload["temperature"] = temperature
        if reasoning is not None:
            payload["reasoning"] = reasoning
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(OPENROUTER_URL, data=body, method="POST", headers={
            "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"] or ""
        usage = data.get("usage")
        details = (usage or {}).get("completion_tokens_details") or {}
        self.last_call = {"served_model": data.get("model"), "provider": data.get("provider"),
                          "usage": usage, "reasoning_tokens": details.get("reasoning_tokens")}
        cost = (usage or {}).get("cost")
        if cost is None or not math.isfinite(float(cost)):
            # Never run with untracked spend (R17).
            raise RuntimeError("OpenRouter response has no usage cost")
        cost = float(cost)
        if self.prices is None:
            return text, cost
        tokens = [usage.get(k) for k in ("prompt_tokens", "completion_tokens")]
        if not all(not isinstance(n, bool) and isinstance(n, int) and n >= 0 for n in tokens):
            raise RuntimeError("OpenRouter response has no token counts: the BYOK cost cannot be checked")
        price = self.prices[model]
        computed = (tokens[0] * price["input"] + tokens[1] * price["output"]) / 1e6
        charged = max(cost, computed)
        self.last_call.update(cost_reported=cost, cost_computed=computed, cost_charged=charged,
                              cost_source="usage_cost" if cost >= computed else "token_price")
        return text, charged
