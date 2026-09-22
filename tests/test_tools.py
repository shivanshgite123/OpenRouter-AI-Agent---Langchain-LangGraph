from src.tools.calculator import UnsafeExpressionError, safe_calculate, cagr, percentage_change
from src.tools.reranker import rerank_documents
from src.tools.web_scraper import extract_document
from src.tools.web_search import run_web_search, run_web_search_batch


def test_web_search_mock_mode_returns_results():
    results = run_web_search("test query")
    assert results
    assert all("url" in r and "title" in r for r in results)


def test_web_search_batch_dedupes_urls():
    results = run_web_search_batch(["q1", "q2"])
    urls = [r["url"] for r in results]
    assert len(urls) == len(set(urls))


def test_web_scraper_mock_mode_never_raises():
    doc = extract_document({"url": "https://example.com/x", "title": "X", "query": "q"})
    assert doc["url"]
    assert doc["error"] is None


def test_reranker_fallback_orders_by_overlap():
    docs = [
        {"title": "cats", "content": "all about cats and dogs"},
        {"title": "unrelated", "content": "completely different topic"},
    ]
    ranked = rerank_documents("cats and dogs", docs)
    assert ranked[0]["title"] == "cats"


def test_calculator_safe_expression():
    assert safe_calculate("2 + 2 * 3") == 8


def test_calculator_rejects_unsafe_input():
    try:
        safe_calculate("__import__('os').system('echo hi')")
        assert False, "should have raised"
    except UnsafeExpressionError:
        pass


def test_calculator_percentage_and_cagr():
    assert percentage_change(100, 150) == 50.0
    assert cagr(100, 200, 5) > 0
