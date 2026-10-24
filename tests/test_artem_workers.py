"""--workers N: the games of a step run concurrently (harness/runner.py run_batch, harness/concurrency.py).

Owner request 2026-10-24 (about 270 real games of 1 to 2 min each before the Sunday-noon freeze).
- workers=1 is the old sequential loop; workers>1 gives byte-identical logs (games are independent).
- Thread-safe budget caps: a call is never sent once a cap was crossed; overspend is bounded by the calls in
  flight, so spend <= cap + workers x (max cost of one call).
- Resume and skip of logged games still work; results come back sorted by game id.
- A worker exception drops only its own game (no log) and is reported (BatchFailed), the other games finish.
- HTTP 429 and 5xx get a bounded retry with exponential backoff (RetryingClient wraps the client).
Hand values: helpers3.cfg has 4 rounds x 2 firms = 8 calls per game; at 0.25 USD per call a game is 2.0 USD.
"""
import copy
import io
import json
import threading
import time
import urllib.error
from pathlib import Path

import pytest

from harness.clients import BudgetExceeded, MockClient
from harness.runlog import load_logs
from harness.runner import run_batch
from helpers3 import cfg

TEXTS = {
    "status": "PROPOSED",
    "label_sentence": "LABEL[{label}].",
    "neutral_label": "neutral sender",
    "trust_label": "trusted sender",
    "offer_body": "OFFER at {deal_price}.",
    "hint_body": "HINT near {deal_price}.",
    "harmless_body": "HARMLESS request.",
    "e_instruction": "E-ALLOWED.",
    "e_threshold_gap_fraction": 0.25,
    "behavioral_gap_fraction": 0.10,
    "behavioral_window": 3,
}
SEEDS = [1, 2, 3, 4, 5, 6]
CONDS = ["A", "B", "D"]


def big_cfg(**over):
    return cfg(seeds=SEEDS, conditions=CONDS, **over)


def ids(c):
    return sorted(f"{c['name']}__{f['family']}__{k}__s{s}" for f in c["families"] for k in c["conditions"]
                  for s in c["seeds"])


class Counting(MockClient):
    """Mock with a lock-protected call counter shared by its copies (test double, never under test)."""

    def __init__(self, cost=0.0, fail_seed=None, barrier=None, delay=0.0):
        self.calls = []
        self.lock = threading.Lock()
        self.fail_seed, self.barrier, self.delay = fail_seed, barrier, delay
        super().__init__(self._reply, cost_per_call=cost)

    def _reply(self, messages, model, seed):
        with self.lock:
            self.calls.append(seed)
        if self.barrier is not None:
            self.barrier.wait(timeout=5)  # BrokenBarrierError unless `parties` games run at the same time
        if self.delay:
            time.sleep(self.delay)
        if seed == self.fail_seed:
            raise RuntimeError(f"boom in seed {seed}")
        return json.dumps({"price": 4.0 + 0.1 * seed, "response_to_message": "accept"})


def files(d):
    return {p.name: p.read_bytes() for p in sorted(Path(d).glob("*.json"))}


# ---------- identical logs, order, concurrency ----------

def test_workers_logs_byte_identical_to_sequential(tmp_path):
    c = big_cfg()
    one = run_batch(c, Counting(), tmp_path / "w1", texts=TEXTS, git_commit="abc")
    four = run_batch(c, Counting(), tmp_path / "w4", texts=TEXTS, git_commit="abc", workers=4)
    a, b = files(tmp_path / "w1"), files(tmp_path / "w4")
    assert len(a) == len(SEEDS) * len(CONDS) == 18
    assert a == b
    assert [g["game_id"] for g in four] == ids(c)
    assert sorted(g["game_id"] for g in one) == ids(c)


def test_workers_one_keeps_the_sequential_order(tmp_path):
    c = big_cfg()
    got = [g["game_id"] for g in run_batch(c, Counting(), tmp_path, texts=TEXTS, git_commit="abc")]
    expected = [f"t__fam__{k}__s{s}" for k in CONDS for s in SEEDS]  # expand_games order: condition, seed
    assert got == expected


def test_workers_really_run_games_concurrently(tmp_path):
    # 4 parties: the barrier only opens if 4 games call the model at the same time
    c = cfg(seeds=[1, 2, 3, 4], conditions=["A"])
    client = Counting(barrier=threading.Barrier(4))
    done = run_batch(c, client, tmp_path, texts=TEXTS, git_commit="abc", workers=4)
    assert len(done) == 4 and len(client.calls) == 4 * 8


def test_workers_value_is_checked(tmp_path):
    for bad in (0, -1, 1.5, True, "4"):
        with pytest.raises(ValueError, match="workers"):
            run_batch(cfg(), Counting(), tmp_path, texts=TEXTS, git_commit="abc", workers=bad)
    assert not list(tmp_path.glob("*.json"))


# ---------- resume ----------

def test_workers_resume_skips_logged_games(tmp_path):
    c = big_cfg()
    run_batch(cfg(seeds=SEEDS[:2], conditions=CONDS), Counting(), tmp_path, texts=TEXTS, git_commit="abc")
    before = files(tmp_path)
    assert len(before) == 6
    client = Counting()
    new = run_batch(c, client, tmp_path, texts=TEXTS, git_commit="abc", workers=4)
    assert len(new) == 12 and len(client.calls) == 12 * 8
    assert {s for s in client.calls} == set(SEEDS[2:])
    after = files(tmp_path)
    assert all(after[k] == v for k, v in before.items())  # write-once: old logs untouched
    again = Counting()
    assert run_batch(c, again, tmp_path, texts=TEXTS, git_commit="abc", workers=4) == [] and again.calls == []


# ---------- worker exception ----------

def test_worker_exception_drops_only_its_game(tmp_path):
    from harness.runner import BatchFailed
    c = big_cfg()
    with pytest.raises(BatchFailed) as ei:
        run_batch(c, Counting(fail_seed=3), tmp_path, texts=TEXTS, git_commit="abc", workers=4)
    failed = sorted(i for i in ids(c) if i.endswith("__s3"))
    assert sorted(ei.value.failed) == failed and len(failed) == 3
    assert "boom in seed 3" in ei.value.failed[failed[0]]
    assert [g["game_id"] for g in ei.value.done] == [i for i in ids(c) if i not in failed]
    logged = sorted(p.stem for p in tmp_path.glob("*.json"))
    assert logged == [i for i in ids(c) if i not in failed]
    for f in failed:
        assert f in str(ei.value)
    # the failed games are not complete: a rerun runs exactly them
    client = Counting()
    run_batch(c, client, tmp_path, texts=TEXTS, git_commit="abc", workers=4)
    assert len(client.calls) == 3 * 8 and set(client.calls) == {3}


# ---------- budget ----------

def test_workers_per_config_cap_bounded_overspend(tmp_path):
    # cap 5.0 USD = 2.5 games; 4 workers x 0.25 USD per call in flight at most
    workers, per_call, cap = 4, 0.25, 5.0
    client = Counting(cost=per_call, delay=0.002)
    with pytest.raises(BudgetExceeded):
        run_batch(big_cfg(budget_usd=cap), client, tmp_path, texts=TEXTS, git_commit="abc", workers=workers)
    spent = len(client.calls) * per_call
    assert cap < spent <= cap + workers * per_call
    logs = load_logs(tmp_path)
    assert sum(g["cost_usd"] for g in logs) <= cap
    assert all(len(g["rounds"]) == 4 for g in logs)  # only complete games are logged


def test_concurrent_budget_is_thread_safe():
    from harness.concurrency import ConcurrentBudget
    b = ConcurrentBudget(1e9)

    def work():
        for _ in range(20000):
            b.add(1.0)

    ts = [threading.Thread(target=work) for _ in range(8)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert b.total == 8 * 20000


def test_concurrent_budget_check_refuses_after_cap():
    from harness.concurrency import ConcurrentBudget
    b = ConcurrentBudget(1.0)
    b.check()
    b.add(1.0)  # equal to the cap: allowed, as BudgetTracker
    b.check()
    with pytest.raises(BudgetExceeded):
        b.add(0.5)
    with pytest.raises(BudgetExceeded):
        b.check()
    assert b.total == pytest.approx(1.5)


def test_guarded_client_sends_nothing_once_stopped():
    from harness.concurrency import ConcurrentBudget, GuardedClient
    b = ConcurrentBudget(1.0)
    inner = Counting(cost=0.75)
    g = GuardedClient(inner, [b])
    g.complete([{"role": "user", "content": "x"}], "m", 1)
    with pytest.raises(BudgetExceeded):
        b.add(0.75)
    with pytest.raises(BudgetExceeded):
        g.complete([{"role": "user", "content": "x"}], "m", 1)
    assert len(inner.calls) == 1


# ---------- provenance stays with its own game ----------

class Provenance(MockClient):
    """Sets last_call per call, like OpenRouterClient (shared between threads unless forked per game)."""
    is_mock = True

    def __init__(self):
        super().__init__(None)
        self.last_call = None

    def complete(self, messages, model, seed, **settings):
        self.last_call = {"seed": seed, "provider": "p"}
        time.sleep(0.001)
        return json.dumps({"price": 4.0, "response_to_message": "accept"}), 0.0


def test_workers_provenance_is_not_mixed_between_games(tmp_path):
    for g in run_batch(big_cfg(), Provenance(), tmp_path, texts=TEXTS, git_commit="abc", workers=6):
        for r in g["rounds"]:
            for f in r["firms"].values():
                assert f["provenance"]["seed"] == g["seed"], g["game_id"]


def test_fork_client_gives_independent_last_call():
    from harness.concurrency import fork_client
    c = Provenance()
    a, b = fork_client(c), fork_client(c)
    a.complete([], "m", 1)
    b.complete([], "m", 2)
    assert a.last_call["seed"] == 1 and b.last_call["seed"] == 2 and c.last_call is None


# ---------- retry on 429 and 5xx ----------

def http_error(code, retry_after=None):
    headers = {"Retry-After": str(retry_after)} if retry_after is not None else {}
    return urllib.error.HTTPError("https://example.invalid", code, "err", headers, io.BytesIO(b""))


class Flaky:
    is_mock = False

    def __init__(self, codes):
        self.codes, self.calls, self.last_call = list(codes), 0, None

    def complete(self, messages, model, seed, **settings):
        self.calls += 1
        if self.codes:
            raise http_error(self.codes.pop(0))
        self.last_call = {"ok": True}
        return "text", 0.5


def test_retry_429_and_5xx_then_success():
    from harness.concurrency import RetryingClient
    sleeps = []
    inner = Flaky([429, 503, 500])
    r = RetryingClient(inner, attempts=5, base_delay=1.0, max_delay=30.0, sleep=sleeps.append)
    assert r.complete([], "m", 1) == ("text", 0.5)
    assert inner.calls == 4
    assert sleeps == [1.0, 2.0, 4.0]  # 1 x 2^k
    assert r.last_call == {"ok": True} and r.is_mock is False


def test_retry_is_bounded():
    from harness.concurrency import RetryingClient
    sleeps = []
    inner = Flaky([429] * 10)
    r = RetryingClient(inner, attempts=3, base_delay=1.0, max_delay=30.0, sleep=sleeps.append)
    with pytest.raises(urllib.error.HTTPError):
        r.complete([], "m", 1)
    assert inner.calls == 3 and sleeps == [1.0, 2.0]


def test_retry_not_on_client_errors():
    from harness.concurrency import RetryingClient
    for code in (400, 401, 402, 403, 404):
        inner = Flaky([code])
        sleeps = []
        with pytest.raises(urllib.error.HTTPError):
            RetryingClient(inner, attempts=5, sleep=sleeps.append).complete([], "m", 1)
        assert inner.calls == 1 and sleeps == []


def test_retry_honours_retry_after_capped():
    from harness.concurrency import RetryingClient
    sleeps = []

    class After(Flaky):
        def complete(self, messages, model, seed, **settings):
            self.calls += 1
            if self.calls == 1:
                raise http_error(429, retry_after=7)
            if self.calls == 2:
                raise http_error(429, retry_after=999)
            return "t", 0.0

    RetryingClient(After([]), attempts=4, base_delay=1.0, max_delay=30.0, sleep=sleeps.append).complete([], "m", 1)
    assert sleeps == [7.0, 30.0]


def test_run_batch_retries_in_the_runner(tmp_path, monkeypatch):
    from harness import concurrency
    monkeypatch.setattr(concurrency, "_sleep", lambda s: None)
    state = {"n": 0}
    lock = threading.Lock()

    def fn(messages, model, seed):
        with lock:
            state["n"] += 1
            n = state["n"]
        if n in (3, 10):
            raise http_error(429)
        return json.dumps({"price": 4.0, "response_to_message": "accept"})

    done = run_batch(cfg(seeds=[1, 2]), MockClient(fn), tmp_path, texts=TEXTS, git_commit="abc", workers=2)
    assert len(done) == 2 and state["n"] == 2 * 8 + 2


# ---------- tools/run.py --workers ----------

def test_tools_run_workers_flag(tmp_path, capsys):
    import yaml
    from tools import run
    c = big_cfg(name="wcli", out_dir="dry_runs/wcli")
    p = tmp_path / "c.yaml"
    p.write_text(yaml.safe_dump(c), encoding="utf-8")
    assert run.main([str(p), "--out-dir", str(tmp_path / "o1")]) == 0
    out1 = capsys.readouterr().out
    assert run.main([str(p), "--out-dir", str(tmp_path / "o4"), "--workers", "4"]) == 0
    out4 = capsys.readouterr().out
    assert out1.replace("o1", "oX") == out4.replace("o4", "oX")
    a, b = files(tmp_path / "o1"), files(tmp_path / "o4")
    assert len(a) == 18
    # git_commit is the repo HEAD in both runs
    assert a == b
