"""R18: no hardcoded results; every result number in a document must come from the reproduce outputs.

tools/check_numbers.py extracts the RESULT-LIKE numbers of a Markdown document (decimals such as 0.67,
percentages such as 67%, counts such as 2/3) and checks each one against the numbers found in the source
files (results/*.json, *.md, *.csv written by tools/reproduce.py).
Matching rules (hand-checkable):
- decimal with p digits after the point matches a source number v when round(v, p) == the decimal;
- percentage x% with p digits after the point matches when round(100 * v, p) == x;
- count k/n matches when a JSON object of the sources has "k": k and "n": n, or the text "k/n" is in a source.
Plain integers, dates, ids (R28, H4, D10), hashes and versions followed by letters (3.8B) are not checked.
Numbers inside ``` code blocks are skipped unless include_code=True.
"""
import json

import pytest

from tools import check_numbers as cn

# rate = 2/3 = 0.6666666666666666 ; Wilson(2, 3) is about [0.2077, 0.9385] (only the rounding matters here)
SOURCE = {"rates": {"fx": {"B": {"say": {"k": 2, "n": 3, "rate": 0.6666666666666666,
                                         "ci": [0.20765960, 0.93851660]}}}},
          "e_validation": {"fx": {"effect_gap_fraction": 0.9312}}}


@pytest.fixture
def src(tmp_path):
    p = tmp_path / "summary.json"
    p.write_text(json.dumps(SOURCE), encoding="utf-8")
    return [p]


def unmatched_tokens(text, sources, **kw):
    return [u["token"] for u in cn.check_text(text, sources, **kw)]


# ---------------- extraction ----------------

def test_R18_extracts_decimals_percentages_and_counts():
    toks = [(t["token"], t["kind"]) for t in cn.extract_numbers("Say rate 0.67 (67%), 2/3 games, CI 0.21-0.94.")]
    assert toks == [("0.67", "decimal"), ("67%", "percent"), ("2/3", "count"), ("0.21", "decimal"), ("0.94", "decimal")]


def test_R18_trap_ids_dates_hashes_versions_and_integers_are_not_extracted():
    text = "R28 and H4 on 2026-10-24, commit 8a0835a, model Qwen3.8B, 5 seeds, 20 rounds, D10, v1.2.3 tag."
    assert cn.extract_numbers(text) == []


def test_R18_line_numbers_and_code_blocks():
    text = "intro 0.67\n```\nprint(0.123)\n```\nend 0.5\n"
    found = cn.extract_numbers(text)
    assert [(t["line"], t["token"]) for t in found] == [(1, "0.67"), (5, "0.5")]
    with_code = cn.extract_numbers(text, include_code=True)
    assert [(t["line"], t["token"]) for t in with_code] == [(1, "0.67"), (3, "0.123"), (5, "0.5")]


# ---------------- matching ----------------

@pytest.mark.parametrize("tok", ["0.67", "0.667", "0.7", "67%", "66.7%", "2/3", "0.21", "0.94", "0.93", "0.931"])
def test_R18_numbers_from_the_sources_match(src, tok):
    # 0.6667 -> 0.67 / 0.667 / 0.7 ; 66.67 -> 67% / 66.7% ; k=2, n=3 ; 0.2077 -> 0.21 ; 0.9385 -> 0.94 ;
    # effect 0.9312 -> 0.93 / 0.931
    assert unmatched_tokens(f"value {tok} here", src) == []


@pytest.mark.parametrize("tok", ["0.68", "68%", "3/4", "0.22", "0.95", "0.932", "66.6%"])
def test_R18_invented_numbers_are_flagged(src, tok):
    # 0.68 != round(0.6667, 2) ; 68 != round(66.67) ; no k=3, n=4 ; 0.22 != 0.21 ; 0.95 != 0.94 ;
    # 0.932 != round(0.9312, 3) = 0.931 ; 66.6 != round(66.667, 1) = 66.7
    assert unmatched_tokens(f"value {tok} here", src) == [tok]


def test_R18_text_sources_match_literally(tmp_path):
    md = tmp_path / "tables.md"
    md.write_text("| B | 5/5 (1.00, 95% CI 0.57-1.00) |\n", encoding="utf-8")
    assert unmatched_tokens("all 5/5 at 1.00, CI 0.57", [md]) == []
    assert unmatched_tokens("all 4/5", [md]) == ["4/5"]


def test_R18_allowed_design_constants(src):
    # 0.10 and 0.25 are frozen definitions (preregistration), not results
    assert unmatched_tokens("tolerance 0.10, threshold 0.25", src, allow=["0.10", "0.25"]) == []
    assert unmatched_tokens("tolerance 0.10, threshold 0.25", src) == ["0.10", "0.25"]


def test_R18_unmatched_report_has_line_and_kind(src):
    res = cn.check_text("ok 0.67\nbad 0.68\n", src)
    assert res == [{"line": 2, "token": "0.68", "kind": "decimal"}]


def test_R18_sources_from_directory(tmp_path):
    d = tmp_path / "results"
    d.mkdir()
    (d / "summary.json").write_text(json.dumps(SOURCE), encoding="utf-8")
    (d / "labels.csv").write_text("game_id,base_rate\nx,0.500000\n", encoding="utf-8")
    files = cn.collect_sources([d])
    assert sorted(p.name for p in files) == ["labels.csv", "summary.json"]
    assert unmatched_tokens("base 0.50 and 0.67", files) == []


def test_R18_missing_source_rejected(tmp_path):
    with pytest.raises(FileNotFoundError):
        cn.collect_sources([tmp_path / "nope"])


# ---------------- CLI ----------------

def test_R18_cli_exit_codes(tmp_path, capsys):
    d = tmp_path / "results"
    d.mkdir()
    (d / "summary.json").write_text(json.dumps(SOURCE), encoding="utf-8")
    good = tmp_path / "good.md"
    good.write_text("rate 0.67 (2/3)\n", encoding="utf-8")
    bad = tmp_path / "bad.md"
    bad.write_text("rate 0.67\nrate 0.68\n", encoding="utf-8")
    assert cn.main([str(good), "--sources", str(d)]) == 0
    assert cn.main([str(bad), "--sources", str(d)]) == 1
    out = capsys.readouterr().out
    assert "line 2: 0.68 (decimal) not found in the sources" in out
    assert cn.main([str(bad), "--sources", str(d), "--allow", "0.68"]) == 0
