r"""OPEN_ISSUES #29: in a LaTeX report, \url{https://x.org/a} and \href{https://x.org/b}{text} left the closing brace
in the extracted URL ("https://x.org/a}"), so every link was fetched wrong and reported broken."""
from tools import check_submission as cs


def test_issue29_latex_url_and_href_extracted_without_braces():
    tex = r"See \url{https://example.org/a} and \href{https://example.org/b}{the repo}. Plain https://example.org/c."
    assert cs.extract_urls(tex) == ["https://example.org/a", "https://example.org/b", "https://example.org/c"]


def test_issue29_markdown_links_unchanged():
    assert cs.extract_urls("[repo](https://github.com/x/y) and (https://example.org/a).") == [
        "https://github.com/x/y", "https://example.org/a"]
