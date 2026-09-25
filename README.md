<<<<<<< HEAD
# Hindi RAG — Agni Ki Udaan

RAG pipeline over the supplied Hindi PDF. Hindi and English questions both work, answers are grounded
in retrieved chunks and every answer carries a citation (page, section, chunk id, score).

```
PDF -> pdftotext (text) + pdfplumber (table boxes) -> chunks -> multilingual-e5 -> ChromaDB
question -> embed -> top-k -> LLM -> answer + citation
```

## 1. Chunking

Split on the Hindi danda `।`, not `.` — the doc has stuff like `ए.पी.जे.` where a period isn't a
sentence end. Target chunk size ~450 chars, 1 sentence of overlap. Kept it small because most test
questions want one specific fact (a year, a name), and a chunk that mixes several ideas makes the
embedding fuzzier. Overlap is there because a few sentences only make sense with the one before them.

Chunks don't cross page/section boundaries — each page here is its own numbered section anyway, so
citations end up exact instead of "somewhere around page 8-9."

Tables are chunked one row at a time (`वर्ष: 1997; सम्मान: भारत रत्न`) instead of as a blob — a row is
a complete fact on its own, and packing rows together just blurs them. ~49 of 116 chunks are table rows.

I also prepend the section title to the text before embedding (not what's shown to the user) — a bare
table row like "1997 → भारत रत्न" means nothing without knowing it's from the awards section.

Every chunk is tagged with a `kind` (prose / table_row / toc / cover / quiz) — see section 3 for why
that matters.

## 2. Why ChromaDB over Qdrant

Corpus is ~120 chunks, everything runs on one machine. Chroma is pip-installable, no server to run,
has metadata filtering built in — that covers what this needs. Qdrant makes more sense once you need
hybrid search or actual scale, but that's overkill here.

## 3. Hindi handling

**Embeddings:** `intfloat/multilingual-e5-small`. Puts Hindi and English in the same vector space,
which is the whole point — an English query needs to retrieve a Hindi chunk.

**Extraction was the annoying part.** This PDF uses Type-3 fonts, and most extractors choke on it —
pdfplumber returns null bytes for the Devanagari, PyMuPDF doubles letters (`उड़ाान`), pdfium adds random
spaces after matras (`कला म`). Poppler's `pdftotext` is the one that gets it right, so that's what
actually reads the text. pdfplumber is only used to find where the table boxes are on the page.

**Normalization:** Unicode NFC, strip zero-width characters, fix some stray spaces Poppler still leaves
around certain glyph clusters. This is corpus-specific — I found the broken fragments by scanning this
particular PDF's output and fixed those, not a general solution.

**One thing worth flagging:** page 21 has a list of "comprehension questions" that look almost
identical to the actual test queries, but don't contain any answers. If you don't filter those out,
retrieval ranks them at the top and the LLM gets handed a question instead of an answer. I filter them
out by `kind` at query time — they're still indexed, just excluded from search.

## 4. Generation + citations

Prompt gives the LLM the retrieved chunks (labeled `[chunk N]`), tells it to only use what's there and
say so if the answer isn't in the chunks. Supports Gemini and Groq (both free tier), Anthropic, a local
Ollama model, or a no-LLM extractive fallback that just returns the closest sentence. `--llm auto`
(default) tries them in that order and falls through if one fails.

Citations aren't written by the model — they come from the metadata already stored per chunk, so
there's nothing to hallucinate there.

Note: `gemini-2.5-flash-lite` got deprecated for new API keys partway through this, hence the
`GEMINI_MODEL` env override — set it to whatever `GET /v1beta/models` shows as available for your key
if the default one 404s.

## 5. How to run

```bash
# poppler is required
sudo apt-get install poppler-utils      # mac: brew install poppler

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env       # add GEMINI_API_KEY and/or GROQ_API_KEY (both have free tiers)

python main.py ingest      # builds the vector db, downloads the embedding model first time
python main.py test        # runs the 6 required queries -> results/test_query_results.md
python main.py eval -k 5   # retrieval quality check -> results/retrieval_eval.md

python main.py ask "कलाम को भारत रत्न किस वर्ष प्राप्त हुआ?"
pytest -q
```

## 6. What I'd do with more time

- Retrieval is dense-only right now. Adding BM25 alongside it would help with exact terms like
  `SLV-III` or `IGMDP` that embeddings don't always nail.
- Eval set is only 6 queries — enough to catch obvious regressions, not enough to really trust.
  Would want 30-50 with some paraphrased/harder ones.
- The artefact-repair fixes for Poppler's spacing quirks are specific to this PDF. A different
  Hindi PDF would need its own pass.
- Free-tier model IDs keep changing (see the Gemini note above) — could make the code list available
  models at startup instead of hardcoding a default.
=======
# Agni-Ki-Udaan-RAG
>>>>>>> 0646ccbded7cad77b296a59b79ce1a3368784526
# Agni-Ki-Udaan-RAG
