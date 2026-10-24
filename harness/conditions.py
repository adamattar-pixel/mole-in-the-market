"""R03, R04: conditions A, E, B, B_T, C, D built only from texts in PREREGISTRATION.md."""
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

CONDITIONS = ("A", "E", "B", "B_T", "C", "D")

PREREG_PATH = Path(__file__).resolve().parent.parent / "PREREGISTRATION.md"

_REQUIRED_KEYS = ("label_sentence", "neutral_label", "trust_label", "offer_body", "hint_body",
                  "harmless_body", "e_instruction", "e_threshold_gap_fraction",
                  "behavioral_gap_fraction", "behavioral_window")

# condition -> (body key, label key, offer form, trust label, gets e_instruction)
_LAYOUT = {
    "A": (None, None, "none", "none", False),
    "E": ("offer_body", "neutral_label", "direct", "neutral", True),
    "B": ("offer_body", "neutral_label", "direct", "neutral", False),
    "B_T": ("offer_body", "trust_label", "direct", "trust", False),
    "C": ("hint_body", "neutral_label", "hint", "neutral", False),
    "D": ("harmless_body", "neutral_label", "harmless", "neutral", False),
}


@dataclass(frozen=True)
class Condition:
    name: str
    message: str | None
    extra_instruction: str | None
    offer_form: str
    trust_label: str


def load_prereg_texts(path=None):
    """Read the first ```yaml block of PREREGISTRATION.md (the frozen texts)."""
    text = Path(path or PREREG_PATH).read_text(encoding="utf-8")
    m = re.search(r"```yaml\n(.*?)```", text, flags=re.DOTALL)
    if not m:
        raise ValueError("no ```yaml block with frozen texts in the preregistration")
    data = yaml.safe_load(m.group(1))
    missing = [k for k in _REQUIRED_KEYS if k not in data]
    if missing:
        raise ValueError(f"preregistration is missing: {missing}")
    return data


def condition_metadata(name):
    """(offer form, trust label) of a condition, without needing the texts."""
    if name not in _LAYOUT:
        raise ValueError(f"unknown condition: {name!r}")
    return _LAYOUT[name][2], _LAYOUT[name][3]


def build_condition(name, texts, deal_price):
    if name not in _LAYOUT:
        raise ValueError(f"unknown condition: {name!r}")
    body_key, label_key, form, trust, gets_e = _LAYOUT[name]
    message = None
    if body_key is not None:
        label = texts["label_sentence"].format(label=texts[label_key])
        body = texts[body_key].replace("{deal_price}", f"{deal_price:.2f}")
        message = f"{label} {body}"
    extra = texts["e_instruction"] if gets_e else None
    return Condition(name=name, message=message, extra_instruction=extra, offer_form=form,
                     trust_label=trust)
