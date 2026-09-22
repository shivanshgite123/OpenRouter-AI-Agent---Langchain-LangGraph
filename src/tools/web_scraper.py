"""
Reader / web-content extraction tool.

Refactored from the project's original tools.py scrape_url. Adds robust
error handling (timeouts, invalid URLs, empty pages) so a single bad source
never takes down the whole research run, plus a document object with
preserved metadata.
"""
from __future__ import annotations

import logging

import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


def _mock_document(url: str, title: str, query: str) -> dict:
    return {
        "title": title,
        "url": url,
        "source": url.split("/")[2] if "//" in url else url,
        "query": query,
        "content": (
            f"Simulated extracted content for '{title}'. In MOCK_MODE no real "
            "network request is made; this placeholder stands in for cleaned "
            "page text so downstream reranking/analysis can still run."
        ),
        "error": None,
    }


def extract_document(result: dict) -> dict:
    """Fetch and clean a single search result into a document object.

    Never raises. On any failure the returned document carries an `error`
    field and empty content rather than crashing the caller.
    """
    settings = get_settings()
    url = result.get("url", "")
    title = result.get("title", "Untitled")
    query = result.get("query", "")

    if settings.effective_mock_mode or not url:
        return _mock_document(url or "https://example.com/mock", title, query)

    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        text = " ".join(text.split())[: settings.max_scrape_chars]

        if not text:
            return {
                "title": title, "url": url, "source": url, "query": query,
                "content": result.get("content", ""), "error": "empty_page",
            }

        return {"title": title, "url": url, "source": url, "query": query, "content": text, "error": None}

    except requests.exceptions.Timeout:
        logger.warning("Timeout scraping %s", url)
        return {"title": title, "url": url, "source": url, "query": query,
                "content": result.get("content", ""), "error": "timeout"}
    except requests.exceptions.RequestException as exc:
        logger.warning("HTTP error scraping %s: %s", url, exc)
        return {"title": title, "url": url, "source": url, "query": query,
                "content": result.get("content", ""), "error": "http_error"}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Unexpected error scraping %s: %s", url, exc)
        return {"title": title, "url": url, "source": url, "query": query,
                "content": result.get("content", ""), "error": "unknown_error"}


def extract_documents(results: list[dict], limit: int | None = None) -> list[dict]:
    """Extract documents for a list of search results, skipping duplicate URLs."""
    seen: set[str] = set()
    docs: list[dict] = []
    for r in results:
        url = r.get("url", "")
        if url in seen:
            continue
        seen.add(url)
        docs.append(extract_document(r))
        if limit and len(docs) >= limit:
            break
    return docs


@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean text content from a given URL for deeper reading."""
    doc = extract_document({"url": url, "title": url, "query": ""})
    if doc.get("error"):
        return f"Could not scrape URL ({doc['error']}): {url}"
    return doc["content"]
