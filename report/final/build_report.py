"""Build report/final/REPORT.docx (on the official Apart template's styles) and REPORT.pdf from REPORT.md.

Run from the repo root:  python3 report/final/build_report.py
Optional: python3 report/final/build_report.py <source.md> <out.docx>  (used to test the page budget on a filled copy)
Needs python-docx, pymupdf and LibreOffice (soffice) for the PDF. No API key, no network. REPORT.md is the source.
Bracketed placeholders [like this] and the AI-DRAFTED banner are highlighted in yellow; HTML comments are not printed.
Prints the main-body length in pages: from the top of page 1 to the "Code and Data" heading (limit 8).
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

import docx
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = HERE / "REPORT.md"
TEMPLATE = ROOT / "report" / "template" / "apart_template.docx"
OUT_DOCX = HERE / "REPORT.docx"

INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]*\](?!\())")


def add_runs(par, text, highlight_all=False):
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            run = par.add_run(part[2:-2])
            run.bold = True
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            run = par.add_run(part[1:-1])
            run.italic = True
        elif part.startswith("`") and part.endswith("`"):
            run = par.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(9)
        elif part.startswith("[") and part.endswith("]"):
            run = par.add_run(part)
            run.font.highlight_color = WD_COLOR_INDEX.YELLOW
        else:
            run = par.add_run(part)
        if highlight_all:
            run.font.highlight_color = WD_COLOR_INDEX.YELLOW


def clear_body(document):
    body = document.element.body
    for child in list(body):
        if not child.tag.endswith("}sectPr"):
            body.remove(child)


def add_table(document, rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    cells = [r for r in cells if not all(re.fullmatch(r"-{3,}", c) for c in r)]
    table = document.add_table(rows=len(cells), cols=len(cells[0]))
    borders = OxmlElement("w:tblBorders")  # the template has no table style: thin borders
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:color"), "999999")
        borders.append(el)
    table._tbl.tblPr.append(borders)
    for i, r in enumerate(cells):
        for j, c in enumerate(r):
            par = table.cell(i, j).paragraphs[0]
            add_runs(par, c)
            for run in par.runs:
                run.font.size = Pt(8.5)
                if i == 0:
                    run.bold = True
    document.add_paragraph()


def build(src=SRC, out_docx=OUT_DOCX):
    lines = Path(src).read_text(encoding="utf-8").split("\n")
    document = docx.Document(str(TEMPLATE))
    clear_body(document)
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.strip().startswith("<!--"):
            i += 1
            continue
        if line.startswith("> "):
            add_runs(document.add_paragraph(), line[2:], highlight_all=True)
        elif line.startswith("# "):
            add_runs(document.add_paragraph(style="Title"), line[2:])
        elif line.startswith("## "):
            add_runs(document.add_paragraph(style="Heading 2"), line[3:])
        elif line.startswith("### "):
            add_runs(document.add_paragraph(style="Heading 3"), line[4:])
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            add_table(document, rows)
            continue
        elif line.startswith("!["):
            m = re.match(r"!\[(.*)\]\((.*)\)", line)
            document.add_picture(str((HERE / m.group(2)).resolve()), width=Inches(6.3))
            cap = document.add_paragraph()
            add_runs(cap, m.group(1))
            for run in cap.runs:
                run.font.size = Pt(9)
        elif line.startswith("- "):
            add_runs(document.add_paragraph(), "\u2022 " + line[2:])
        else:
            add_runs(document.add_paragraph(), line)
        i += 1
    document.save(str(out_docx))
    print("wrote", out_docx)


def to_pdf(docx_path=OUT_DOCX):
    soffice = shutil.which("soffice") or str(Path("C:/Program Files/LibreOffice/program/soffice.exe"))
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(Path(docx_path).parent), str(docx_path)],
                   check=True, capture_output=True)
    print("wrote", Path(docx_path).with_suffix(".pdf"))


def body_pages(pdf_path):
    """Main body length in pages, from the top of page 1 to the "Code and Data" heading."""
    import pymupdf
    doc = pymupdf.open(str(pdf_path))
    for n, page in enumerate(doc, start=1):
        hits = page.search_for("Code and Data")
        if hits:
            length = (n - 1) + hits[0].y0 / page.rect.height
            print(f"PDF pages: {len(doc)}; main body: {length:.2f} pages (limit 8, margin {8 - length:.2f} pages)")
            return len(doc), length
    raise SystemExit("heading 'Code and Data' not found in the PDF")


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 2 else SRC
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT_DOCX
    build(src, out)
    to_pdf(out)
    body_pages(Path(out).with_suffix(".pdf"))
