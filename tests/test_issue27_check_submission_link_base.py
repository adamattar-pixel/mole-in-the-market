"""OPEN_ISSUES #27: tools/check_submission.py resolved relative links from the repo root, but a Markdown link
is relative to the document's own folder. A report in report/ that links figures/key_figure.png and
../figures/game_grid.pdf was reported as having broken links. Default base is now the report's folder;
--repo-root still overrides it. Hand-built layout: <tmp>/report/r.md, <tmp>/report/figures/k.png,
<tmp>/figures/g.pdf."""
from tools import check_submission as cs

DOC = "# T\n\nAuthors: A\n\n## Abstract\nx\n\n![k](figures/k.png) ![g](../figures/g.pdf)\n"


def layout(tmp_path):
    (tmp_path / "report" / "figures").mkdir(parents=True)
    (tmp_path / "figures").mkdir()
    (tmp_path / "report" / "figures" / "k.png").write_bytes(b"png")
    (tmp_path / "figures" / "g.pdf").write_bytes(b"%PDF")
    doc = tmp_path / "report" / "r.md"
    doc.write_text(DOC, encoding="utf-8")
    return doc


def test_issue27_links_resolved_from_the_report_folder(tmp_path, capsys):
    doc = layout(tmp_path)
    cs.main([str(doc), "--offline"])
    out = capsys.readouterr().out
    assert "local links: OK" in out


def test_issue27_repo_root_still_overrides(tmp_path, capsys):
    doc = layout(tmp_path)
    cs.main([str(doc), "--offline", "--repo-root", str(tmp_path)])
    assert "local links: FAIL" in capsys.readouterr().out  # figures/k.png is not under <tmp>/figures
