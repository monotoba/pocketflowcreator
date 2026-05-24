from __future__ import annotations

import copy
import json
import threading
from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from pocketflow_creator.model.graph_model import GraphModel
from pocketflow_creator.runtime.providers import LLMProvider


@dataclass
class RunStep:
    node_id: str
    node_title: str
    action: str
    shared_before: dict[str, object]
    shared_after: dict[str, object]
    prompt: str = ""
    response: str = ""


@dataclass
class RunTrace:
    started_at: str
    project_name: str
    graph_title: str
    steps: list[RunStep] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(
            {
                "started_at": self.started_at,
                "project": self.project_name,
                "graph": self.graph_title,
                "steps": [
                    {
                        "node_id": s.node_id,
                        "node_title": s.node_title,
                        "action": s.action,
                        "shared_before": s.shared_before,
                        "shared_after": s.shared_after,
                        "prompt": s.prompt,
                        "response": s.response,
                    }
                    for s in self.steps
                ],
            },
            indent=2,
        )


class StepController:
    """Thread-safe pause/resume gate for the debug runner thread."""

    def __init__(self) -> None:
        self._resume = threading.Event()
        self._resume.set()  # running initially
        self._stopped = False

    def pause(self) -> None:
        self._resume.clear()

    def resume(self) -> None:
        self._resume.set()

    def stop(self) -> None:
        self._stopped = True
        self._resume.set()  # unblock any waiting thread

    @property
    def is_stopped(self) -> bool:
        return self._stopped

    def wait_for_resume(self) -> bool:
        """Block the caller until resume() or stop(). Returns False if stopped."""
        self._resume.wait()
        return not self._stopped


class FlowRunner:
    """Interpret a GraphModel directly — no generated code required."""

    MAX_STEPS = 200  # guard against cycles

    def steps(
        self,
        graph: GraphModel,
        provider: LLMProvider,
        *,
        shared: dict[str, object] | None = None,
    ) -> Generator[RunStep, None, None]:
        """Yield one RunStep per executed node. Non-blocking; consumer controls pacing."""
        if not graph.start_node:
            return

        shared_store: dict[str, object] = dict(shared or {})
        node_index = {n.id: n for n in graph.nodes}
        current_id = graph.start_node
        visited = 0

        while current_id and visited < self.MAX_STEPS:
            node = node_index.get(current_id)
            if node is None:
                break
            visited += 1

            shared_before = copy.deepcopy(shared_store)
            prompt = ""
            response = ""
            if "llm" in node.type_id.lower():
                prompt = f"[{node.title}] {node.type_id}"
                response = provider.complete(prompt)
                shared_store[f"{node.id}_response"] = response

            shared_after = copy.deepcopy(shared_store)
            outgoing = [e for e in graph.edges if e.from_node == current_id]
            chosen_action = outgoing[0].action if outgoing else "default"

            yield RunStep(
                node_id=current_id,
                node_title=node.title,
                action=chosen_action,
                shared_before=shared_before,
                shared_after=shared_after,
                prompt=prompt,
                response=response,
            )

            next_edge = next((e for e in outgoing if e.action == chosen_action), None)
            current_id = next_edge.to_node if next_edge else ""

    def run(
        self,
        graph: GraphModel,
        provider: LLMProvider,
        *,
        project_name: str = "",
        shared: dict[str, object] | None = None,
    ) -> RunTrace:
        started_at = datetime.now(tz=timezone.utc).isoformat()
        return RunTrace(
            started_at=started_at,
            project_name=project_name,
            graph_title=graph.title,
            steps=list(self.steps(graph, provider, shared=shared)),
        )

    def run_debug(
        self,
        graph: GraphModel,
        provider: LLMProvider,
        controller: StepController,
        *,
        breakpoints: set[str] | None = None,
        on_step: object = None,
        project_name: str = "",
        shared: dict[str, object] | None = None,
    ) -> RunTrace:
        """Run the graph in debug mode; pauses at breakpoints via controller.

        Intended to run in a background thread. on_step is called with each
        RunStep if provided (use a thread-safe callback or Qt signal wrapper).
        """
        bp = breakpoints or set()
        started_at = datetime.now(tz=timezone.utc).isoformat()
        collected: list[RunStep] = []

        for step in self.steps(graph, provider, shared=shared):
            if controller.is_stopped:
                break
            collected.append(step)
            if callable(on_step):
                on_step(step)  # type: ignore[operator]
            if step.node_id in bp:
                controller.pause()
            if not controller.wait_for_resume():
                break

        return RunTrace(
            started_at=started_at,
            project_name=project_name,
            graph_title=graph.title,
            steps=collected,
        )

    def save_trace(self, trace: RunTrace, run_reports_dir: Path) -> Path:
        run_reports_dir.mkdir(parents=True, exist_ok=True)
        ts = trace.started_at.replace(":", "-").replace("+", "").split(".")[0]
        out = run_reports_dir / f"{ts}.json"
        out.write_text(trace.to_json(), encoding="utf-8")
        return out
