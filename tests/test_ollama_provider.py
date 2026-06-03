from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from pocketflow_creator.runtime.providers import MockProvider, OllamaProvider


def _make_server(response_text: str) -> tuple[HTTPServer, int]:
    """Spin up a one-shot HTTP server that returns a JSON Ollama-style response."""

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", 0))
            self.rfile.read(length)
            body = json.dumps({"response": response_text}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:  # noqa: ARG002
            pass  # suppress test output

    server = HTTPServer(("127.0.0.1", 0), Handler)
    return server, server.server_address[1]


def _serve_once(server: HTTPServer) -> None:
    server.handle_request()
    server.server_close()


class TestMockProvider:
    def test_returns_configured_response(self) -> None:
        p = MockProvider(response="hello")
        assert p.complete("any prompt") == "hello"

    def test_model_kwarg_ignored(self) -> None:
        p = MockProvider(response="ok")
        assert p.complete("x", model="gpt-99") == "ok"


class TestOllamaProvider:
    def test_complete_sends_post_and_parses_response(self) -> None:
        server, port = _make_server("the answer")
        t = threading.Thread(target=_serve_once, args=(server,))
        t.start()
        provider = OllamaProvider(base_url=f"http://127.0.0.1:{port}", default_model="test-model")
        result = provider.complete("what is 2+2?")
        t.join(timeout=5)
        assert result == "the answer"

    def test_complete_uses_override_model(self) -> None:
        server, port = _make_server("overridden")
        t = threading.Thread(target=_serve_once, args=(server,))
        t.start()
        provider = OllamaProvider(base_url=f"http://127.0.0.1:{port}")
        result = provider.complete("prompt", model="my-model")
        t.join(timeout=5)
        assert result == "overridden"

    def test_complete_raises_on_connection_error(self) -> None:
        provider = OllamaProvider(base_url="http://127.0.0.1:1")
        with pytest.raises(RuntimeError, match="Ollama request failed"):
            provider.complete("prompt")
