"""
Security tests — error response safety (validates Fix 1).

These tests verify that raw exception messages are NEVER sent to clients.
Before Fix 1 they would FAIL; after Fix 1 they PASS and act as regression guards.
"""
import json
from unittest.mock import AsyncMock, patch

import pytest

_SENSITIVE = "Connection refused: postgresql://admin:mysecret@db:5432/prod"


def test_chat_500_does_not_expose_exception_message(client, auth_headers):
    with patch(
        "app.routers.chat.get_chat_response",
        new=AsyncMock(side_effect=RuntimeError(_SENSITIVE)),
    ):
        r = client.post("/api/chat", json={"message": "hello"}, headers=auth_headers)

    assert r.status_code == 500
    assert _SENSITIVE not in r.text
    assert "mysecret" not in r.text


def test_chat_500_returns_generic_detail(client, auth_headers):
    with patch(
        "app.routers.chat.get_chat_response",
        new=AsyncMock(side_effect=RuntimeError(_SENSITIVE)),
    ):
        r = client.post("/api/chat", json={"message": "hello"}, headers=auth_headers)

    body = r.json()
    assert "detail" in body
    assert body["detail"] == "Internal server error"


def test_stream_error_does_not_expose_exception(client, auth_headers, gemini_enabled):
    with patch(
        "app.routers.chat._iter_llm_stream",
        side_effect=RuntimeError(_SENSITIVE),
    ):
        r = client.post(
            "/api/chat/stream",
            json={"message": "xyz alakasiz 999", "intent": "LEGAL_QUESTION"},
            headers=auth_headers,
        )

    assert _SENSITIVE not in r.text
    assert "mysecret" not in r.text


def test_stream_error_event_has_generic_message(client, auth_headers, gemini_enabled):
    with patch(
        "app.routers.chat._iter_llm_stream",
        side_effect=RuntimeError(_SENSITIVE),
    ):
        r = client.post(
            "/api/chat/stream",
            json={"message": "xyz alakasiz 999", "intent": "LEGAL_QUESTION"},
            headers=auth_headers,
        )

    # Find the error event in the SSE stream
    for line in r.text.splitlines():
        if line.startswith("data: "):
            event = json.loads(line[6:])
            if "error" in event:
                assert event["error"] != _SENSITIVE
                assert event["error"] == "Stream error"
                break


def test_422_does_not_expose_server_file_paths(client, auth_headers):
    r = client.post("/api/chat", json={"message": ""}, headers=auth_headers)
    assert r.status_code == 422
    assert "/home/" not in r.text
    assert "/usr/" not in r.text


def test_401_response_has_no_traceback(client):
    r = client.post("/api/chat", json={"message": "x"}, headers={})
    assert r.status_code == 401
    assert "Traceback" not in r.text
    assert "File " not in r.text


def test_500_response_has_no_python_traceback(client, auth_headers):
    with patch(
        "app.routers.chat.get_chat_response",
        new=AsyncMock(side_effect=RuntimeError("kaboom")),
    ):
        r = client.post("/api/chat", json={"message": "hello"}, headers=auth_headers)

    assert "Traceback" not in r.text
    assert "line " not in r.text
