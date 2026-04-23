"""Integration tests for POST /api/chat/stream (SSE)."""
import json

import pytest


def _parse_sse(body: str) -> list[dict]:
    """Parse SSE text/event-stream body into list of JSON event payloads."""
    events = []
    for line in body.splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


# ── Content-type and format ──────────────────────────────────────────────────

def test_stream_content_type_is_sse(client, auth_headers):
    r = client.post("/api/chat/stream", json={"message": "merhaba"}, headers=auth_headers)
    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]


def test_stream_lines_prefixed_with_data(client, auth_headers):
    r = client.post("/api/chat/stream", json={"message": "merhaba"}, headers=auth_headers)
    for line in r.text.splitlines():
        if line.strip():
            assert line.startswith("data: "), f"Unexpected SSE line: {line!r}"


def test_stream_events_separated_by_double_newline(client, auth_headers):
    r = client.post("/api/chat/stream", json={"message": "merhaba"}, headers=auth_headers)
    assert "\n\n" in r.text


# ── FAQ path (no Gemini needed) ──────────────────────────────────────────────

def test_stream_faq_match_first_event_has_text(client, auth_headers):
    r = client.post("/api/chat/stream", json={"message": "merhaba"}, headers=auth_headers)
    events = _parse_sse(r.text)
    assert any("text" in e for e in events)


def test_stream_faq_match_last_event_done(client, auth_headers):
    r = client.post("/api/chat/stream", json={"message": "merhaba"}, headers=auth_headers)
    events = _parse_sse(r.text)
    last = events[-1]
    assert last.get("done") is True


def test_stream_faq_match_suggestions_in_last_event(client, auth_headers):
    r = client.post("/api/chat/stream", json={"message": "merhaba"}, headers=auth_headers)
    events = _parse_sse(r.text)
    last = events[-1]
    assert isinstance(last.get("suggestions"), list)


# ── Fallback path (no Gemini key) ───────────────────────────────────────────

def test_stream_no_gemini_key_returns_fallback(client, auth_headers):
    # GEMINI_API_KEY="" in test env — no FAQ match for this message
    r = client.post(
        "/api/chat/stream",
        json={"message": "xyz alakasiz metin 999", "intent": "LEGAL_QUESTION"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    events = _parse_sse(r.text)
    last = events[-1]
    assert last.get("done") is True


# ── LLM path (with Gemini mock) ──────────────────────────────────────────────

def test_stream_llm_chunks_emitted(client, auth_headers, gemini_enabled, mock_llm_stream):
    r = client.post(
        "/api/chat/stream",
        json={"message": "xyz alakasiz metin 999", "intent": "LEGAL_QUESTION"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    events = _parse_sse(r.text)
    text_events = [e for e in events if "text" in e]
    assert len(text_events) >= 2  # at least the mock chunks


def test_stream_llm_done_event_has_suggestions(client, auth_headers, gemini_enabled, mock_llm_stream):
    r = client.post(
        "/api/chat/stream",
        json={"message": "xyz alakasiz metin 999", "intent": "LEGAL_QUESTION"},
        headers=auth_headers,
    )
    events = _parse_sse(r.text)
    last = events[-1]
    assert last.get("done") is True
    assert isinstance(last.get("suggestions"), list)


# ── Validation ───────────────────────────────────────────────────────────────

def test_stream_no_auth_returns_401(client):
    r = client.post("/api/chat/stream", json={"message": "merhaba"})
    assert r.status_code == 401


def test_stream_empty_message_returns_422(client, auth_headers):
    r = client.post("/api/chat/stream", json={"message": ""}, headers=auth_headers)
    assert r.status_code == 422


def test_stream_message_too_long_returns_422(client, auth_headers):
    r = client.post("/api/chat/stream", json={"message": "a" * 2001}, headers=auth_headers)
    assert r.status_code == 422
