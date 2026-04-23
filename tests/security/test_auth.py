"""Security tests — authentication middleware."""
import pytest

_PROTECTED = [
    ("POST", "/api/chat",        {"message": "hello"}),
    ("POST", "/api/chat/stream", {"message": "hello"}),
    ("POST", "/api/feedback",    {"message": "x", "response": "y", "rating": 3}),
]


@pytest.mark.parametrize("method,path,body", _PROTECTED)
def test_no_api_key_returns_401(client, method, path, body):
    r = client.request(method, path, json=body, headers={})
    assert r.status_code == 401


@pytest.mark.parametrize("method,path,body", _PROTECTED)
def test_wrong_api_key_returns_401(client, method, path, body):
    r = client.request(method, path, json=body, headers={"X-Internal-API-Key": "wrong-key"})
    assert r.status_code == 401


@pytest.mark.parametrize("method,path,body", _PROTECTED)
def test_empty_api_key_returns_401(client, method, path, body):
    r = client.request(method, path, json=body, headers={"X-Internal-API-Key": ""})
    assert r.status_code == 401


def test_401_does_not_reveal_real_key(client):
    r = client.post("/api/chat", json={"message": "x"}, headers={"X-Internal-API-Key": "wrong"})
    assert r.status_code == 401
    # The actual configured key must never appear in the error response
    assert "test-secret-key" not in r.text


def test_api_key_comparison_is_case_sensitive(client):
    r = client.post("/api/chat", json={"message": "x"}, headers={"X-Internal-API-Key": "TEST-SECRET-KEY"})
    assert r.status_code == 401


def test_public_root_no_key_needed(client):
    assert client.get("/").status_code == 200


def test_public_health_no_key_needed(client):
    assert client.get("/health").status_code == 200


def test_misconfigured_server_returns_503(client, monkeypatch):
    """When INTERNAL_API_KEY is not set, protected endpoints return 503."""
    import app.main as main_mod
    monkeypatch.setattr(main_mod, "INTERNAL_API_KEY", "")
    r = client.post("/api/chat", json={"message": "hello"}, headers={"X-Internal-API-Key": "anything"})
    assert r.status_code == 503


def test_401_body_is_json(client):
    r = client.post("/api/chat", json={"message": "x"}, headers={})
    assert r.status_code == 401
    body = r.json()
    assert "detail" in body


def test_401_no_traceback_in_response(client):
    r = client.post("/api/chat", json={"message": "x"}, headers={})
    assert "traceback" not in r.text.lower()
    assert "File " not in r.text
