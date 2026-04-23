"""Security tests — rate limiting (slowapi 5/minute per IP)."""
import pytest


# The _isolate_rate_limit autouse fixture in conftest.py gives each test its
# own virtual IP key, so these tests don't interfere with each other.


def test_first_five_requests_succeed(client, auth_headers):
    for i in range(5):
        r = client.post("/api/chat", json={"message": "merhaba"}, headers=auth_headers)
        assert r.status_code == 200, f"Request {i+1} failed with {r.status_code}"


def test_sixth_request_is_rate_limited(client, auth_headers):
    for _ in range(5):
        client.post("/api/chat", json={"message": "merhaba"}, headers=auth_headers)
    r = client.post("/api/chat", json={"message": "merhaba"}, headers=auth_headers)
    assert r.status_code == 429


def test_rate_limit_response_body_contains_error(client, auth_headers):
    for _ in range(5):
        client.post("/api/chat", json={"message": "merhaba"}, headers=auth_headers)
    r = client.post("/api/chat", json={"message": "merhaba"}, headers=auth_headers)
    assert r.status_code == 429
    body = r.json()
    # slowapi returns {"error": "Rate limit exceeded: ..."} on 429
    assert "error" in body or "detail" in body


def test_stream_endpoint_has_independent_rate_limit(client, auth_headers):
    """Chat and stream use separate limit counters."""
    # Exhaust the /api/chat limit
    for _ in range(5):
        client.post("/api/chat", json={"message": "merhaba"}, headers=auth_headers)
    # /api/chat/stream counter is still fresh
    r = client.post("/api/chat/stream", json={"message": "merhaba"}, headers=auth_headers)
    assert r.status_code == 200


def test_public_endpoints_not_rate_limited(client):
    """/ and /health have no rate-limit decorator — many requests must succeed."""
    for _ in range(15):
        r = client.get("/health")
        assert r.status_code == 200
