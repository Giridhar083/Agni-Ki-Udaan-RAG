from __future__ import annotations

from dataclasses import dataclass

from .extract import Block, split_heading
from .text import clean_inline, split_sentences

MAX_CHARS = 450
OVERLAP_SENTENCES = 1


@dataclass
class Chunk:
    chunk_id: int
    page: int
    section: str
    section_no: int
    kind: str
    text: str
    embed_text: str

    def metadata(self) -> dict:
        return {"chunk_id": self.chunk_id, "page": self.page, "section": self.section,
                "section_no": self.section_no, "kind": self.kind, "n_chars": len(self.text)}


def pack_sentences(sentences: list[str], max_chars: int = MAX_CHARS,
                   overlap: int = OVERLAP_SENTENCES) -> list[str]:
    chunks: list[list[str]] = []
    cur: list[str] = []
    for s in sentences:
        if cur and len(" ".join(cur + [s])) > max_chars:
            chunks.append(cur)
            cur = cur[-overlap:] if overlap else []
            if cur and len(" ".join(cur + [s])) > max_chars:
                cur = []
        cur.append(s)
    if cur:
        chunks.append(cur)
    return [" ".join(c) for c in chunks]


def _kind_for(section_no: int, section: str) -> str:
    if section_no == 0 and section == "विषय-सूची":
        return "toc"
    if section_no == 0:
        return "cover"
    if "बोध-प्रश्न" in section:
        return "quiz"
    return "prose"


def table_row_text(header: list[str], row: list[str]) -> str:
    pairs = [f"{h}: {v}" for h, v in zip(header, row) if v and v.strip("—- ")]
    return "; ".join(pairs)


def build_chunks(blocks: list[Block], max_chars: int = MAX_CHARS,
                 overlap: int = OVERLAP_SENTENCES) -> list[Chunk]:
    chunks: list[Chunk] = []
    section_no, section = 0, "आवरण पृष्ठ"

    def add(page: int, kind: str, text: str, ctx: str):
        chunks.append(Chunk(len(chunks), page, section, section_no, kind, text, f"{ctx}: {text}"))

    for b in blocks:
        if b.kind == "text":
            heading, body = split_heading(b.text)
            if heading:
                section_no, section = (heading[0] or 0), heading[1]
            kind = _kind_for(section_no, section)
            for piece in pack_sentences(split_sentences(body), max_chars, overlap):
                add(b.page, kind, piece, section)
        else:  # table
            header, *data = b.rows
            for row in data:
                text = table_row_text(header, row)
                if text:
                    add(b.page, "table_row", text, f"{section} (तालिका)")
    return chunks
