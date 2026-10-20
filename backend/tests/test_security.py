"""
Tests for security: Rate limiting, path traversal, error sanitization, and secret protection.
"""
from app.config import settings
from app.utils.rate_limiter import reset_rate_limits


def test_rate_limiting(client, monkeypatch):
    """Bug 13: Expensive endpoints enforce rate limits."""
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 3)
    reset_rate_limits()

    # Perform 3 requests
    for _ in range(3):
        res = client.post("/api/documents/non_existent/query", json={"question": "Test?"})
        # Could be 404 since doc doesn't exist, but NOT 429
        assert res.status_code != 429

    # 4th request must trigger 429
    res4 = client.post("/api/documents/non_existent/query", json={"question": "Test?"})
    assert res4.status_code == 429
    assert "Rate limit exceeded" in res4.json()["detail"]


def test_health_check_does_not_leak_key(client, monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "super_secret_api_key_12345")
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["gemini_key_configured"] is True
    # Key string itself must never appear in response
    assert "super_secret_api_key_12345" not in res.text


def test_directory_traversal_prevention(client):
    res = client.get("/api/documents/../../etc/passwd/file")
    assert res.status_code in [404, 400]
    res2 = client.get("/api/documents/non_existent_id/file")
    assert res2.status_code == 404
