"""R02: the spy is a script, not a model. At spy_start it sends the same frozen text to both firms."""
import inspect
import re
from pathlib import Path

import pytest

from harness.spy import ScriptedSpy

TEXT = "This message is from another agent in the market. Placeholder offer at 5.50."


def test_R02_both_firms_get_byte_identical_text_at_spy_start():
    spy = ScriptedSpy(TEXT, spy_start=8)
    msgs = spy.messages_for_round(8)
    assert set(msgs) == {"0", "1"}
    assert msgs["0"].encode("utf-8") == msgs["1"].encode("utf-8") == TEXT.encode("utf-8")


@pytest.mark.parametrize("rnd", [1, 7, 9, 20])
def test_R02_no_message_outside_spy_start(rnd):
    # PROPOSED definition (QUESTIONS #3): one message, once, in round spy_start.
    spy = ScriptedSpy(TEXT, spy_start=8)
    assert spy.messages_for_round(rnd) == {"0": None, "1": None}


def test_R02_spy_start_round_one():
    spy = ScriptedSpy(TEXT, spy_start=1)
    assert spy.messages_for_round(1) == {"0": TEXT, "1": TEXT}
    assert spy.messages_for_round(2) == {"0": None, "1": None}


def test_R02_no_message_condition_sends_nothing():
    spy = ScriptedSpy(None, spy_start=8)
    assert spy.messages_for_round(8) == {"0": None, "1": None}


def test_R02_spy_is_a_script_without_model_or_network():
    # Works with no client at all, and the module has no LLM or network import.
    spy = ScriptedSpy(TEXT, spy_start=2)
    assert spy.messages_for_round(2) == {"0": TEXT, "1": TEXT}
    params = inspect.signature(ScriptedSpy.__init__).parameters
    assert not any("client" in p or "model" in p for p in params)
    src = Path(inspect.getsourcefile(ScriptedSpy)).read_text(encoding="utf-8")
    forbidden = r"^\s*(import|from)\s+(harness\.clients|openai|anthropic|requests|urllib|http|httpx|socket)\b"
    assert not re.search(forbidden, src, flags=re.MULTILINE)


def test_R02_text_is_not_rewritten():
    weird = "  Exact  text,\twith odd   spacing.\n"
    spy = ScriptedSpy(weird, spy_start=3)
    assert spy.messages_for_round(3)["0"] == weird
