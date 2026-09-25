from __future__ import annotations

import zlib
from pathlib import Path

import numpy as np

from .text import normalize

DEFAULT_MODEL = "intfloat/multilingual-e5-small"


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str = DEFAULT_MODEL, device: str | None = None):
        from sentence_transformers import SentenceTransformer
        self.name = model_name
        self.model = SentenceTransformer(model_name, device=device)
        self._q, self._p = ("query: ", "passage: ") if "e5" in model_name.lower() else ("", "")

    def _enc(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(texts, normalize_embeddings=True, batch_size=16,
                                 show_progress_bar=False)

    def embed_passages(self, texts: list[str]) -> np.ndarray:
        return self._enc([self._p + normalize(t) for t in texts])

    def embed_query(self, text: str) -> np.ndarray:
        return self._enc([self._q + normalize(text)])[0]


class HashingEmbedder:
    DIM = 2048

    def __init__(self, state_dir: str | Path = "chroma_db"):
        self.name = "hashing-char-ngram (offline, lexical only)"
        self._path = Path(state_dir) / "hash_idf.npy"
        self.idf = np.load(self._path) if self._path.exists() else None

    def _tf(self, text: str) -> np.ndarray:
        v = np.zeros(self.DIM, dtype=np.float32)
        t = f" {normalize(text).lower()} "
        for n in (2, 3, 4):
            for i in range(len(t) - n + 1):
                v[zlib.crc32(t[i:i + n].encode()) % self.DIM] += 1.0
        return np.log1p(v)

    @staticmethod
    def _unit(m: np.ndarray) -> np.ndarray:
        return m / np.maximum(np.linalg.norm(m, axis=-1, keepdims=True), 1e-9)

    def embed_passages(self, texts: list[str]) -> np.ndarray:
        tf = np.stack([self._tf(t) for t in texts])
        df = (tf > 0).sum(axis=0)
        self.idf = (np.log((1 + len(texts)) / (1 + df)) + 1).astype(np.float32)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        np.save(self._path, self.idf)
        return self._unit(tf * self.idf)

    def embed_query(self, text: str) -> np.ndarray:
        if self.idf is None:
            raise RuntimeError("Run `ingest` first (IDF statistics are fitted at ingest time).")
        return self._unit(self._tf(text) * self.idf)


def make_embedder(spec: str, state_dir: str | Path = "chroma_db"):
    if spec == "hash":
        return HashingEmbedder(state_dir)
    return SentenceTransformerEmbedder(spec)
