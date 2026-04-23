"""Integration tests for POST /api/feedback."""


# ── Happy paths ──────────────────────────────────────────────────────────────

def test_feedback_valid_returns_204(client, auth_headers):
    r = client.post(
        "/api/feedback",
        json={"message": "sözleşme nasıl yapılır", "response": "Sol menüden tıklayın.", "rating": 5},
        headers=auth_headers,
    )
    assert r.status_code == 204


def test_feedback_204_has_no_body(client, auth_headers):
    r = client.post(
        "/api/feedback",
        json={"message": "test", "response": "ok", "rating": 3},
        headers=auth_headers,
    )
    assert r.content == b""


def test_feedback_rating_boundary_1(client, auth_headers):
    r = client.post(
        "/api/feedback",
        json={"message": "test", "response": "ok", "rating": 1},
        headers=auth_headers,
    )
    assert r.status_code == 204


def test_feedback_rating_boundary_5(client, auth_headers):
    r = client.post(
        "/api/feedback",
        json={"message": "test", "response": "ok", "rating": 5},
        headers=auth_headers,
    )
    assert r.status_code == 204


def test_feedback_with_optional_intent(client, auth_headers):
    r = client.post(
        "/api/feedback",
        json={"message": "test", "response": "ok", "rating": 3, "intent": "LEGAL_QUESTION"},
        headers=auth_headers,
    )
    assert r.status_code == 204


# ── Validation (422) ─────────────────────────────────────────────────────────

def test_feedback_rating_0_rejected(client, auth_headers):
    r = client.post(
        "/api/feedback",
        json={"message": "test", "response": "ok", "rating": 0},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_feedback_rating_6_rejected(client, auth_headers):
    r = client.post(
        "/api/feedback",
        json={"message": "test", "response": "ok", "rating": 6},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_feedback_missing_rating_rejected(client, auth_headers):
    r = client.post(
        "/api/feedback",
        json={"message": "test", "response": "ok"},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_feedback_missing_message_rejected(client, auth_headers):
    r = client.post(
        "/api/feedback",
        json={"response": "ok", "rating": 3},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_feedback_missing_response_rejected(client, auth_headers):
    r = client.post(
        "/api/feedback",
        json={"message": "test", "rating": 3},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_feedback_empty_message_rejected(client, auth_headers):
    r = client.post(
        "/api/feedback",
        json={"message": "", "response": "ok", "rating": 3},
        headers=auth_headers,
    )
    assert r.status_code == 422


# ── Auth ─────────────────────────────────────────────────────────────────────

def test_feedback_no_api_key_returns_401(client):
    r = client.post(
        "/api/feedback",
        json={"message": "test", "response": "ok", "rating": 3},
    )
    assert r.status_code == 401
