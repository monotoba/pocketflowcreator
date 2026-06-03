"""Health checks for local LLM providers (Ollama, LM Studio)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request


def check_ollama(base_url: str = "http://localhost:11434", timeout: int = 2) -> bool:
    """Test if Ollama is running and responding."""
    try:
        url = f"{base_url.rstrip('/')}/api/tags"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            return isinstance(data, dict) and "models" in data
    except Exception:
        return False


def check_lm_studio(base_url: str = "http://localhost:1234/v1", timeout: int = 2) -> bool:
    """Test if LM Studio is running and responding."""
    try:
        url = f"{base_url.rstrip('/')}/models"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            return isinstance(data, dict) and "data" in data
    except Exception:
        return False
