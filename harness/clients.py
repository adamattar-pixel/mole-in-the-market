"""Model clients. MockClient is for tests and dry runs only; real runs use OpenRouterClient. R17 budget."""
import json
import math
import os
import urllib.error
import urllib.request
from pathlib import Path

import yaml

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_TIMEOUT_S = 120  # read timeout per request (was 60); a config sets its own with `timeout_s`
# max_tokens sent when the caller gives none: replies are about 50 chars, so 512 stops a runaway generation;
# a reasoning model needs room for its trace before the reply.
MAX_TOKENS_DEFAULT = 512
MAX_TOKENS_REASONING = 16000
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


def _reasoning_trace(message):
    """Raw reasoning of a response message: {} when the message has none, else reasoning_text (message.reasoning,
    or the joined reasoning.text entries of reasoning_details; None when only summaries or encrypted blocks came
    back) and, when reasoning_details is present, the sorted list of its entry types."""
    details = message.get("reasoning_details")
    out = {}
    if isinstance(details, list) and details:
        out["reasoning_detail_types"] = sorted({str(d.get("type")) for d in details if isinstance(d, dict)})
    raw = message.get("reasoning")
    if isinstance(raw, str) and raw:
        out["reasoning_text"] = raw
    elif "reasoning_detail_types" in out:
        parts = [d["text"] for d in details if isinstance(d, dict) and d.get("type") == "reasoning.text"
                 and isinstance(d.get("text"), str)]
        out["reasoning_text"] = "\n".join(parts) if parts else None
    return out


def _http_message(exc, key):
    """Server body of an HTTP error, with the API key removed. Falls back to the reason phrase."""
    raw = b""
    try:
        raw = exc.read() or b""
    except Exception:
        raw = b""
    detail = raw.decode("utf-8", errors="replace")
    message = str(exc.reason or "")
    parsed = None
    if detail.strip():
        try:
            parsed = json.loads(detail)
        except (json.JSONDecodeError, ValueError):
            parsed = None
    if isinstance(parsed, dict):
        err = parsed.get("error")
        if isinstance(err, dict) and err.get("message"):
            message = str(err["message"])
        elif isinstance(err, str) and err:
            message = err
    elif detail.strip():
        message = detail.strip()
    if key:
        message = message.replace(key, "[redacted]")
    return message[:500]


class OpenRouterClient:
    """Real client. The key is read from the OPENROUTER_API_KEY environment variable at call time.

    temperature, reasoning and provider (OpenRouter's routing object) are sent only when not None (None =
    provider default, as before). The raw reasoning trace, when the response has one, is kept in last_call
    (reasoning_text, reasoning_detail_types) and is never part of the returned reply.
    After each call, last_call holds the provenance: served model, provider, raw usage, reasoning tokens and
    usage.cost_details.upstream_inference_cost (the provider's bill under BYOK; only when present, log only).
    With a price table (load_prices), each call is charged max(usage.cost, tokens x price): under BYOK usage.cost
    is only OpenRouter's fee. last_call then adds cost_reported, cost_computed, cost_charged and cost_source
    ("usage_cost" or "token_price"). A model with no price is refused before the request.
    max_tokens is sent when not None (run_game always gives one: MAX_TOKENS_REASONING when reasoning is set,
    else MAX_TOKENS_DEFAULT, unless the family sets max_tokens); last_call then records it. The response's
    finish_reason is recorded when present ("length" = truncated reply; it is counted invalid only when the truncated text fails to parse, and no call in runs/ was truncated).
    """
    is_mock = False

    def __init__(self, timeout=DEFAULT_TIMEOUT_S, prices=None):
        self.timeout = timeout
        self.prices = prices
        self.last_call = None

    def complete(self, messages, model, seed, temperature=None, reasoning=None, provider=None, max_tokens=None):
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise MissingAPIKey("OPENROUTER_API_KEY is not set")
        self.last_call = None
        if self.prices is not None and model not in self.prices:
            raise MissingPrice(f"no price for {model!r} in configs/prices.yaml: refused before any request (R17)")
        payload = {"model": model, "messages": messages, "seed": seed, "usage": {"include": True}}
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if temperature is not None:
            payload["temperature"] = temperature
        if reasoning is not None:
            payload["reasoning"] = reasoning
        if provider is not None:
            payload["provider"] = provider
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(OPENROUTER_URL, data=body, method="POST", headers={
            "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            # Keep the status code (403 stays 403, so it is still not retried) and put the server
            # text on the error. The key is never copied into that text.
            raise urllib.error.HTTPError(req.full_url, exc.code, _http_message(exc, key),
                                          exc.headers, None) from None
        choice = data["choices"][0]
        message = choice["message"]
        # The reply is `content` only: the reasoning trace is logged, never parsed (THINK_ARM.md).
        text = message.get("content") or ""
        usage = data.get("usage")
        details = (usage or {}).get("completion_tokens_details") or {}
        self.last_call = {"served_model": data.get("model"), "provider": data.get("provider"),
                          "usage": usage, "reasoning_tokens": details.get("reasoning_tokens")}
        if max_tokens is not None:
            self.last_call["max_tokens"] = max_tokens
        if "finish_reason" in choice:
            self.last_call["finish_reason"] = choice["finish_reason"]
        self.last_call.update(_reasoning_trace(message))
        upstream = ((usage or {}).get("cost_details") or {}).get("upstream_inference_cost")
        if upstream is not None:
            self.last_call["upstream_inference_cost"] = float(upstream)
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
