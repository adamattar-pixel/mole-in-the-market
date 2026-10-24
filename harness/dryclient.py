"""Deterministic mock client for dry runs only (never used by a real run).

Replies are pseudo-random but fixed by (model, seed, prompt): same config -> same prices.
It only exercises the pipeline; its prices mean nothing and are never results.
"""
import hashlib
import json
import random

from harness.clients import MockClient
from harness.config import GameConfig


def make_dry_client(cfg):
    gc = GameConfig.from_dict(cfg)
    lo, hi = gc.nash_price * 0.9, gc.monopoly_price * 1.1

    def reply(messages, model, seed):
        user = messages[-1]["content"]
        h = hashlib.sha256(f"{model}|{seed}|{user}".encode("utf-8")).hexdigest()
        rng = random.Random(int(h[:16], 16))
        price = round(rng.uniform(lo, hi), 4)
        response = rng.choice(["accept", "decline"]) if "Message received this round" in user else "no_message"
        return json.dumps({"price": price, "response_to_message": response})

    return MockClient(reply, cost_per_call=float(cfg.get("mock_cost_per_call", 0.0)))
