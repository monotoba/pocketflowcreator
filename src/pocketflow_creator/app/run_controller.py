"""RunController — thread/signal wiring for FlowRunner run and debug modes.

This module owns:
  - ``build_provider``   — construct an LLM provider from QSettings
  - ``make_input_callback`` — wire a thread-safe human-input callback to Qt signals
  - ``start_run``        — fire a background run thread and return the signal object
  - ``start_debug``      — fire a background debug thread and return the signal object
"""
from __future__ import annotations

import os
import threading
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PySide6.QtWidgets import QMainWindow

from pocketflow_creator.app.settings_keys import (
    _APP,
    _ORG,
    _SKEY_MOCK_RESPONSE,
    _SKEY_OLLAMA_MODEL,
    _SKEY_OLLAMA_TIMEOUT,
    _SKEY_OLLAMA_URL,
    _SKEY_PROVIDER,
    provider_profile_api_key_skey,
)
from pocketflow_creator.model.graph_model import GraphModel
from pocketflow_creator.model.project import ProjectModel
from pocketflow_creator.runtime.providers import (
    LLMProvider,
    MockProvider,
    OllamaProvider,
    build_provider_from_profile,
)
from pocketflow_creator.runtime.runner import FlowRunner, ProviderResolver, RunStep, StepController


def _load_api_key(profile_id: str) -> str:
    """Load a profile's API key from QSettings, resolving env: references."""
    try:
        from PySide6.QtCore import QSettings
        settings = QSettings(_ORG, _APP)
        raw = str(settings.value(provider_profile_api_key_skey(profile_id), ""))
    except Exception:
        raw = ""
    if raw.startswith("env:"):
        return os.environ.get(raw[4:], "")
    return raw


def build_default_provider(project: ProjectModel | None = None) -> LLMProvider:
    """Return the default provider for *project*.

    Falls back to the legacy QSettings-based provider selection when the
    project has no provider profiles configured.
    """
    if project is not None and project.providers.profiles:
        profile = project.providers.default_profile
        if profile is not None:
            api_key = profile.api_key or _load_api_key(profile.id)
            return build_provider_from_profile(profile, api_key)

    # Legacy / no-project path: read from QSettings global provider setting.
    try:
        from PySide6.QtCore import QSettings
    except ImportError:  # pragma: no cover
        return MockProvider(response="mock response")
    settings = QSettings(_ORG, _APP)
    prov_type = str(settings.value(_SKEY_PROVIDER, "mock"))
    if prov_type == "ollama":
        return OllamaProvider(
            base_url=str(settings.value(_SKEY_OLLAMA_URL, "http://localhost:11434")),
            default_model=str(settings.value(_SKEY_OLLAMA_MODEL, "qwen2.5-coder:14b")),
            timeout=int(settings.value(_SKEY_OLLAMA_TIMEOUT, 120)),  # type: ignore[arg-type]
        )
    return MockProvider(response=str(settings.value(_SKEY_MOCK_RESPONSE, "mock response")))


def build_provider_resolver(project: ProjectModel | None) -> ProviderResolver | None:
    """Return a resolver callable for per-node provider overrides, or None."""
    if project is None or not project.providers.profiles:
        return None
    profile_map = {p.id: p for p in project.providers.profiles}
    if not profile_map:
        return None

    def _resolve(profile_id: str) -> LLMProvider:
        profile = profile_map.get(profile_id)
        if profile is None:
            return MockProvider(response="[unknown provider profile]")
        api_key = profile.api_key or _load_api_key(profile.id)
        return build_provider_from_profile(profile, api_key)

    return _resolve


def make_input_callback(
    signals: Any,
    parent: QMainWindow,
) -> Callable[[dict, dict], object]:
    """Build a thread-safe human-input callback wired to *signals*.input_requested.

    The returned callable can be passed as ``input_callback`` to FlowRunner.
    *signals* must have an ``input_requested(object, object)`` signal attribute.
    """
    try:
        from PySide6.QtWidgets import QDialog
    except ImportError:  # pragma: no cover
        def _noop(props: dict, shared_store: dict) -> object:
            return None
        return _noop

    _event = threading.Event()
    _result: dict[str, object] = {"value": None}

    def _on_input_requested_gui(props: object, store_snap: object) -> None:
        from pocketflow_creator.app.human_input_dialog import create_human_input_dialog
        p = props if isinstance(props, dict) else {}
        s = store_snap if isinstance(store_snap, dict) else {}
        dlg = create_human_input_dialog(str(p.get("input_type", "form")), p, s, parent)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            _result["value"] = dlg.result_data
        else:
            _result["value"] = None
        _event.set()

    def input_cb(props: dict, shared_store: dict) -> object:
        _event.clear()
        signals.input_requested.emit(props, shared_store)
        _event.wait(timeout=600)
        return _result["value"]

    signals.input_requested.connect(_on_input_requested_gui)
    return input_cb


def start_run(
    graph: GraphModel,
    known_graphs: dict[str, GraphModel] | None,
    project_name: str,
    project_root: Path | None,
    parent: QMainWindow,
    on_complete: Callable[[object], None],
    project: ProjectModel | None = None,
) -> tuple[Any, FlowRunner]:
    """Start a background run thread.

    Returns ``(signals, runner)`` where *signals* is the GC-pinned QObject.
    Caller must keep a reference to *signals* until *on_complete* fires.
    """
    from PySide6.QtCore import QObject
    from PySide6.QtCore import Signal as _Sig

    class _RunSignals(QObject):
        result_ready = _Sig(object)
        input_requested = _Sig(object, object)

    signals = _RunSignals()
    runner = FlowRunner()
    provider = build_default_provider(project)
    resolver = build_provider_resolver(project)
    input_cb = make_input_callback(signals, parent)

    def _on_result(result: object) -> None:
        on_complete(result)

    signals.result_ready.connect(_on_result)

    def _run_thread() -> None:
        try:
            trace = runner.run(
                graph,
                provider,
                project_name=project_name,
                known_graphs=known_graphs or None,
                project_root=project_root,
                input_callback=input_cb,
                provider_resolver=resolver,
            )
            signals.result_ready.emit(trace)
        except Exception as exc:
            signals.result_ready.emit(exc)

    threading.Thread(target=_run_thread, daemon=True).start()
    return signals, runner


def start_debug(
    graph: GraphModel,
    known_graphs: dict[str, GraphModel] | None,
    project_name: str,
    project_root: Path | None,
    ctrl: StepController,
    breakpoints: set[str],
    parent: QMainWindow,
    on_step: Callable[[RunStep], None],
    on_finished: Callable[[], None],
    project: ProjectModel | None = None,
) -> Any:
    """Start a background debug thread.

    Returns the GC-pinned signals QObject.  Caller must keep a reference to
    it until *on_finished* fires.
    """
    from PySide6.QtCore import QObject
    from PySide6.QtCore import Signal as _Sig

    class _DbgSignals(QObject):
        step_ready = _Sig(object)
        run_finished = _Sig()
        input_requested = _Sig(object, object)

    signals = _DbgSignals()
    runner = FlowRunner()
    provider = build_default_provider(project)
    resolver = build_provider_resolver(project)
    dbg_input_cb = make_input_callback(signals, parent)

    def _on_step_gui(step: object) -> None:
        if isinstance(step, RunStep):
            on_step(step)

    def _on_finished_gui() -> None:
        on_finished()

    signals.step_ready.connect(_on_step_gui)
    signals.run_finished.connect(_on_finished_gui)

    def _run_thread() -> None:
        runner.run_debug(
            graph,
            provider,
            ctrl,
            breakpoints=breakpoints,
            on_step=lambda s: signals.step_ready.emit(s),
            project_name=project_name,
            known_graphs=known_graphs or None,
            project_root=project_root,
            input_callback=dbg_input_cb,
            provider_resolver=resolver,
        )
        signals.run_finished.emit()

    threading.Thread(target=_run_thread, daemon=True).start()
    return signals
