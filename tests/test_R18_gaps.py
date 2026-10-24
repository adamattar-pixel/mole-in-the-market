"""R18 gap tests (new, separate from the locked tests/test_R18_check_numbers.py), found by running
tools/check_numbers.py on the team's documents on 2026-10-25:
- arXiv ids (2507.01413) and section numbers (### 4.1, Section 4.2) are not result numbers;
- a count k/n also matches when k and n are two integer values of the same JSON object
  (for example {"traces": 40, "traces_with_collusion_word": 39} -> 39/40), not across objects.
"""
import json

import pytest

from tools import check_numbers as cn


@pytest.mark.parametrize("text", ["see arXiv 2507.01413 and arXiv:2603.13940v2", "[x](https://arxiv.org/abs/2310.13548)",
                                  "### 4.1 Q1 say vs do", "Section 4.2 shows it", "(section 4.6)", "1.2 Results"])
def test_R18_gap_arxiv_ids_and_section_numbers_not_extracted(text):
    assert cn.extract_numbers(text) == []


def test_R18_gap_ordinary_decimals_still_extracted():
    # a decimal inside a sentence, or after a heading title, is still a result-like number
    assert [t["token"] for t in cn.extract_numbers("### Q1 rate 0.67\nrate 4.1 per game")] == ["0.67", "4.1"]


def test_R18_gap_count_from_two_integers_of_one_object(tmp_path):
    p = tmp_path / "extras.json"
    p.write_text(json.dumps({"rows": [{"traces": 40, "traces_with_collusion_word": 39},
                                      {"traces": 40, "other": 34}]}), encoding="utf-8")
    assert cn.check_text("39/40 and 34/40", [p]) == []
    # 39 and 34 are never in one object: 39/34 is not a count of the sources; 41/40 neither
    assert [u["token"] for u in cn.check_text("39/34 and 41/40", [p])] == ["39/34", "41/40"]


def test_R18_gap_count_numerator_not_above_denominator(tmp_path):
    # 39 and 40 are in one object, but a count is k/n with k <= n: 40/39 is not a count of the sources
    p = tmp_path / "extras.json"
    p.write_text(json.dumps({"traces": 40, "traces_with_collusion_word": 39}), encoding="utf-8")
    assert [u["token"] for u in cn.check_text("40/39", [p])] == ["40/39"]
