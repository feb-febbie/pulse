"""
RAG (Retrieval-Augmented Generation) over the Pulse medical knowledge base.

Uses a HYBRID retrieval strategy:
  - FAISS dense vector search (sentence-transformers/all-MiniLM-L6-v2)
  - BM25 sparse keyword scoring
  - Reciprocal Rank Fusion (RRF) to merge results

Dense embeddings handle semantic queries ("my head hurts" → headache).
BM25 handles exact medical terminology ("Ibuprofen 400mg", "tachycardia").
RRF fuses both rankings without requiring score normalization.

Medical credibility requires grounding responses in a curated source —
this prevents hallucination on symptom interpretation.
"""
from __future__ import annotations

import math
import os
import re
from collections import Counter
from typing import Optional

import numpy as np

import config
from data.geriatric_knowledge import get_all_text_chunks

try:
    from sentence_transformers import SentenceTransformer
    _ST_AVAILABLE = True
except ImportError:
    _ST_AVAILABLE = False

try:
    import faiss
    _FAISS_AVAILABLE = True
except ImportError:
    _FAISS_AVAILABLE = False


# ── BM25 implementation ───────────────────────────────────────────────────────

class BM25:
    """
    Okapi BM25 sparse retrieval over the medical knowledge chunks.
    k1=1.5, b=0.75 are standard defaults from the original paper.
    """

    def __init__(self, chunks: list[dict], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self._tokenize_corpus()

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\b[a-z]{2,}\b", text.lower())

    def _tokenize_corpus(self) -> None:
        self.tokenized = [
            self._tokenize(c["content"] + " " + " ".join(c.get("symptoms", [])))
            for c in self.chunks
        ]
        self.doc_lengths = [len(t) for t in self.tokenized]
        self.avgdl = sum(self.doc_lengths) / max(len(self.doc_lengths), 1)

        # Inverted index: term → {doc_idx: term_freq}
        self.inverted: dict[str, dict[int, int]] = {}
        for idx, tokens in enumerate(self.tokenized):
            for term, freq in Counter(tokens).items():
                self.inverted.setdefault(term, {})[idx] = freq

        # IDF for each term
        N = len(self.chunks)
        self.idf: dict[str, float] = {}
        for term, postings in self.inverted.items():
            df = len(postings)
            self.idf[term] = math.log((N - df + 0.5) / (df + 0.5) + 1)

    def score(self, query: str) -> list[float]:
        query_terms = self._tokenize(query)
        scores = [0.0] * len(self.chunks)
        for term in query_terms:
            if term not in self.inverted:
                continue
            idf = self.idf[term]
            for idx, tf in self.inverted[term].items():
                dl = self.doc_lengths[idx]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                scores[idx] += idf * numerator / denominator
        return scores

    def retrieve(self, query: str, k: int) -> list[dict]:
        scores = self.score(query)
        ranked = sorted(range(len(scores)), key=lambda i: -scores[i])
        return [self.chunks[i] for i in ranked[:k] if scores[i] > 0]


# ── Reciprocal Rank Fusion ────────────────────────────────────────────────────

def _rrf_merge(ranked_lists: list[list[dict]], k: int = 60) -> list[dict]:
    """
    Reciprocal Rank Fusion: score = Σ 1/(k + rank).
    Works across arbitrarily many ranked lists without score normalization.
    """
    scores: dict[str, float] = {}
    id_to_chunk: dict[str, dict] = {}

    for ranked in ranked_lists:
        for rank, chunk in enumerate(ranked):
            cid = chunk["id"]
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
            id_to_chunk[cid] = chunk

    return [id_to_chunk[cid] for cid, _ in sorted(scores.items(), key=lambda x: -x[1])]


# ── MedicalRAG ────────────────────────────────────────────────────────────────

class MedicalRAG:
    """
    Hybrid retrieval over the Pulse medical knowledge base.

    Combines FAISS dense vector search with BM25 sparse keyword scoring
    via Reciprocal Rank Fusion. Falls back to BM25-only if sentence-
    transformers or faiss-cpu are not installed.
    """

    def __init__(self):
        self._chunks = get_all_text_chunks()
        self._index = None
        self._embedder = None
        self._embeddings: Optional[np.ndarray] = None
        self._bm25 = BM25(self._chunks)

        if _ST_AVAILABLE and _FAISS_AVAILABLE:
            self._init_vector_store()

    def _init_vector_store(self) -> None:
        os.makedirs(config.VECTOR_STORE_DIR, exist_ok=True)
        index_path = os.path.join(config.VECTOR_STORE_DIR, "medical.index")
        emb_path = os.path.join(config.VECTOR_STORE_DIR, "medical_embeddings.npy")

        if os.path.exists(index_path) and os.path.exists(emb_path):
            try:
                self._index = faiss.read_index(index_path)
                self._embeddings = np.load(emb_path)
                self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
                return
            except Exception:
                pass

        print("[RAG] Building FAISS index…")
        self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
        texts = [c["content"] for c in self._chunks]
        self._embeddings = self._embedder.encode(texts, show_progress_bar=False).astype(np.float32)

        dim = self._embeddings.shape[1]
        self._index = faiss.IndexFlatL2(dim)
        self._index.add(self._embeddings)

        faiss.write_index(self._index, index_path)
        np.save(emb_path, self._embeddings)
        print(f"[RAG] Index built: {len(texts)} chunks.")

    def retrieve(self, query: str, k: int = 5) -> list[dict]:
        """
        Hybrid retrieval: FAISS + BM25 fused via RRF.
        Falls back to BM25 alone if vector store unavailable.
        """
        pool = k * 2  # over-fetch before merging

        bm25_results = self._bm25.retrieve(query, k=pool)

        if self._index is not None and self._embedder is not None:
            faiss_results = self._faiss_search(query, k=pool)
            merged = _rrf_merge([faiss_results, bm25_results])
        else:
            merged = bm25_results

        # Always include a red-flag chunk if the query touches serious symptoms
        serious_kw = {"headache", "nausea", "pain", "dizzy", "chest", "fever", "stomach"}
        query_words = set(query.lower().split())
        if query_words & serious_kw:
            merged_ids = {c["id"] for c in merged[:k]}
            for chunk in self._chunks:
                if chunk.get("red_flags") and chunk["id"] not in merged_ids:
                    merged.append(chunk)
                    break

        return merged[:k]

    def retrieve_for_symptoms(self, symptoms: list[str], extra_query: str = "", k: int = 5) -> list[dict]:
        query = " ".join(symptoms) + (" " + extra_query if extra_query else "")
        return self.retrieve(query, k=k)

    def _faiss_search(self, query: str, k: int) -> list[dict]:
        q_emb = self._embedder.encode([query], show_progress_bar=False).astype(np.float32)
        distances, indices = self._index.search(q_emb, min(k, len(self._chunks)))
        return [
            {**self._chunks[i], "score": float(distances[0][rank])}
            for rank, i in enumerate(indices[0])
            if i < len(self._chunks)
        ]

    def format_context(self, chunks: list[dict]) -> str:
        parts = []
        for chunk in chunks:
            flag = " ⚠️ RED FLAGS" if chunk.get("red_flags") else ""
            parts.append(f"[SOURCE: {chunk['title']}{flag}]\n{chunk['content'].strip()}")
        return "\n\n---\n\n".join(parts)


# ── Singleton ─────────────────────────────────────────────────────────────────

_rag_instance: Optional[MedicalRAG] = None


def get_rag() -> MedicalRAG:
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = MedicalRAG()
    return _rag_instance


def retrieve_medical_context(symptoms: list[str], query: str = "") -> str:
    rag = get_rag()
    chunks = rag.retrieve_for_symptoms(symptoms, extra_query=query, k=5)
    if not chunks:
        return "No specific medical information found for these symptoms."
    return rag.format_context(chunks)
