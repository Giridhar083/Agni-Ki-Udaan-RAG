"""ChromaDB persistence + retrieval"""
from __future__ import annotations

from dataclasses import dataclass

import chromadb

from .chunk import Chunk

COLLECTION = "kalam_hindi"
ANSWERABLE = ["prose", "table_row"]


@dataclass
class Hit:
    chunk_id: int
    page: int
    section: str
    kind: str
    text: str
    score: float           # cosine similarity

    def citation(self) -> str:
        return (f'page: {self.page} · section: "{self.section}" · '
                f'chunk_id: {self.chunk_id} · score: {self.score:.2f}')


def _collection(db_dir: str, reset: bool = False):
    client = chromadb.PersistentClient(path=db_dir)
    if reset:
        try:
            client.delete_collection(COLLECTION)
        except Exception:
            pass
    return client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})


def index_chunks(db_dir: str, chunks: list[Chunk], embeddings, meta_extra: dict | None = None) -> int:
    col = _collection(db_dir, reset=True)
    col.add(
        ids=[f"chunk-{c.chunk_id:04d}" for c in chunks],
        documents=[c.text for c in chunks],
        embeddings=[e.tolist() for e in embeddings],
        metadatas=[{**c.metadata(), **(meta_extra or {})} for c in chunks],
    )
    return col.count()


def search(db_dir: str, query_embedding, k: int = 4, kinds: list[str] | None = None) -> list[Hit]:
    col = _collection(db_dir)
    where = {"kind": {"$in": kinds if kinds is not None else ANSWERABLE}} if kinds != [] else None
    res = col.query(query_embeddings=[query_embedding.tolist()], n_results=k, where=where)
    hits = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        hits.append(Hit(meta["chunk_id"], meta["page"], meta["section"], meta["kind"],
                        doc, 1.0 - dist))
    return hits
