import shutil
import sys
import types
import unicodedata
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rag import chunk as C                      # noqa: E402
from rag.embed import HashingEmbedder, SentenceTransformerEmbedder  # noqa: E402
from rag.extract import Block, extract_blocks   # noqa: E402
from rag.store import index_chunks, search      # noqa: E402
from rag.text import normalize, split_sentences  # noqa: E402

PDF = ROOT / "data" / "Agni_Ki_Udaan_Adhyayan_Sahayika_Hindi.pdf"
needs_poppler = pytest.mark.skipif(shutil.which("pdftotext") is None, reason="poppler not installed")


# ------------------------------------------------------------------ text hygiene
def test_normalize_repairs_known_artefacts_but_keeps_real_spaces():
    assert normalize("रॉके ट") == "रॉकेट"
    assert normalize("इं जीनियरिं ग") == "इंजीनियरिंग"
    assert normalize("एकीकृ त") == "एकीकृत"
    assert normalize("के वल") == "केवल"
    assert "अग्नि की उड़ान" in normalize("अग्नि की उड़ान")      # real word boundary preserved


def test_normalize_is_nfc_idempotent_and_strips_invisibles():
    s = "क़\u200d\u200b ड़"
    once = normalize(s)
    assert once == unicodedata.normalize("NFC", once) and normalize(once) == once
    assert "\u200d" not in once and "\u200b" not in once


def test_sentence_split_uses_danda_and_keeps_abbreviations():
    s = split_sentences('ए.पी.जे. अब्दुल कलाम थे। उन्होंने कहा "सपने देखो।" क्या यह सच है? हाँ!')
    assert len(s) == 4
    assert s[0].startswith("ए.पी.जे.") and s[1].endswith('।"')


# ------------------------------------------------------------------ chunking
def test_pack_sentences_respects_max_and_overlaps_one_sentence():
    sents = [f"वाक्य संख्या {i} " + "क" * 80 + "।" for i in range(6)]
    chunks = C.pack_sentences(sents, max_chars=250, overlap=1)
    assert all(len(c) <= 250 for c in chunks) and len(chunks) > 2
    for a, b in zip(chunks, chunks[1:]):
        assert a.split("। ")[-1].rstrip("।") in b          # last sentence of a reappears in b


def test_table_row_text_drops_empty_cells():
    assert C.table_row_text(["वर्ष", "सम्मान", "टिप्पणी"], ["1997", "भारत रत्न", "—"]) == \
        "वर्ष: 1997; सम्मान: भारत रत्न"


def test_build_chunks_metadata_kinds_and_section_carry_forward():
    blocks = [
        Block(1, "text", "एक अध्ययन सहायिका। आवरण।"),
        Block(2, "text", "विषय-सूची\n1. कुछ।"),
        Block(3, "text", "6 · इसरो के वर्ष\nपहला वाक्य। दूसरा वाक्य।"),
        Block(3, "table", rows=[["वर्ष", "पड़ाव"], ["1980", "रोहिणी"]]),
        Block(4, "text", "अगले पृष्ठ का पाठ बिना शीर्षक के।"),
        Block(5, "text", "19 · विचार एवं बोध-प्रश्न\n1. प्रश्न?"),
    ]
    ch = C.build_chunks(blocks)
    assert [c.chunk_id for c in ch] == list(range(len(ch)))
    assert [c.kind for c in ch] == ["cover", "toc", "prose", "table_row", "prose", "quiz"]
    assert ch[3].page == 3 and ch[3].section == "इसरो के वर्ष" and "1980" in ch[3].text
    assert ch[4].page == 4 and ch[4].section == "इसरो के वर्ष"      # carried across pages
    assert ch[5].section_no == 19


# ------------------------------------------------------------------ embedders
def test_e5_prefixes_are_applied(monkeypatch):
    seen = []

    class Fake:
        def __init__(self, *a, **k): ...
        def encode(self, texts, **k):
            seen.extend(texts)
            import numpy as np
            return np.ones((len(texts), 3))

    monkeypatch.setitem(sys.modules, "sentence_transformers",
                        types.SimpleNamespace(SentenceTransformer=Fake))
    e = SentenceTransformerEmbedder("intfloat/multilingual-e5-small")
    e.embed_passages(["नमस्ते"]); e.embed_query("hello")
    assert seen == ["passage: नमस्ते", "query: hello"]
    seen.clear()
    SentenceTransformerEmbedder("BAAI/bge-m3").embed_query("hello")
    assert seen == ["hello"]                                       # no prefix for BGE


# ------------------------------------------------------------------ real PDF (integration)
@needs_poppler
def test_real_pdf_extraction_is_clean_and_cited_correctly():
    ch = C.build_chunks(extract_blocks(str(PDF)))
    assert [c.chunk_id for c in ch] == list(range(len(ch)))
    joined = "\n".join(c.text for c in ch)
    assert "\x00" not in joined and "\ufffd" not in joined       # no mojibake / NULs
    assert "रॉकेट" in joined and "इंजीनियरिंग" in joined

    bharat = [c for c in ch if c.kind == "table_row" and "भारत रत्न" in c.text and "1997" in c.text]
    assert bharat and bharat[0].page == 16 and bharat[0].section == "पुरस्कार एवं सम्मान"

    death = [c for c in ch if c.kind == "prose" and "शिलांग" in c.text and "गिर पड़े" in c.text]
    assert death and death[0].page == 15

    assert {c.page for c in ch if c.kind == "quiz"} == {21}
    assert {c.page for c in ch if c.kind == "table_row"} == {9, 12, 16, 17, 20, 22}


@needs_poppler
def test_quiz_chunks_are_never_retrieved_even_for_a_verbatim_quiz_question(tmp_path):
    ch = C.build_chunks(extract_blocks(str(PDF)))
    emb = HashingEmbedder(tmp_path)
    index_chunks(str(tmp_path), ch, emb.embed_passages([c.embed_text for c in ch]))
    quiz_q = "SLV-III क्या था, इसने किस उपग्रह को कक्षा में स्थापित किया, और किस वर्ष?"
    hits = search(str(tmp_path), emb.embed_query(quiz_q), k=5)
    assert hits and all(h.kind in ("prose", "table_row") for h in hits)
    assert "पृष्ठ" not in hits[0].citation() and "page:" in hits[0].citation()
    naive = search(str(tmp_path), emb.embed_query(quiz_q), k=5, kinds=[])
    assert any(h.kind == "quiz" for h in naive)                   # the trap is real without the filter


# ------------------------------------------------------------------ free-tier LLM backends (HTTP mocked)
def _hits():
    from rag.store import Hit
    return [Hit(30, 8, "इसरो", "prose", "SLV-III ने रोहिणी उपग्रह को 1980 में स्थापित किया।", 0.8)]


def test_gemini_backend_parses_response_and_skips_thought_parts(monkeypatch):
    from rag import generate as G
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    seen = {}

    def fake_post(url, body, headers, timeout=60):
        seen.update(url=url, headers=headers, body=body)
        return {"candidates": [{"content": {"parts": [
            {"text": "reasoning...", "thought": True}, {"text": "रोहिणी, 1980 [chunk 30]"}]}}]}
    monkeypatch.setattr(G, "_post_json", fake_post)
    text, used = G.generate("q", _hits(), "gemini")
    assert used == "gemini" and text == "रोहिणी, 1980 [chunk 30]"
    assert "generativelanguage.googleapis.com" in seen["url"] and seen["headers"]["x-goog-api-key"] == "x"
    assert G.cited_ids(text) == {30}


def test_groq_backend_parses_openai_style_response(monkeypatch):
    from rag import generate as G
    monkeypatch.setenv("GROQ_API_KEY", "x")
    monkeypatch.setattr(G, "_post_json", lambda *a, **k: {"choices": [{"message": {"content": " 1997 [chunk 5] "}}]})
    assert G.generate("q", _hits(), "groq") == ("1997 [chunk 5]", "groq")


def test_auto_falls_through_when_free_tier_is_rate_limited(monkeypatch):
    from rag import generate as G
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    monkeypatch.setenv("GROQ_API_KEY", "x")
    monkeypatch.setattr(G, "_ollama_up", lambda: False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def gemini_429(*a, **k):
        raise RuntimeError("HTTP 429")
    monkeypatch.setattr(G, "_gemini", gemini_429)
    monkeypatch.setattr(G, "_groq", lambda q, h: "ok [chunk 30]")
    assert G.generate("q", _hits(), "auto") == ("ok [chunk 30]", "groq")
