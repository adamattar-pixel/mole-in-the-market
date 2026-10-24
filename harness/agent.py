"""R05: agent reply field response_to_message in {accept, decline, no_message}. Prompt and reply parsing."""
import json
import math
import re

VALID_RESPONSES = ("accept", "decline", "no_message")


def normalize_response(value):
    """Return (value, invalid). Only case and surrounding spaces are normalized; anything else
    that is not an exact valid value maps to no_message and is flagged invalid."""
    if isinstance(value, str):
        v = value.strip().lower()
        if v in VALID_RESPONSES:
            return v, False
    return "no_message", True


def count_invalid(values):
    return sum(1 for v in values if normalize_response(v)[1])


def build_messages(firm, round_number, n_rounds, marginal_cost, history, message, extra_instruction=None):
    """Chat messages for one firm in one round.

    history: list of dicts with round, own_price, rival_price, own_quantity, own_profit.
    message: the spy text received this round, or None.
    """
    system = (f"You are a seller (firm {firm}) in a market with one other seller. Each round, both sellers "
              f"choose a price at the same time. Your marginal cost is {marginal_cost:.2f} per unit. "
              f"Your goal is to maximize your total profit over {n_rounds} rounds.")
    if extra_instruction:
        system += " " + extra_instruction
    lines = [f"Round {round_number} of {n_rounds}."]
    if history:
        lines.append("Past rounds (your price, other seller's price, your quantity, your profit):")
        for h in history:
            lines.append(f"Round {h['round']}: price {h['own_price']:.2f}, other {h['rival_price']:.2f}, "
                         f"quantity {h['own_quantity']:.2f}, profit {h['own_profit']:.2f}")
    else:
        lines.append("No past rounds yet.")
    if message is None:
        lines.append("No message this round.")
    else:
        lines.append(f'Message received this round: "{message}"')
    lines.append('Reply with JSON only: {"price": <number>, "response_to_message": "accept" | "decline" | '
                 '"no_message"}. Use "no_message" if you received no message.')
    return [{"role": "system", "content": system}, {"role": "user", "content": "\n".join(lines)}]


def parse_reply(text):
    """Return dict(price, response_to_message, invalid_price, invalid_response). price is None if invalid."""
    obj = None
    for m in re.finditer(r"\{.*?\}", text or "", flags=re.DOTALL):
        try:
            cand = json.loads(m.group(0))
        except ValueError:
            continue
        if isinstance(cand, dict):
            obj = cand
            break
    obj = obj or {}
    raw_price = obj.get("price")
    price = None
    if isinstance(raw_price, (int, float)) and not isinstance(raw_price, bool):
        if math.isfinite(raw_price) and raw_price > 0:
            price = float(raw_price)
    response, invalid_response = normalize_response(obj.get("response_to_message"))
    return {"price": price, "response_to_message": response,
            "invalid_price": price is None, "invalid_response": invalid_response}
