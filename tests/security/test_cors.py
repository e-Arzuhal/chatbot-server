"""Security tests — CORS configuration."""


def test_allowed_origin_gets_cors_header(client):
    r = client.get("/", headers={"Origin": "http://localhost:8080"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:8080"


def test_second_allowed_origin_gets_cors_header(client):
    r = client.get("/", headers={"Origin": "http://localhost:3000"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_disallowed_origin_gets_no_cors_header(client):
    r = client.get("/", headers={"Origin": "http://evil.com"})
    assert r.headers.get("access-control-allow-origin") is None


def test_no_wildcard_in_cors_response(client):
    r = client.get("/", headers={"Origin": "http://localhost:8080"})
    assert r.headers.get("access-control-allow-origin") != "*"


def test_credentials_not_allowed(client):
    """allow_credentials=False — header must not be 'true'."""
    r = client.get("/", headers={"Origin": "http://localhost:8080"})
    allow_creds = r.headers.get("access-control-allow-credentials", "false")
    assert allow_creds.lower() != "true"


def test_cors_present_without_auth_on_public_endpoint(client):
    """CORS headers are added to public endpoints without any API key."""
    r = client.get("/health", headers={"Origin": "http://localhost:8080"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:8080"
