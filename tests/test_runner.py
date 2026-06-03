from __future__ import annotations

import json
import threading
from pathlib import Path

from pocketflow_creator.model.graph_model import EdgeModel, GraphModel, NodeModel
from pocketflow_creator.runtime.providers import MockProvider
from pocketflow_creator.runtime.runner import FlowRunner, RunTrace, StepController


def _two_node_graph() -> GraphModel:
    nodes = [
        NodeModel(id="n1", type_id="basic", title="Start"),
        NodeModel(id="n2", type_id="basic", title="End"),
    ]
    edges = [EdgeModel(id="e1", from_node="n1", to_node="n2", action="default")]
    return GraphModel(id="g1", title="Two Node", nodes=nodes, edges=edges, start_node="n1")


def _llm_graph() -> GraphModel:
    nodes = [
        NodeModel(id="n1", type_id="llm_call", title="LLM"),
        NodeModel(id="n2", type_id="basic", title="End"),
    ]
    edges = [EdgeModel(id="e1", from_node="n1", to_node="n2", action="default")]
    return GraphModel(id="g2", title="LLM Flow", nodes=nodes, edges=edges, start_node="n1")


class TestFlowRunner:
    def test_run_produces_trace_with_steps(self) -> None:
        trace = FlowRunner().run(_two_node_graph(), MockProvider(), project_name="demo")
        assert len(trace.steps) == 2

    def test_run_visits_start_node_first(self) -> None:
        trace = FlowRunner().run(_two_node_graph(), MockProvider())
        assert trace.steps[0].node_id == "n1"

    def test_run_visits_all_nodes_in_order(self) -> None:
        trace = FlowRunner().run(_two_node_graph(), MockProvider())
        assert [s.node_id for s in trace.steps] == ["n1", "n2"]

    def test_empty_graph_returns_empty_trace(self) -> None:
        graph = GraphModel(id="g0", title="Empty", nodes=[], edges=[], start_node="")
        trace = FlowRunner().run(graph, MockProvider())
        assert trace.steps == []

    def test_llm_node_calls_provider(self) -> None:
        provider = MockProvider(response="the answer")
        trace = FlowRunner().run(_llm_graph(), provider)
        llm_step = trace.steps[0]
        assert llm_step.response == "the answer"
        assert llm_step.prompt != ""

    def test_llm_response_stored_in_shared(self) -> None:
        provider = MockProvider(response="42")
        trace = FlowRunner().run(_llm_graph(), provider)
        llm_step = trace.steps[0]
        assert llm_step.shared_after.get("n1_response") == "42"

    def test_non_llm_node_does_not_call_provider(self) -> None:
        calls: list[str] = []

        class SpyProvider:
            def complete(self, prompt: str, *, model: str | None = None) -> str:
                calls.append(prompt)
                return "x"

        FlowRunner().run(_two_node_graph(), SpyProvider())  # type: ignore[arg-type]
        assert calls == []

    def test_trace_json_roundtrip(self) -> None:
        trace = FlowRunner().run(_two_node_graph(), MockProvider(), project_name="demo")
        raw = json.loads(trace.to_json())
        assert raw["graph"] == "Two Node"
        assert len(raw["steps"]) == 2

    def test_save_trace_writes_file(self, tmp_path: Path) -> None:
        trace = FlowRunner().run(_two_node_graph(), MockProvider(), project_name="demo")
        out = FlowRunner().save_trace(trace, tmp_path / "run_reports")
        assert out.exists()
        data = json.loads(out.read_text())
        assert "steps" in data


class TestRunTrace:
    def test_project_name_in_json(self) -> None:
        trace = RunTrace(
            started_at="2026-01-01T00:00:00+00:00",
            project_name="my_proj",
            graph_title="flow",
        )
        raw = json.loads(trace.to_json())
        assert raw["project"] == "my_proj"


class TestStepGenerator:
    def test_steps_yields_same_count_as_run(self) -> None:
        steps = list(FlowRunner().steps(_two_node_graph(), MockProvider()))
        assert len(steps) == 2

    def test_steps_yields_run_step_objects(self) -> None:
        from pocketflow_creator.runtime.runner import RunStep

        steps = list(FlowRunner().steps(_two_node_graph(), MockProvider()))
        assert all(isinstance(s, RunStep) for s in steps)

    def test_steps_consumer_can_stop_early(self) -> None:
        gen = FlowRunner().steps(_two_node_graph(), MockProvider())
        first = next(gen)
        assert first.node_id == "n1"
        gen.close()  # consumer stops early — no error

    def test_steps_empty_graph_yields_nothing(self) -> None:
        graph = GraphModel(id="g0", title="Empty", nodes=[], edges=[], start_node="")
        steps = list(FlowRunner().steps(graph, MockProvider()))
        assert steps == []


class TestRunDebug:
    def test_run_debug_collects_all_steps(self) -> None:
        ctrl = StepController()
        trace = FlowRunner().run_debug(_two_node_graph(), MockProvider(), ctrl)
        assert len(trace.steps) == 2

    def test_run_debug_pauses_at_breakpoint_and_resumes(self) -> None:
        ctrl = StepController()
        result: list[object] = []

        def _runner() -> None:
            trace = FlowRunner().run_debug(_two_node_graph(), MockProvider(), ctrl, breakpoints={"n1"})
            result.append(trace)

        t = threading.Thread(target=_runner)
        t.start()
        # Wait until the runner is paused (event cleared), then resume
        import time

        deadline = time.monotonic() + 5
        while ctrl._resume.is_set() and time.monotonic() < deadline:
            time.sleep(0.001)
        ctrl.resume()
        t.join(timeout=5)

        assert result, "run_debug thread did not complete"
        from pocketflow_creator.runtime.runner import RunTrace as RT

        trace = result[0]
        assert isinstance(trace, RT)
        assert [s.node_id for s in trace.steps] == ["n1", "n2"]

    def test_run_debug_stop_halts_after_current_step(self) -> None:
        ctrl = StepController()

        def _on_step(step: object) -> None:
            ctrl.stop()

        trace = FlowRunner().run_debug(_two_node_graph(), MockProvider(), ctrl, on_step=_on_step)
        assert len(trace.steps) == 1
        assert trace.steps[0].node_id == "n1"


class TestStepController:
    def test_wait_returns_true_when_running(self) -> None:
        ctrl = StepController()
        assert ctrl.wait_for_resume() is True

    def test_wait_returns_false_after_stop(self) -> None:
        ctrl = StepController()
        ctrl.stop()
        assert ctrl.wait_for_resume() is False

    def test_is_stopped_false_initially(self) -> None:
        ctrl = StepController()
        assert ctrl.is_stopped is False

    def test_is_stopped_true_after_stop(self) -> None:
        ctrl = StepController()
        ctrl.stop()
        assert ctrl.is_stopped is True

    def test_pause_then_resume_unblocks(self) -> None:
        ctrl = StepController()
        ctrl.pause()
        threading.Thread(target=ctrl.resume).start()
        assert ctrl.wait_for_resume() is True
