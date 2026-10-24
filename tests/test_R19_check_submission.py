"""R19: submission checks on the report source (Markdown or LaTeX). Page count stays MANUAL.

Rules (live sprint page, 2026-10-24, docs/apart/Guidelines.md): abstract 150 to 250 words; appendix titled exactly
"Limitations and Dual-Use / Ethical Considerations"; authors listed; same title on each submission; links work.
Word = a run of letters/digits, inner hyphens, apostrophes and dots kept ("dual-use" = 1, "0.25" = 1, "don't" = 1);
punctuation alone ("|", "-", "--") is not a word.
"""
import pytest

from tools import check_submission as cs

APPENDIX = "Limitations and Dual-Use / Ethical Considerations"


def md(abstract, authors="Authors: Ada Lovelace, Alan Turing", appendix=f"## {APPENDIX}\nText.", title="# Mole in the Market", extra=""):
    return f"{title}\n\n{authors}\n\n## Abstract\n{abstract}\n\n## Introduction\nBody.\n{extra}\n{appendix}\n"


# ---------------- abstract ----------------

def test_R19_word_count_rules():
    # "dual-use"=1, "0.25"=1, "don't"=1, "|" and "--" are not words -> 5 words: A dual-use test 0.25 don't
    assert cs.count_words("A dual-use test | 0.25 -- don't") == 5
    assert cs.count_words("") == 0


def test_R19_abstract_exactly_150_words_passes():
    r = cs.check_text(md(" ".join(["word"] * 150)))
    assert r["abstract_words"] == 150 and r["abstract_ok"] is True


def test_R19_abstract_exactly_250_words_passes():
    r = cs.check_text(md(" ".join(["word"] * 250)))
    assert r["abstract_words"] == 250 and r["abstract_ok"] is True


def test_R19_abstract_149_or_251_words_fails():
    r = cs.check_text(md(" ".join(["word"] * 149)))
    assert r["abstract_words"] == 149 and r["abstract_ok"] is False
    r = cs.check_text(md(" ".join(["word"] * 251)))
    assert r["abstract_words"] == 251 and r["abstract_ok"] is False


def test_R19_abstract_stops_at_next_heading():
    # Trap: the Introduction ("Body.") must not be counted. 3 words in the abstract.
    assert cs.check_text(md("One two three."))["abstract_words"] == 3


def test_R19_missing_abstract_fails():
    text = "# T\n\nAuthors: A\n\n## Introduction\nx\n## " + APPENDIX + "\n"
    r = cs.check_text(text)
    assert r["abstract_words"] is None and r["abstract_ok"] is False


def test_R19_latex_abstract():
    tex = ("\\title{Mole}\n\\author{Ada \\and Alan}\n\\begin{abstract}\nOne two three four.\n\\end{abstract}\n"
           "\\section{Intro}\nx\n\\section*{" + APPENDIX + "}\ny\n")
    r = cs.check_text(tex)
    assert r["abstract_words"] == 4 and r["abstract_ok"] is False  # 4 < 150
    assert r["appendix_ok"] is True
    assert r["authors"] == ["Ada", "Alan"]
    assert r["title"] == "Mole"


# ---------------- appendix ----------------

def test_R19_appendix_heading_present():
    assert cs.check_text(md("a b"))["appendix_ok"] is True


def test_R19_appendix_title_must_be_exact():
    r = cs.check_text(md("a b", appendix="## Limitations and Dual Use / Ethical Considerations\nx"))
    assert r["appendix_ok"] is False


def test_R19_appendix_title_in_body_text_only_fails():
    # Trap: the words appear in a sentence, not as a heading.
    body = f"We discuss the {APPENDIX} later."
    assert cs.check_text(md("a b", appendix=body))["appendix_ok"] is False


def test_R19_appendix_with_appendix_prefix_passes():
    assert cs.check_text(md("a b", appendix=f"## Appendix A: {APPENDIX}\nx"))["appendix_ok"] is True


# ---------------- authors and title ----------------

def test_R19_authors_listed():
    r = cs.check_text(md("a b"))
    assert r["authors"] == ["Ada Lovelace", "Alan Turing"] and r["authors_ok"] is True


def test_R19_missing_authors_fails():
    r = cs.check_text(md("a b", authors=""))
    assert r["authors"] == [] and r["authors_ok"] is False


def test_R19_title_matches_expected():
    assert cs.check_text(md("a b"), expected_title="Mole in the Market")["title_ok"] is True
    assert cs.check_text(md("a b"), expected_title="Mole in the Market v2")["title_ok"] is False
    # without an expected title the check is not run
    assert cs.check_text(md("a b"))["title_ok"] is None


# ---------------- links ----------------

def test_R19_links_extracted_without_trailing_punctuation():
    text = md("a b", extra="See (https://example.org/a). And https://example.org/b, and [repo](https://github.com/x/y).")
    assert cs.extract_urls(text) == ["https://example.org/a", "https://example.org/b", "https://github.com/x/y"]


def test_R19_links_checked_with_injected_fetcher():
    text = md("a b", extra="https://ok.org/x https://bad.org/y")
    status = {"https://ok.org/x": 200, "https://bad.org/y": 404}
    r = cs.check_text(text, fetch=lambda u: status[u])
    assert r["links"] == {"https://ok.org/x": True, "https://bad.org/y": False}
    assert r["links_ok"] is False


def test_R19_links_not_checked_offline():
    r = cs.check_text(md("a b", extra="https://ok.org/x"))
    assert r["links_ok"] is None  # not run, never reported as passed


def test_R19_fetch_error_counts_as_broken():
    def boom(u):
        raise OSError("down")
    r = cs.check_text(md("a b", extra="https://ok.org/x"), fetch=boom)
    assert r["links"] == {"https://ok.org/x": False}


def test_R19_relative_repo_links_must_exist(tmp_path):
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "game_grid.pdf").write_bytes(b"%PDF")
    text = md("a b", extra="![grid](figures/game_grid.pdf) [missing](runs/nothing.json)")
    r = cs.check_text(text, repo_root=tmp_path)
    assert r["local_links"] == {"figures/game_grid.pdf": True, "runs/nothing.json": False}
    assert r["local_links_ok"] is False


# ---------------- overall and CLI ----------------

def test_R19_overall_pass_and_fail():
    good = cs.check_text(md(" ".join(["w"] * 200)), expected_title="Mole in the Market", fetch=lambda u: 200)
    assert cs.overall(good) is True
    bad = cs.check_text(md(" ".join(["w"] * 251)), expected_title="Mole in the Market", fetch=lambda u: 200)
    assert cs.overall(bad) is False
    # a check that was not run (offline links, no expected title) is never a pass
    assert cs.overall(cs.check_text(md("a b"))) is False


def test_R19_cli_exit_codes(tmp_path, capsys):
    p = tmp_path / "report.md"
    p.write_text(md(" ".join(["w"] * 200)), encoding="utf-8")
    assert cs.main([str(p), "--title", "Mole in the Market", "--offline"]) == 1  # links not checked -> not a pass
    out = capsys.readouterr().out
    assert "abstract: 200 words (150 to 250) OK" in out and "links: NOT RUN" in out
    assert "page count: MANUAL" in out
