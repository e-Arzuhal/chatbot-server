"""Integration tests for POST /api/chat."""
import pytest


# ── Happy paths ──────────────────────────────────────────────────────────────

def test_chat_faq_merhaba(client, auth_headers):
    r = client.post("/api/chat", json={"message": "merhaba"}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert "response" in body
    assert isinstance(body["suggested_questions"], list)


def test_chat_faq_pdf(client, auth_headers):
    r = client.post("/api/chat", json={"message": "pdf indir"}, headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()["response"]) > 0


def test_chat_faq_onay(client, auth_headers):
    r = client.post("/api/chat", json={"message": "onay sureci"}, headers=auth_headers)
    assert r.status_code == 200


def test_chat_faq_no_match_returns_fallback(client, auth_headers):
    r = client.post(
        "/api/chat",
        json={"message": "tamamen alakasiz xyz999 metin"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert "response" in body


def test_chat_with_history(client, auth_headers):
    history = [
        {"role": "user", "content": "Nasılsın?"},
        {"role": "assistant", "content": "İyiyim, teşekkürler!"},
    ]
    r = client.post(
        "/api/chat",
        json={"message": "merhaba", "history": history},
        headers=auth_headers,
    )
    assert r.status_code == 200


def test_chat_camelcase_fields_accepted(client, auth_headers):
    r = client.post(
        "/api/chat",
        json={
            "message": "soru",
            "sanitizedMessage": "temiz soru",
            "contractContext": "sözleşme içeriği",
        },
        headers=auth_headers,
    )
    assert r.status_code == 200


def test_chat_with_intent_general_help_uses_faq(client, auth_headers):
    r = client.post(
        "/api/chat",
        json={"message": "merhaba", "intent": "GENERAL_HELP"},
        headers=auth_headers,
    )
    assert r.status_code == 200


def test_chat_with_intent_legal_question_uses_llm(client, auth_headers, gemini_enabled, mock_chat_response):
    r = client.post(
        "/api/chat",
        json={"message": "bu madde nedir", "intent": "LEGAL_QUESTION"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    mock_chat_response.assert_called_once()


def test_chat_response_has_correct_schema(client, auth_headers):
    r = client.post("/api/chat", json={"message": "merhaba"}, headers=auth_headers)
    body = r.json()
    assert set(body.keys()) == {"response", "suggested_questions"}
    assert isinstance(body["response"], str)
    assert isinstance(body["suggested_questions"], list)


# ── Validation (422) ─────────────────────────────────────────────────────────

def test_chat_empty_message_rejected(client, auth_headers):
    r = client.post("/api/chat", json={"message": ""}, headers=auth_headers)
    assert r.status_code == 422


def test_chat_message_too_long_rejected(client, auth_headers):
    r = client.post("/api/chat", json={"message": "a" * 2001}, headers=auth_headers)
    assert r.status_code == 422


def test_chat_history_too_long_rejected(client, auth_headers):
    history = [{"role": "user", "content": "x"} for _ in range(21)]
    r = client.post(
        "/api/chat",
        json={"message": "hello", "history": history},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_chat_missing_message_field_rejected(client, auth_headers):
    r = client.post("/api/chat", json={"history": []}, headers=auth_headers)
    assert r.status_code == 422


def test_chat_invalid_json_rejected(client, auth_headers):
    r = client.post(
        "/api/chat",
        content=b"not json",
        headers={**auth_headers, "Content-Type": "application/json"},
    )
    assert r.status_code == 422
