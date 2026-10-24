"""R03, R04: conditions A, E, B, B_T, C, D built only from texts in PREREGISTRATION.md."""

CONDITIONS = ("A", "E", "B", "B_T", "C", "D")


def load_prereg_texts(path=None):
    raise NotImplementedError


def build_condition(name, texts, deal_price):
    raise NotImplementedError
