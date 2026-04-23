"""Unit tests for app/config.py production guards."""
import os
import subprocess
import sys

import pytest

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def _run_config(env_overrides: dict) -> subprocess.CompletedProcess:
    """Import app.config in a subprocess with the given env overrides."""
    env = os.environ.copy()
    # Prevent dotenv from overriding our test values (they're already set)
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-c", "import app.config"],
        capture_output=True,
        text=True,
        cwd=_PROJECT_ROOT,
        env=env,
    )


def test_production_missing_api_key_raises():
    result = _run_config({
        "APP_ENV": "production",
        "INTERNAL_API_KEY": "",
        "ALLOWED_ORIGINS": "https://api.example.com",
    })
    assert result.returncode != 0
    assert "INTERNAL_API_KEY" in result.stderr


def test_production_wildcard_cors_raises():
    result = _run_config({
        "APP_ENV": "production",
        "INTERNAL_API_KEY": "strong-secret",
        "ALLOWED_ORIGINS": "*",
    })
    assert result.returncode != 0
    assert "ALLOWED_ORIGINS" in result.stderr


def test_production_valid_config_loads():
    result = _run_config({
        "APP_ENV": "production",
        "INTERNAL_API_KEY": "strong-secret",
        "ALLOWED_ORIGINS": "https://api.example.com",
    })
    assert result.returncode == 0


def test_development_empty_key_is_ok():
    result = _run_config({
        "APP_ENV": "development",
        "INTERNAL_API_KEY": "",
        "ALLOWED_ORIGINS": "http://localhost:8080",
    })
    assert result.returncode == 0


def test_development_wildcard_cors_is_ok():
    result = _run_config({
        "APP_ENV": "development",
        "INTERNAL_API_KEY": "",
        "ALLOWED_ORIGINS": "*",
    })
    assert result.returncode == 0
