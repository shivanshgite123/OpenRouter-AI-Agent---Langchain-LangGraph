import time

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_start_and_poll_research():
    resp = client.post("/api/research", json={"question": "What is 2+2 and why does it matter?"})
    assert resp.status_code == 200
    research_id = resp.json()["research_id"]
    assert resp.json()["status"] == "started"

    # background task runs on the TestClient's event loop synchronously
    # enough for mock mode; poll briefly to be safe.
    for _ in range(20):
        status_resp = client.get(f"/api/research/{research_id}/status")
        assert status_resp.status_code == 200
        if status_resp.json()["status"] == "completed":
            break
        time.sleep(0.2)

    result_resp = client.get(f"/api/research/{research_id}")
    assert result_resp.status_code == 200
    assert result_resp.json()["research_id"] == research_id


def test_unknown_research_id_returns_404():
    resp = client.get("/api/research/does-not-exist")
    assert resp.status_code == 404
