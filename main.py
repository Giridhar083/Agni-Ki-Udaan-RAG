#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from rag import chunk as chunk_mod
from rag.embed import DEFAULT_MODEL, make_embedder
from rag.extract import extract_blocks
from rag.generate import cited_ids, generate
from rag.queries import TEST_QUERIES
from rag.store import Hit, index_chunks, search
from rag.text import normalize

ROOT = Path(__file__).parent
DEFAULT_PDF = str(ROOT / "data" / "Agni_Ki_Udaan_Adhyayan_Sahayika_Hindi.pdf")
DEFAULT_DB = str(ROOT / "chroma_db")
RESULTS = ROOT / "results"

def _info_path(db: str) -> Path:
    return Path(db) / "index_info.json"


def load_embedder(args):
    info = json.loads(_info_path(args.db).read_text()) if _info_path(args.db).exists() else {}
    spec = args.model or info.get("model") or DEFAULT_MODEL
    if info and spec != info.get("model"):
        sys.exit(f"Index was built with '{info['model']}' but --model '{spec}' was requested. "
                 f"Re-run `python main.py --model {spec} ingest`.")
    return make_embedder(spec, args.db), spec


def answer_query(query: str, args, embedder) -> dict:
    hits = search(args.db, embedder.embed_query(query), k=args.k)
    text, used = generate(query, hits, args.llm, embedder)
    cited = cited_ids(text)
    return {"query": query, "answer": text, "llm": used, "hits": hits, "cited": cited}


def print_result(r: dict) -> None:
    print(f"\nQ: {r['query']}\nA: {r['answer']}\n   (generator: {r['llm']})\nSources:")
    for h in r["hits"]:
        mark = "★" if h.chunk_id in r["cited"] else " "
        print(f" {mark} {h.citation()}\n     “{h.text[:140]}{'…' if len(h.text) > 140 else ''}”")

def cmd_ingest(args):
    blocks = extract_blocks(args.pdf)
    chunks = chunk_mod.build_chunks(blocks, args.max_chars, args.overlap)
    embedder = make_embedder(args.model or DEFAULT_MODEL, args.db)
    vecs = embedder.embed_passages([c.embed_text for c in chunks])
    n = index_chunks(args.db, chunks, vecs)
    _info_path(args.db).write_text(json.dumps(
        {"model": args.model or DEFAULT_MODEL, "max_chars": args.max_chars,
         "overlap": args.overlap, "n_chunks": n}, ensure_ascii=False, indent=2))
    RESULTS.mkdir(exist_ok=True)
    with open(RESULTS / "chunks_dump.jsonl", "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps({**c.metadata(), "text": c.text}, ensure_ascii=False) + "\n")
    kinds = {}
    for c in chunks:
        kinds[c.kind] = kinds.get(c.kind, 0) + 1
    print(f"Indexed {n} chunks from {len(blocks)} blocks with '{embedder.name}' -> {args.db}\n"
          f"  by kind: {kinds}\n  chunk dump: {RESULTS / 'chunks_dump.jsonl'}")


def cmd_ask(args):
    embedder, _ = load_embedder(args)
    print_result(answer_query(args.query, args, embedder))


def cmd_test(args):
    embedder, spec = load_embedder(args)
    results = [answer_query(t["q"], args, embedder) for t in TEST_QUERIES]
    lines = [
        "# Test-query results (produced by `python main.py test`)", "",
        f"- Generated: {dt.datetime.now():%Y-%m-%d %H:%M}",
        f"- Embedding model: `{embedder.name}`",
        f"- Generator: `{results[0]['llm']}` · top-k = {args.k} · vector DB: ChromaDB (cosine)",
        f"- Retrieval filter: `kind ∈ {{prose, table_row}}` (quiz/TOC/cover chunks excluded)", "",
    ]
    for i, (t, r) in enumerate(zip(TEST_QUERIES, results), 1):
        print_result(r)
        primary = [h for h in r["hits"] if h.chunk_id in r["cited"]] or r["hits"][:1]
        others = [h for h in r["hits"] if h not in primary]
        lines += [f"## Query {i} ({'Hindi' if t['lang'] == 'hi' else 'English'})", "",
                  "| Field | Value |", "|---|---|",
                  f"| Query | {t['q']} |",
                  f"| Answer | {r['answer'].replace('|', '/').replace(chr(10), ' ')} |",
                  f"| Source (citation) | {'<br>'.join(h.citation() for h in primary)} |",
                  f"| Expected (from document) | {t['expected']} |", "",
                  "Other retrieved chunks:", ""]
        lines += [f"- {h.citation()} — {h.text[:110]}…" for h in others] or ["- (none)"]
        lines.append("")
    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / "test_query_results.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {out}")


def _first_rank(hits: list[Hit], gold: list[str]) -> int | None:
    for rank, h in enumerate(hits, 1):
        if all(normalize(g) in h.text for g in gold):
            return rank
    return None


def cmd_eval(args):
    embedder, _ = load_embedder(args)
    rows, summary = [], {}
    for label, kinds in (("kind filter ON (default)", None), ("kind filter OFF (naive)", [])):
        ranks = []
        for t in TEST_QUERIES:
            hits = search(args.db, embedder.embed_query(t["q"]), k=args.k, kinds=kinds)
            r = _first_rank(hits, t["gold"])
            ranks.append(r)
            rows.append((label, t["lang"], t["q"], r))
        n = len(ranks)
        summary[label] = {
            "hit@1": sum(r == 1 for r in ranks) / n,
            "hit@3": sum(r is not None and r <= 3 for r in ranks) / n,
            f"hit@{args.k}": sum(r is not None for r in ranks) / n,
            "MRR": sum(1 / r for r in ranks if r) / n}
    out = ["# Retrieval evaluation", "",
           f"Embedding model `{embedder.name}` · k = {args.k}. A hit = a retrieved chunk containing "
           "ALL gold substrings for the query (see `rag/queries.py`).", "",
           "| Configuration | " + " | ".join(next(iter(summary.values())).keys()) + " |",
           "|---|" + "---|" * len(next(iter(summary.values())))]
    out += [f"| {k} | " + " | ".join(f"{v:.2f}" for v in s.values()) + " |" for k, s in summary.items()]
    out += ["", "| Configuration | Lang | Query | Rank of first gold chunk |", "|---|---|---|---|"]
    out += [f"| {a} | {b} | {c} | {d if d else f'miss (>{args.k})'} |" for a, b, c, d in rows]
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "retrieval_eval.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))


# --------------------------------------------------------------------------- argparse
def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--db", default=DEFAULT_DB, help="ChromaDB directory")
    p.add_argument("--model", default=None,
                   help=f"embedding model name, or 'hash' for the offline lexical fallback "
                        f"(default: {DEFAULT_MODEL})")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("ingest", help="extract, chunk, embed, store")
    s.add_argument("--pdf", default=DEFAULT_PDF)
    s.add_argument("--max-chars", type=int, default=chunk_mod.MAX_CHARS)
    s.add_argument("--overlap", type=int, default=chunk_mod.OVERLAP_SENTENCES,
                   help="sentences carried into the next chunk")
    s.set_defaults(fn=cmd_ingest)

    for name, fn, helptext in (("ask", cmd_ask, "answer one question"),
                               ("test", cmd_test, "run the 6 required queries"),
                               ("eval", cmd_eval, "retrieval hit@k / MRR")):
        s = sub.add_parser(name, help=helptext)
        if name == "ask":
            s.add_argument("query")
        s.add_argument("-k", type=int, default=4, help="chunks to retrieve")
        s.add_argument("--llm", default="auto", choices=["auto", "gemini", "groq", "anthropic", "ollama", "extractive"])
        s.set_defaults(fn=fn)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
