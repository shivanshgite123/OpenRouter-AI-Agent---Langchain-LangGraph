"""
Document reranking stage.

Uses the Jina Reranker API when JINA_API_KEY is configured; otherwise falls
back to a simple, dependency-free lexical relevance score so the workflow
degrades gracefully instead of crashing.
"""
from __future__ import annotations

import logging
import re

import requests

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

JINA_RERANK_URL = "https://api.jina.ai/v1/rerank"


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _fallback_score(query: str, documents: list[dict]) -> list[dict]:
    """Overlap-based relevance scoring, used when Jina is unavailable."""
    query_tokens = _tokenize(query)
    scored = []
    for doc in documents:
        doc_tokens = _tokenize(f"{doc.get('title', '')} {doc.get('content', '')}")
        overlap = len(query_tokens & doc_tokens)
        score = overlap / (len(query_tokens) or 1)
        scored.append({**doc, "relevance_score": round(score, 4)})
    scored.sort(key=lambda d: d["relevance_score"], reverse=True)
    return scored


def rerank_documents(query: str, documents: list[dict], top_n: int | None = None) -> list[dict]:
    """Rank documents by relevance to `query`. Never raises."""
    if not documents:
        return []

    settings = get_settings()
    top_n = top_n or len(documents)

    if settings.effective_mock_mode or not settings.jina_api_key:
        return _fallback_score(query, documents)[:top_n]

    try:
        payload = {
            "model": "jina-reranker-v2-base-multilingual",
            "query": query,
            "top_n": top_n,
            "documents": [d.get("content", "")[:2000] for d in documents],
        }
        headers = {
            "Authorization": f"Bearer {settings.jina_api_key}",
            "Content-Type": "application/json",
        }
        resp = requests.post(JINA_RERANK_URL, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])

        ranked = []
        for item in results:
            idx = item.get("index")
            if idx is None or idx >= len(documents):
                continue
            ranked.append({**documents[idx], "relevance_score": item.get("relevance_score", 0.0)})
        return ranked or _fallback_score(query, documents)[:top_n]

    except Exception as exc:  # noqa: BLE001
        logger.warning("Jina reranker failed, falling back to lexical scoring: %s", exc)
        return _fallback_score(query, documents)[:top_n]
