"""Tests for provider health checks."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pocketflow_creator.app.provider_health import check_lm_studio, check_ollama


def test_ollama_health_check_success() -> None:
    """Test ollama health check when service is running."""
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"models": [{"name": "llama2"}]}'
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=mock_response):
        assert check_ollama() is True


def test_ollama_health_check_failure_connection() -> None:
    """Test ollama health check when service is offline."""
    with patch("urllib.request.urlopen", side_effect=ConnectionError("refused")):
        assert check_ollama() is False


def test_ollama_health_check_timeout() -> None:
    """Test ollama health check timeout."""
    with patch("urllib.request.urlopen", side_effect=TimeoutError("timeout")):
        assert check_ollama() is False


def test_ollama_health_check_invalid_response() -> None:
    """Test ollama health check with invalid JSON response."""
    with patch("urllib.request.urlopen", side_effect=ValueError("invalid json")):
        assert check_ollama() is False


def test_lm_studio_health_check_success() -> None:
    """Test LM Studio health check when service is running."""
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"data": [{"id": "gpt-3.5"}]}'
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=mock_response):
        assert check_lm_studio() is True


def test_lm_studio_health_check_failure_connection() -> None:
    """Test LM Studio health check when service is offline."""
    with patch("urllib.request.urlopen", side_effect=ConnectionError("refused")):
        assert check_lm_studio() is False


def test_lm_studio_health_check_timeout() -> None:
    """Test LM Studio health check timeout."""
    with patch("urllib.request.urlopen", side_effect=TimeoutError("timeout")):
        assert check_lm_studio() is False


def test_ollama_custom_base_url() -> None:
    """Test ollama health check with custom base URL."""
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"models": []}'
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=mock_response) as mock_open:
        assert check_ollama(base_url="http://127.0.0.1:11434") is True
        req = mock_open.call_args[0][0]
        assert "127.0.0.1:11434" in req.full_url


def test_lm_studio_custom_base_url() -> None:
    """Test LM Studio health check with custom base URL."""
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"data": []}'
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=mock_response) as mock_open:
        assert check_lm_studio(base_url="http://127.0.0.1:1234/v1") is True
        req = mock_open.call_args[0][0]
        assert "127.0.0.1:1234" in req.full_url
