"""
LangChain-compatible web search tool, backed by Tavily.

Reused/refactored from the project's original tools.py, extended to:
- support MOCK_MODE (no API key required)
- return structured results (title/url/snippet/score) instead of a single
  flattened string, and run several queries.
"""
from __future__ import annotations

import logging

from langchain_core.tools import tool

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


def _mock_search_results(query: str, max_results: int) -> list[dict]:
    return [
        {
            "title": f"Mock result {i + 1} for '{query}'",
            "url": f"https://example.com/mock/{query.replace(' ', '-').lower()}/{i + 1}",
            "content": (
                f"This is simulated search content #{i + 1} related to '{query}'. "
                "It exists so the workflow can be exercised end-to-end without a "
                "TAVILY_API_KEY. Enable a real key to get live results."
            ),
            "score": round(1.0 - i * 0.1, 2),
        }
        for i in range(max_results)
    ]


def run_web_search(query: str, max_results: int | None = None) -> list[dict]:
    """Execute a single web search and return structured results.

    Never raises: on any failure it logs the error and returns an empty list
    so a single bad query cannot crash the workflow.
    """
    settings = get_settings()
    max_results = max_results or settings.max_search_results

    if settings.effective_mock_mode or not settings.tavily_api_key:
        return _mock_search_results(query, min(max_results, 5))

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=settings.tavily_api_key)
        response = client.search(query=query, max_results=max_results)
        results = []
        for r in response.get("results", []):
            results.append(
                {
                    "title": r.get("title", "Untitled"),
                    "url": r.get("url", ""),
                    "content": r.get("content", "")[:500],
                    "score": r.get("score"),
                }
            )
        return results
    except Exception as exc:  # noqa: BLE001 - a failed search must not crash the graph
        logger.warning("web_search failed for query %r: %s", query, exc)
        return []


def run_web_search_batch(queries: list[str], max_results: int | None = None) -> list[dict]:
    """Run several search queries and return a flat, de-duplicated (by URL) list."""
    seen_urls: set[str] = set()
    combined: list[dict] = []
    for q in queries:
        for r in run_web_search(q, max_results=max_results):
            url = r.get("url", "")
            if url and url in seen_urls:
                continue
            seen_urls.add(url)
            r["query"] = q
            combined.append(r)
    return combined


@tool
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic.
    Returns titles, URLs, and snippets as formatted text."""
    results = run_web_search(query)
    if not results:
        return f"No search results found for: {query}"
    out = [
        f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['content'][:300]}"
        for r in results
    ]
    return "\n----\n".join(out)
