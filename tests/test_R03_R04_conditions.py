"""R03: conditions are config driven, texts only from PREREGISTRATION.md. R04: B and B_T differ only by the label."""
import re

import pytest

from harness.conditions import CONDITIONS, build_condition, load_prereg_texts

PLACEHOLDER_PREREG = """# PREREGISTRATION (test placeholder)
## Frozen texts
```yaml
status: PROPOSED
label_sentence: "LABEL[{label}]."
neutral_label: "neutral sender"
trust_label: "trusted sender"
offer_body: "OFFER at {deal_price}."
hint_body: "HINT near {deal_price}."
harmless_body: "HARMLESS request."
e_instruction: "E-ALLOWED."
e_threshold_gap_fraction: 0.25
behavioral_gap_fraction: 0.10
behavioral_window: 3
```
"""

# Words that signal a price pact. D must contain none of them.
PACT_WORDS = ["deal", "pact", "agree", "both", "together", "coordinat", "collu", "fix", "cartel", "{deal_price}"]


@pytest.fixture
def texts(tmp_path):
    p = tmp_path / "PREREGISTRATION.md"
    p.write_text(PLACEHOLDER_PREREG, encoding="utf-8")
    return load_prereg_texts(p)


def test_R03_all_six_conditions_exist(texts):
    assert set(CONDITIONS) == {"A", "E", "B", "B_T", "C", "D"}
    assert {build_condition(n, texts, 5.5).name for n in CONDITIONS} == set(CONDITIONS)


def test_R03_A_sends_nothing(texts):
    c = build_condition("A", texts, deal_price=5.5)
    assert c.message is None
    assert c.extra_instruction is None


def test_R03_each_condition_loads_its_text(texts):
    # Label sentence + one space + body. Deal price 5.5 -> "{deal_price}" becomes "5.50" (2 decimals).
    assert build_condition("B", texts, 5.5).message == "LABEL[neutral sender]. OFFER at 5.50."
    assert build_condition("B_T", texts, 5.5).message == "LABEL[trusted sender]. OFFER at 5.50."
    assert build_condition("C", texts, 5.5).message == "LABEL[neutral sender]. HINT near 5.50."
    assert build_condition("D", texts, 5.5).message == "LABEL[neutral sender]. HARMLESS request."


def test_R03_E_is_B_offer_plus_instruction(texts):
    e = build_condition("E", texts, 5.5)
    b = build_condition("B", texts, 5.5)
    assert e.message == b.message
    assert e.extra_instruction == "E-ALLOWED."
    for name in ("A", "B", "B_T", "C", "D"):
        assert build_condition(name, texts, 5.5).extra_instruction is None


def test_R03_texts_follow_the_prereg_file(tmp_path):
    # Trap: hardcoded texts would ignore an edited file.
    p = tmp_path / "PREREGISTRATION.md"
    p.write_text(PLACEHOLDER_PREREG.replace("OFFER at", "CHANGED OFFER at"), encoding="utf-8")
    t = load_prereg_texts(p)
    assert build_condition("B", t, 5.5).message == "LABEL[neutral sender]. CHANGED OFFER at 5.50."


def test_R03_unknown_condition_rejected(texts):
    with pytest.raises(ValueError):
        build_condition("F", texts, 5.5)


def test_R03_missing_text_rejected(tmp_path):
    p = tmp_path / "PREREGISTRATION.md"
    p.write_text(re.sub(r"hint_body: .*\n", "", PLACEHOLDER_PREREG), encoding="utf-8")
    with pytest.raises((ValueError, KeyError)):
        t = load_prereg_texts(p)
        build_condition("C", t, 5.5)


def test_R03_real_prereg_D_has_no_pact_wording():
    t = load_prereg_texts()
    d = build_condition("D", t, 1.93).message.lower()
    for w in PACT_WORDS + ["1.93"]:
        assert w not in d, w


def test_R03_real_prereg_loads_every_condition():
    t = load_prereg_texts()
    for name in CONDITIONS:
        c = build_condition(name, t, 1.93)
        assert (c.message is None) == (name == "A")


def test_R03_condition_metadata(texts):
    assert build_condition("B", texts, 5.5).offer_form == "direct"
    assert build_condition("B_T", texts, 5.5).offer_form == "direct"
    assert build_condition("E", texts, 5.5).offer_form == "direct"
    assert build_condition("C", texts, 5.5).offer_form == "hint"
    assert build_condition("D", texts, 5.5).offer_form == "harmless"
    assert build_condition("A", texts, 5.5).offer_form == "none"
    assert build_condition("B_T", texts, 5.5).trust_label == "trust"
    assert build_condition("B", texts, 5.5).trust_label == "neutral"
    assert build_condition("A", texts, 5.5).trust_label == "none"


def _check_only_label_differs(t, deal):
    b = build_condition("B", t, deal).message
    bt = build_condition("B_T", t, deal).message
    neutral_sentence = t["label_sentence"].format(label=t["neutral_label"])
    trust_sentence = t["label_sentence"].format(label=t["trust_label"])
    assert b != bt
    assert b.count(neutral_sentence) == 1 and bt.count(trust_sentence) == 1
    # Removing the label sentence leaves byte-identical texts.
    assert b.replace(neutral_sentence, "") == bt.replace(trust_sentence, "")
    # Swapping the label sentence turns B into B_T exactly.
    assert b.replace(neutral_sentence, trust_sentence) == bt


def test_R04_placeholder_B_BT_differ_only_by_label(texts):
    _check_only_label_differs(texts, 5.5)


def test_R04_real_prereg_B_BT_differ_only_by_label():
    _check_only_label_differs(load_prereg_texts(), 1.93)
