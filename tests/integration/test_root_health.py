"""Integration tests for GET / and GET /health endpoints."""


def test_root_returns_200(client):
    r = client.get("/")
    assert r.status_code == 200


def test_root_returns_service_name(client):
    r = client.get("/")
    assert r.json()["service"] == "e-Arzuhal Chatbot Server"


def test_root_contains_version(client):
    r = client.get("/")
    assert "version" in r.json()


def test_root_no_api_key_required(client):
    r = client.get("/", headers={})
    assert r.status_code == 200


def test_health_returns_200(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_health_status_healthy(client):
    r = client.get("/health")
    assert r.json()["status"] == "healthy"


def test_health_has_version(client):
    r = client.get("/health")
    assert "version" in r.json()


def test_health_llm_status_valid_value(client):
    r = client.get("/health")
    assert r.json()["llm_status"] in ("ok", "disabled", "error")


def test_health_llm_disabled_when_no_gemini_key(client):
    # GEMINI_API_KEY="" in the test env (set in conftest.py)
    r = client.get("/health")
    assert r.json()["llm_status"] == "disabled"


def test_health_no_api_key_required(client):
    r = client.get("/health", headers={})
    assert r.status_code == 200


def test_health_content_type_json(client):
    r = client.get("/health")
    assert "application/json" in r.headers["content-type"]
