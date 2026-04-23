"""
Shared fixtures for the chatbot-server test suite.

Module-level os.environ assignments run at collection time,
BEFORE any app.* module is imported, so config picks them up correctly.
"""
import os
from unittest.mock import AsyncMock, patch

import pytest

# ── Set test env BEFORE app.* imports ──────────────────────────────────────
os.environ["APP_ENV"] = "development"
os.environ["INTERNAL_API_KEY"] = "test-secret-key"
os.environ["GEMINI_API_KEY"] = ""
os.environ["LLM_ENABLED"] = "true"
os.environ["DEBUG"] = "true"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:8080,http://localhost:3000"
os.environ["LOG_LEVEL"] = "WARNING"   # silence logs during tests


# ── App / client ────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def app():
    from app.main import app as _app
    return _app


@pytest.fixture(scope="session")
def client(app):
    from fastapi.testclient import TestClient
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ── Common helpers ──────────────────────────────────────────────────────────

@pytest.fixture
def auth_headers():
    return {"X-Internal-API-Key": "test-secret-key"}


# ── Rate-limit isolation ────────────────────────────────────────────────────
# slowapi captures key_func in Limit objects at decoration time, so patching
# limiter._key_func has no effect. Instead, call limiter.reset() which clears
# the in-memory MemoryStorage before each test.

@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    from app.limiter import limiter
    limiter.reset()
    yield
    limiter.reset()


# ── LLM mocks ───────────────────────────────────────────────────────────────

@pytest.fixture
def mock_chat_response():
    """Patch get_chat_response so /api/chat never calls Gemini."""
    with patch(
        "app.routers.chat.get_chat_response",
        new=AsyncMock(return_value=("Mock LLM yanıtı.", ["Soru 1?", "Soru 2?"])),
    ) as m:
        yield m


@pytest.fixture
def mock_llm_stream():
    """Patch _iter_llm_stream so /api/chat/stream never calls Gemini."""
    def _fake(msg, history, system_override=None):
        yield "Chunk bir. "
        yield "Chunk iki."

    with patch("app.routers.chat._iter_llm_stream", side_effect=_fake) as m:
        yield m


@pytest.fixture
def gemini_enabled(monkeypatch):
    """Activate the LLM code path by exposing a fake API key."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake-gemini-key")
    import app.config as cfg
    import app.routers.chat as chat_mod
    monkeypatch.setattr(cfg, "GEMINI_API_KEY", "fake-gemini-key")
    monkeypatch.setattr(chat_mod, "GEMINI_API_KEY", "fake-gemini-key", raising=False)
    # Also patch chatbot service so health checks and service calls see the key
    import app.services.chatbot as svc
    monkeypatch.setattr(svc, "GEMINI_API_KEY", "fake-gemini-key")
