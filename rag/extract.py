"""
Extract text and table rows from a PDF while keeping the correct page order.

This PDF uses Devanagari Type-3 fonts, which causes problems with some PDF
libraries:
  - pdfplumber/pdfminer often return U+0000 instead of the actual characters.
  - PyMuPDF can return duplicated characters, such as "उड़ाान" or "अब्दुुल".
  - Poppler's pdftotext handles the Devanagari text correctly.

So, Poppler is used for extracting the actual text, while pdfplumber is used
only to detect table boundaries from the ruling lines. Once the table and
prose regions are identified, each region is cropped and passed to Poppler,
which lets us preserve the document order and extract table rows cleanly.
"""
from __future__ import annotations

import logging
import re
import shutil
import subprocess
from dataclasses import dataclass, field

import pdfplumber

from .text import clean_inline, normalize

logging.getLogger("pdfminer").setLevel(logging.ERROR)  # noisy FontBBox warnings

HEADING_RE = re.compile(r"^\s*(\d{1,2}) · (.+?)\s*$")
UNNUMBERED_HEADINGS = {"विषय-सूची"}


@dataclass
class Block:
    page: int
    kind: str
    text: str = ""
    rows: list[list[str]] = field(default_factory=list)


def _pdftotext(pdf: str, page: int, box: tuple[float, float, float, float] | None = None) -> str:
    if shutil.which("pdftotext") is None:
        raise RuntimeError(
            "`pdftotext` (Poppler) not found. Install it: `sudo apt-get install poppler-utils` "
            "| `brew install poppler` | `conda install -c conda-forge poppler`."
        )
    cmd = ["pdftotext", "-enc", "UTF-8", "-nopgbrk", "-f", str(page), "-l", str(page)]
    if box:
        x0, y0, x1, y1 = box
        cmd += ["-r", "72", "-x", str(int(x0)), "-y", str(int(y0)),
                "-W", str(int(x1 - x0) + 1), "-H", str(int(y1 - y0) + 1)]
    out = subprocess.run(cmd + [pdf, "-"], capture_output=True, check=True)
    return normalize(out.stdout.decode("utf-8"))


def extract_blocks(pdf_path: str) -> list[Block]:
    blocks: list[Block] = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            width, height = float(page.width), float(page.height)
            cursor = 0.0
            for table in sorted(page.find_tables(), key=lambda t: t.bbox[1]):
                x0, top, x1, bottom = table.bbox
                if top - cursor > 4:
                    blocks.append(Block(pno, "text", _pdftotext(pdf_path, pno, (0, cursor, width, top))))
                rows = []
                for row in table.rows:
                    cells = [clean_inline(_pdftotext(pdf_path, pno, c)) if c else "" for c in row.cells]
                    rows.append(cells)
                blocks.append(Block(pno, "table", rows=rows))
                cursor = bottom
            if height - cursor > 4:
                blocks.append(Block(pno, "text", _pdftotext(pdf_path, pno, (0, cursor, width, height))))
    return [b for b in blocks if (b.text.strip() if b.kind == "text" else b.rows)]


def split_heading(text: str) -> tuple[tuple[int | None, str] | None, str]:
    lines = text.strip().splitlines()
    if not lines:
        return None, ""
    m = HEADING_RE.match(lines[0])
    if m:
        return (int(m.group(1)), m.group(2)), "\n".join(lines[1:])
    if lines[0].strip() in UNNUMBERED_HEADINGS:
        return (None, lines[0].strip()), "\n".join(lines[1:])
    return None, text
