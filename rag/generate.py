from __future__ import annotations

import json
import os
import re
import urllib.request

import numpy as np

from .store import Hit
from .text import split_sentences

SYSTEM = (
    "You answer questions about a Hindi document using ONLY the numbered context excerpts "
    "provided. Do not use outside knowledge, even if you know the answer. "
    "Reply in the same language as the question (Hindi question -> Hindi answer, English "
    "question -> English answer). Be concise: one or two sentences. "
    "After each fact, cite the excerpt it came from as [chunk N]. "
    "If the excerpts do not contain the answer, say so plainly instead of guessing."
)


def build_prompt(query: str, hits: list[Hit]) -> str:
    ctx = "\n\n".join(f"[chunk {h.chunk_id}] (page {h.page}, section: {h.section})\n{h.text}"
                      for h in hits)
    return f"Context excerpts:\n\n{ctx}\n\nQuestion: {query}\n\nAnswer:"


def cited_ids(answer: str) -> set[int]:
    return {int(n) for grp in re.findall(r"\[chunk\s*([\d,\s]+)\]", answer)
            for n in re.findall(r"\d+", grp)}


def _post_json(url: str, body: dict, headers: dict, timeout: int = 60) -> dict:
    req = urllib.request.Request(
        url, json.dumps(body).encode(),
        {"Content-Type": "application/json", "User-Agent": "kalam-rag/1.0", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _gemini(query: str, hits: list[Hit]) -> str:
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
    data = _post_json(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        {"systemInstruction": {"parts": [{"text": SYSTEM}]},
         "contents": [{"role": "user", "parts": [{"text": build_prompt(query, hits)}]}],
         # generous cap: "thinking" models spend part of this budget before answering
         "generationConfig": {"temperature": 0, "maxOutputTokens": 1024}},
        {"x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    parts = data["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()


def _groq(query: str, hits: list[Hit]) -> str:
    data = _post_json(
        "https://api.groq.com/openai/v1/chat/completions",
        {"model": os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
         "temperature": 0, "max_tokens": 400,
         "messages": [{"role": "system", "content": SYSTEM},
                      {"role": "user", "content": build_prompt(query, hits)}]},
        {"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"})
    return data["choices"][0]["message"]["content"].strip()


def _ollama_url() -> str:
    return os.environ.get("OLLAMA_URL", "http://localhost:11434")


def _ollama_up() -> bool:
    try:
        urllib.request.urlopen(_ollama_url() + "/api/tags", timeout=1.5)
        return True
    except Exception:
        return False


def _ollama(query: str, hits: list[Hit]) -> str:
    body = json.dumps({
        "model": os.environ.get("OLLAMA_MODEL", "qwen2.5:3b"), "stream": False,
        "options": {"temperature": 0},
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": build_prompt(query, hits)}]}).encode()
    req = urllib.request.Request(_ollama_url() + "/api/chat", body,
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)["message"]["content"].strip()


def _extractive(query: str, hits: list[Hit], embedder) -> str:
    cands = [(h, s) for h in hits[:2] for s in (split_sentences(h.text) or [h.text])]
    vecs = embedder.embed_passages([s for _, s in cands])
    best = int(np.argmax(vecs @ embedder.embed_query(query)))
    h, s = cands[best]
    return f"{s} [chunk {h.chunk_id}]"


def _available() -> list[str]:
    order = []
    if os.environ.get("GEMINI_API_KEY"):
        order.append("gemini")
    if os.environ.get("GROQ_API_KEY"):
        order.append("groq")
    if os.environ.get("ANTHROPIC_API_KEY"):
        order.append("anthropic")
    if _ollama_up():
        order.append("ollama")
    return order + ["extractive"]


def generate(query: str, hits: list[Hit], backend: str = "auto", embedder=None) -> tuple[str, str]:
    fns = {"gemini": _gemini, "groq": _groq, "anthropic": _anthropic, "ollama": _ollama}
    if backend != "auto":
        if backend == "extractive":
            return _extractive(query, hits, embedder), "extractive"
        return fns[backend](query, hits), backend
    for name in _available():
        if name == "extractive":
            break
        try:
            text = fns[name](query, hits)
            if text:
                return text, name
        except Exception as e:
            print(f"[generate] {name} failed ({type(e).__name__}: {e}); trying next backend")
    return _extractive(query, hits, embedder), "extractive"
