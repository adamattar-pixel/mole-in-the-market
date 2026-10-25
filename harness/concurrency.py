"""Helpers for running the games of a step concurrently (run_batch workers > 1) and for retrying transient
HTTP and network errors. harness/clients.py is not changed: everything here wraps a client.

Budget bound (R17) with W workers: a call is sent only after every cap was checked under a lock and found not
crossed, and its cost is added under the same lock as soon as it returns. When one call crosses a cap, at
most W - 1 other calls are already in flight; they finish, are added, and no new call is sent. So the spend
of a cap is at most cap + W x (max cost of one call), against cap + 1 x (max cost of one call) when sequential.
The games in progress when a cap is hit are dropped (no log), as in the sequential run. Their partial
spend is written to _spend.jsonl and counts toward the cap on the next run (up to W games instead of 1).
"""
import copy
import http.client
import socket
import threading
import time
import urllib.error

from harness.clients import BudgetExceeded, BudgetTracker

RETRY_ATTEMPTS = 5
RETRY_BASE_DELAY = 2.0
RETRY_MAX_DELAY = 60.0
_sleep = time.sleep


class ConcurrentBudget(BudgetTracker):
    """BudgetTracker whose add() is atomic, plus check(): refuse a new call once the cap was crossed."""

    def __init__(self, cap_usd):
        super().__init__(cap_usd)
        self._lock = threading.Lock()

    def add(self, cost_usd):
        with self._lock:
            self.total += float(cost_usd)
            if self.total > self.cap:
                raise BudgetExceeded(f"spent {self.total:.4f} USD > cap {self.cap:.4f} USD")

    def check(self):
        with self._lock:
            if self.total > self.cap:
                raise BudgetExceeded(f"spent {self.total:.4f} USD > cap {self.cap:.4f} USD: no new call")


class _Wrap:
    def __init__(self, inner):
        self.inner = inner

    @property
    def is_mock(self):
        return getattr(self.inner, "is_mock", True)

    @property
    def last_call(self):
        return getattr(self.inner, "last_call", None)


def fork_client(client):
    """A per-game copy of the client, so last_call (provenance) is never shared between threads.
    Wrappers fork their inner client; a plain client is shallow-copied (its price table stays shared)."""
    fork = getattr(client, "fork", None)
    return fork() if callable(fork) else copy.copy(client)


class GuardedClient(_Wrap):
    """Checks every budget (and a stop event) before each call: no call is sent once a cap was crossed."""

    def __init__(self, inner, budgets, stop=None):
        super().__init__(inner)
        self.budgets, self.stop = list(budgets), stop

    def complete(self, messages, model, seed, **settings):
        if self.stop is not None and self.stop.is_set():
            raise BudgetExceeded("batch stopped: no new call")
        for b in self.budgets:
            check = getattr(b, "check", None)
            if check is not None:
                check()
        return self.inner.complete(messages, model, seed, **settings)


_TRANSIENT = (TimeoutError, socket.timeout, ConnectionResetError, ConnectionRefusedError,
              http.client.RemoteDisconnected, http.client.IncompleteRead)


def _retryable(exc):
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code == 429 or 500 <= exc.code <= 599
    if isinstance(exc, urllib.error.URLError):
        return isinstance(exc.reason, _TRANSIENT)
    return isinstance(exc, _TRANSIENT)


def _retry_after(exc):
    try:
        v = float((exc.headers or {}).get("Retry-After"))
    except (TypeError, ValueError):
        return None
    return v if v >= 0 else None


class RetryingClient(_Wrap):
    """Bounded retry of HTTP 429 and 5xx and of transient network errors: socket timeouts, connection reset or
    refused, RemoteDisconnected, IncompleteRead, and a URLError wrapping one of them. No cost is charged for a
    failed request: the client raises before returning a cost, and only the successful attempt's cost is
    returned. Delay before retry k (k = 0, 1, ...): Retry-After if the server sent it, else
    base_delay x 2^k, capped at max_delay. Other errors and the last failure are raised unchanged.
    last_retries is the retry count of the last call (run_game adds it to the provenance when > 0)."""

    def __init__(self, inner, attempts=RETRY_ATTEMPTS, base_delay=RETRY_BASE_DELAY, max_delay=RETRY_MAX_DELAY,
                 sleep=None):
        super().__init__(inner)
        if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 1:
            raise ValueError("attempts must be an integer >= 1")
        self.attempts, self.base_delay, self.max_delay, self.sleep = attempts, base_delay, max_delay, sleep
        self.last_retries = 0

    def complete(self, messages, model, seed, **settings):
        self.last_retries = 0
        for k in range(self.attempts):
            self.last_retries = k
            try:
                out = self.inner.complete(messages, model, seed, **settings)
            except Exception as exc:
                if not _retryable(exc) or k == self.attempts - 1:
                    raise
                after = _retry_after(exc) if isinstance(exc, urllib.error.HTTPError) else None
                delay = min(self.max_delay, after if after is not None else self.base_delay * 2 ** k)
                (self.sleep or _sleep)(float(delay))
                continue
            return out
