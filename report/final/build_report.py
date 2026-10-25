"""Build report/final/REPORT.docx (on the official Apart template's styles) and REPORT.pdf from REPORT.md.

Run from the repo root:  python3 report/final/build_report.py
Needs python-docx and LibreOffice (soffice) for the PDF. No network. The Markdown file is the source of truth.
Bracketed placeholders [like this] and the AI-DRAFTED banner are highlighted in yellow so the authors see them.
Prints the page count of the main body (title page to the end of section 6, before "Code and Data").
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
OUT_PDF = HERE / "REPORT.pdf"

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
        if child.tag.endswith("}sectPr"):
            continue
        body.remove(child)


def add_table(document, rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    cells = [r for r in cells if not all(re.fullmatch(r"-{3,}", c) for c in r)]
    table = document.add_table(rows=len(cells), cols=len(cells[0]))
    # The template has no table style: draw thin borders directly.
    borders = OxmlElement("w:tblBorders")
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


def build():
    lines = SRC.read_text(encoding="utf-8").split("\n")
    document = docx.Document(str(TEMPLATE))
    clear_body(document)
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
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
        elif re.match(r"^(\d+)\. ", line):
            add_runs(document.add_paragraph(), line)
        elif line.startswith("- "):
            add_runs(document.add_paragraph(), "\u2022 " + line[2:])
        else:
            add_runs(document.add_paragraph(), line)
        i += 1
    document.save(str(OUT_DOCX))
    print("wrote", OUT_DOCX.relative_to(ROOT))


def to_pdf():
    soffice = shutil.which("soffice") or r"C:\Program Files\LibreOffice\program\soffice.exe"
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(HERE), str(OUT_DOCX)], check=True,
                   capture_output=True)
    print("wrote", OUT_PDF.relative_to(ROOT))


def body_pages():
    from pypdf import PdfReader
    reader = PdfReader(str(OUT_PDF))
    end = None
    for n, page in enumerate(reader.pages, start=1):
        if "Code and Data" in (page.extract_text() or ""):
            end = n
            break
    print(f"PDF pages: {len(reader.pages)}; main body ends on page {end} (the page where 'Code and Data' starts)")
    return len(reader.pages), end


if __name__ == "__main__":
    build()
    to_pdf()
    if "--no-count" not in sys.argv:
        body_pages()
