import os
from rank_bm25 import BM25Okapi
from backend.embeddings.embedder import Embedder
from backend.vectorstore.store import VectorStore


class Retriever:

    def __init__(self, rrf_k=60):
        self.embedder = Embedder()
        self.store = VectorStore()
        self.rrf_k = rrf_k  # RRF constant — 60 is standard
        self._corpus = []   # list of (text, metadata)
        self._bm25 = None
        self._build_bm25_index()

    def _build_bm25_index(self):
        """Load all docs from ChromaDB and build a BM25 index over them."""
        try:
            results = self.store.collection.get(include=["documents", "metadatas"])
            docs = results.get("documents", [])
            metas = results.get("metadatas", [])
            if not docs:
                return
            self._corpus = list(zip(docs, metas))
            tokenized = [doc.lower().split() for doc in docs]
            self._bm25 = BM25Okapi(tokenized)
        except Exception as e:
            print(f"BM25 index build failed: {e}")

    def _dense_retrieve(self, question, n_results=10):
        """Return ranked list of (text, metadata, cosine_similarity)."""
        query_emb = self.embedder.embed(question)[0]
        results = self.store.query(query_emb, n_results=n_results)
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        scores = [round(1 - d, 4) for d in distances]
        return list(zip(docs, metas, scores))

    def _bm25_retrieve(self, question, n_results=10):
        """Return ranked list of (text, metadata, bm25_score_normalized)."""
        if not self._bm25 or not self._corpus:
            return []
        tokens = question.lower().split()
        raw_scores = self._bm25.get_scores(tokens)

        # Normalize to 0–1
        max_score = max(raw_scores) if max(raw_scores) > 0 else 1
        top_indices = sorted(range(len(raw_scores)), key=lambda i: raw_scores[i], reverse=True)[:n_results]

        return [
            (self._corpus[i][0], self._corpus[i][1], round(raw_scores[i] / max_score, 4))
            for i in top_indices
        ]

    def _rrf_merge(self, dense_results, bm25_results, top_k=5):
        """
        Reciprocal Rank Fusion — combines rankings without needing to tune alpha.
        Score = sum(1 / (k + rank)) across both result lists.
        """
        rrf_scores = {}  # text -> {"rrf": float, "dense": float, "bm25": float, "meta": dict}

        for rank, (text, meta, score) in enumerate(dense_results):
            key = text[:100]  # dedupe key
            if key not in rrf_scores:
                rrf_scores[key] = {"text": text, "meta": meta, "rrf": 0.0, "dense": 0.0, "bm25": 0.0}
            rrf_scores[key]["rrf"] += 1 / (self.rrf_k + rank + 1)
            rrf_scores[key]["dense"] = score

        for rank, (text, meta, score) in enumerate(bm25_results):
            key = text[:100]
            if key not in rrf_scores:
                rrf_scores[key] = {"text": text, "meta": meta, "rrf": 0.0, "dense": 0.0, "bm25": 0.0}
            rrf_scores[key]["rrf"] += 1 / (self.rrf_k + rank + 1)
            rrf_scores[key]["bm25"] = score

        merged = sorted(rrf_scores.values(), key=lambda x: x["rrf"], reverse=True)[:top_k]

        # Normalize RRF scores to 0–1 for display
        max_rrf = merged[0]["rrf"] if merged else 1
        for item in merged:
            item["rrf"] = round(item["rrf"] / max_rrf, 3)

        return merged

    def retrieve(self, question, top_k=5):
        dense_results = self._dense_retrieve(question, n_results=10)
        bm25_results = self._bm25_retrieve(question, n_results=10)

        merged = self._rrf_merge(dense_results, bm25_results, top_k=top_k)

        chunks = [
            {
                "text": item["text"],
                "file": item["meta"].get("file", "unknown"),
                "score": item["rrf"],        # final merged score
                "dense_score": item["dense"], # semantic similarity
                "bm25_score": item["bm25"],   # keyword match
            }
            for item in merged
        ]

        source_files = list(set(c["file"] for c in chunks))
        return chunks, source_files