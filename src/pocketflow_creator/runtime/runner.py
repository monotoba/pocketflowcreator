from __future__ import annotations

import copy
import json
import re
import threading
from collections.abc import Callable, Generator
from collections.abc import Callable as _Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from pocketflow_creator.model.graph_model import GraphModel, NodeModel
from pocketflow_creator.runtime.providers import LLMProvider

ProviderResolver = _Callable[[str], LLMProvider]


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

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _provider_for_node(
        node: NodeModel,
        default_provider: LLMProvider,
        resolver: ProviderResolver | None,
    ) -> LLMProvider:
        """Return the provider to use for *node*.

        If the node has a non-empty ``provider_id`` property and a resolver
        is available, delegate to the resolver.  Otherwise return the default.
        """
        if resolver is None:
            return default_provider
        profile_id = str(node.properties.get("provider_id", "")).strip()
        if not profile_id:
            return default_provider
        try:
            return resolver(profile_id)
        except Exception:
            return default_provider

    @staticmethod
    def _resolve_prompt(node_props: dict[str, object], project_root: Path | None) -> str:
        """Return the prompt string for an LLM node, handling both string and path types."""
        prompt_type = str(node_props.get("prompt_type", "string"))
        raw = str(node_props.get("prompt_file", ""))
        if not raw:
            return ""
        if prompt_type == "path":
            if project_root is None:
                return f"(cannot read prompt file — no project root: {raw})"
            try:
                return (project_root / raw).read_text(encoding="utf-8")
            except FileNotFoundError:
                return f"(prompt file not found: {raw})"
            except Exception as exc:
                return f"(error reading {raw}: {exc})"
        return raw  # prompt_type == "string"

    @staticmethod
    def _interpolate(text: str, shared_store: dict[str, object]) -> str:
        """Replace shared store references in a prompt string.

        Supports two syntaxes:
          {key}            — replaced with str(shared_store[key])
          shared['key']    — replaced with str(shared_store[key])
          shared["key"]    — replaced with str(shared_store[key])

        Unknown keys are left as-is so the LLM sees the original placeholder.
        """
        # shared['key'] and shared["key"]
        def _replace_shared(m: re.Match) -> str:
            key = m.group(1)
            return str(shared_store[key]) if key in shared_store else m.group(0)

        text = re.sub(r"""shared\[['"]([^'"]+)['"]\]""", _replace_shared, text)

        # {key} — only replace when the key exists in the store to avoid
        # accidentally clobbering unrelated curly-brace content
        def _replace_brace(m: re.Match) -> str:
            key = m.group(1)
            return str(shared_store[key]) if key in shared_store else m.group(0)

        text = re.sub(r"\{([^}]+)\}", _replace_brace, text)
        return text

    # --------------------------------------------------- per-node-type handlers

    def _handle_subflow_node(
        self,
        node: NodeModel,
        shared_store: dict[str, object],
        provider: LLMProvider,
        known_graphs: dict[str, GraphModel] | None,
        project_root: Path | None,
        input_callback: Callable[[dict, dict], object] | None,
        chosen_action: str,
        resolver: ProviderResolver | None = None,
    ) -> tuple[list[RunStep], str, str, str]:
        """Execute a subflow inline; return (inner_steps, prompt, response, chosen_action).

        The caller must ``yield from inner_steps`` before yielding the outer RunStep.
        """
        ref = str(node.properties.get("subflow_ref", ""))
        subgraph = (known_graphs or {}).get(ref)
        inner_steps: list[RunStep] = []
        if subgraph is not None:
            # Materialise into a list (not yield-from) so that inner_steps[-1]
            # is accessible below to merge the subflow's final shared_after state
            # back into the parent shared_store before we continue execution.
            inner_steps = list(
                self.steps(
                    subgraph, provider, shared=shared_store,
                    known_graphs=known_graphs, project_root=project_root,
                    input_callback=input_callback, provider_resolver=resolver,
                )
            )
            if inner_steps:
                shared_store.update(inner_steps[-1].shared_after)
        shared_store[f"{node.id}_subflow_ref"] = ref
        return inner_steps, "", "", chosen_action

    def _handle_llm_node(
        self,
        node: NodeModel,
        shared_store: dict[str, object],
        provider: LLMProvider,
        project_root: Path | None,
        chosen_action: str,
    ) -> tuple[str, str, str]:
        """Run an LLM node; return (prompt, response, chosen_action)."""
        prompt = self._interpolate(
            self._resolve_prompt(node.properties, project_root) or (
                f"[{node.title}] {node.type_id}"
            ),
            shared_store,
        )
        response = provider.complete(prompt)
        output_key = str(node.properties.get("output_key", f"{node.id}_response"))
        shared_store[output_key] = response
        return prompt, response, chosen_action

    def _handle_classifier_node(
        self,
        node: NodeModel,
        shared_store: dict[str, object],
        available_actions: set[str],
        provider: LLMProvider,
        project_root: Path | None,
    ) -> tuple[str, str, str]:
        """Run a classifier node; return (prompt, response, chosen_action)."""
        input_key = str(node.properties.get("input_key", "input"))
        content = str(shared_store.get(input_key, ""))
        categories = str(node.properties.get("categories", ""))
        resolved = self._resolve_prompt(node.properties, project_root)
        prompt = self._interpolate(
            resolved or (
                f"Classify the following text as exactly one of [{categories}].\n"
                f"Reply with only the category name, nothing else.\n\nText: {content}"
            ),
            shared_store,
        )
        response = provider.complete(prompt)
        label = response.strip().lower()
        if label not in available_actions:
            # fuzzy match: accept if the response contains an action name
            label = next(
                (act for act in available_actions if act in label or label in act),
                next(iter(available_actions), "default"),
            )
        shared_store[f"{node.id}_label"] = label
        return prompt, response, label

    def _handle_judge_node(
        self,
        node: NodeModel,
        shared_store: dict[str, object],
        available_actions: set[str],
        provider: LLMProvider,
        project_root: Path | None,
        chosen_action: str,
    ) -> tuple[str, str, str]:
        """Run a judge node; return (prompt, response, chosen_action)."""
        input_key = str(node.properties.get("input_key", "content"))
        content = str(shared_store.get(input_key, ""))
        criteria = str(node.properties.get("criteria", ""))
        prompt = self._interpolate(
            self._resolve_prompt(node.properties, project_root) or (
                f"Evaluate the content below against the criteria.\n"
                f"Reply with exactly 'pass' or 'fail'.\n\n"
                f"Criteria: {criteria}\n\nContent: {content}"
            ),
            shared_store,
        )
        response = provider.complete(prompt)
        verdict = response.strip().lower()
        if "pass" in verdict and "pass" in available_actions:
            chosen_action = "pass"
        elif "fail" in verdict and "fail" in available_actions:
            chosen_action = "fail"
        shared_store[f"{node.id}_verdict"] = verdict
        return prompt, response, chosen_action

    def _handle_agent_node(
        self,
        node: NodeModel,
        shared_store: dict[str, object],
        available_actions: set[str],
        provider: LLMProvider,
        project_root: Path | None,
        chosen_action: str,
    ) -> tuple[str, str, str]:
        """Run an agent node; return (prompt, response, chosen_action)."""
        input_key = str(node.properties.get("input_key", "task"))
        task = str(shared_store.get(input_key, ""))
        prompt = self._interpolate(
            self._resolve_prompt(node.properties, project_root) or (
                f"You are an AI agent. Complete the following task:\n\n{task}"
            ),
            shared_store,
        )
        response = provider.complete(prompt)
        output_key = str(node.properties.get("output_key", "result"))
        shared_store[output_key] = response
        resp_lower = response.strip().lower()
        done_words = ("done", "complete", "finished", "answer")
        if "done" in available_actions and any(w in resp_lower for w in done_words):
            chosen_action = "done"
        elif "continue" in available_actions:
            chosen_action = "continue"
        return prompt, response, chosen_action

    def _handle_human_input_node(
        self,
        node: NodeModel,
        shared_store: dict[str, object],
        available_actions: set[str],
        input_callback: Callable[[dict, dict], object] | None,
        chosen_action: str,
    ) -> tuple[str, str, str]:
        """Handle a human-input node; return (prompt, response, chosen_action)."""
        output_key = str(node.properties.get("output_key", "input"))
        if input_callback is not None:
            data = input_callback(dict(node.properties), dict(shared_store))
            if isinstance(data, dict):
                shared_store.update(data)
                chosen_action = "saved"
            elif isinstance(data, list):
                shared_store[output_key] = data
                chosen_action = "saved"
            else:
                # None → user cancelled
                chosen_action = "cancelled"
        else:
            # No callback wired (e.g. non-GUI run); skip and continue.
            chosen_action = next(iter(available_actions), "default")
        return "", "", chosen_action

    # ------------------------------------------------------------------ runner

    def steps(
        self,
        graph: GraphModel,
        provider: LLMProvider,
        *,
        shared: dict[str, object] | None = None,
        known_graphs: dict[str, GraphModel] | None = None,
        project_root: Path | None = None,
        input_callback: Callable[[dict, dict], object] | None = None,
        provider_resolver: ProviderResolver | None = None,
    ) -> Generator[RunStep, None, None]:
        """Yield one RunStep per executed node. Non-blocking; consumer controls pacing.

        known_graphs maps subflow_ref strings to pre-loaded GraphModel objects.
        When provided, subflow_node steps are replaced by their inner graph's steps.
        """
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
            outgoing = [e for e in graph.edges if e.from_node == current_id]
            available_actions = {e.action for e in outgoing}
            chosen_action = outgoing[0].action if outgoing else "default"
            inner_steps: list[RunStep] = []

            node_provider = self._provider_for_node(node, provider, provider_resolver)

            if node.type_id == "subflow_node":
                inner_steps, prompt, response, chosen_action = self._handle_subflow_node(
                    node, shared_store, node_provider, known_graphs, project_root,
                    input_callback, chosen_action, provider_resolver,
                )
                yield from inner_steps
            elif "llm" in node.type_id.lower():
                prompt, response, chosen_action = self._handle_llm_node(
                    node, shared_store, node_provider, project_root, chosen_action,
                )
            elif node.type_id == "classifier_node":
                prompt, response, chosen_action = self._handle_classifier_node(
                    node, shared_store, available_actions, node_provider, project_root,
                )
            elif node.type_id == "judge_node":
                prompt, response, chosen_action = self._handle_judge_node(
                    node, shared_store, available_actions, node_provider, project_root, chosen_action,
                )
            elif node.type_id == "agent_node":
                prompt, response, chosen_action = self._handle_agent_node(
                    node, shared_store, available_actions, node_provider, project_root, chosen_action,
                )
            elif node.type_id == "human_input_node":
                prompt, response, chosen_action = self._handle_human_input_node(
                    node, shared_store, available_actions, input_callback, chosen_action,
                )
            else:
                prompt, response = "", ""

            shared_after = copy.deepcopy(shared_store)

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
            if next_edge is None and outgoing:
                # Fallback: prefer a 'default' edge, then any edge.
                # Handles graphs built before action-aware port dragging was available.
                next_edge = next(
                    (e for e in outgoing if e.action == "default"), outgoing[0]
                )
            current_id = next_edge.to_node if next_edge else ""

    def run(
        self,
        graph: GraphModel,
        provider: LLMProvider,
        *,
        project_name: str = "",
        shared: dict[str, object] | None = None,
        known_graphs: dict[str, GraphModel] | None = None,
        project_root: Path | None = None,
        input_callback: Callable[[dict, dict], object] | None = None,
        provider_resolver: ProviderResolver | None = None,
    ) -> RunTrace:
        started_at = datetime.now(tz=timezone.utc).isoformat()
        return RunTrace(
            started_at=started_at,
            project_name=project_name,
            graph_title=graph.title,
            steps=list(
                self.steps(
                    graph, provider,
                    shared=shared, known_graphs=known_graphs, project_root=project_root,
                    input_callback=input_callback, provider_resolver=provider_resolver,
                )
            ),
        )

    def run_debug(
        self,
        graph: GraphModel,
        provider: LLMProvider,
        controller: StepController,
        *,
        breakpoints: set[str] | None = None,
        on_step: Callable[[RunStep], None] | None = None,
        project_name: str = "",
        shared: dict[str, object] | None = None,
        known_graphs: dict[str, GraphModel] | None = None,
        project_root: Path | None = None,
        input_callback: Callable[[dict, dict], object] | None = None,
        provider_resolver: ProviderResolver | None = None,
    ) -> RunTrace:
        """Run the graph in debug mode; pauses at breakpoints via controller.

        Intended to run in a background thread. on_step is called with each
        RunStep if provided (use a thread-safe callback or Qt signal wrapper).
        """
        bp = breakpoints if breakpoints is not None else set()
        started_at = datetime.now(tz=timezone.utc).isoformat()
        collected: list[RunStep] = []

        for step in self.steps(
            graph, provider, shared=shared, known_graphs=known_graphs,
            project_root=project_root, input_callback=input_callback,
            provider_resolver=provider_resolver,
        ):
            if controller.is_stopped:
                break
            collected.append(step)
            if on_step is not None:
                on_step(step)
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
