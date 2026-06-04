"""Generate fully standalone, self-contained Python scripts that run a flow without pocketflow."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from pocketflow_creator.model.graph_model import GraphModel

if TYPE_CHECKING:
    from pocketflow_creator.model.provider_profile import ProjectProviders, ProviderProfile


class StandaloneGenerator:
    """Generate a complete, stdlib-only self-contained Python script."""

    # Provider source code embedded as strings (must stay in sync with providers.py)
    _PROVIDER_SOURCES: dict[str, str] = {
        "ollama": '''\
class OllamaProvider:
    """Ollama native API — /api/generate endpoint."""

    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "qwen2.5-coder:14b", timeout: int = 120):
        self.base_url = base_url
        self.default_model = default_model
        self.timeout = timeout

    def complete(self, prompt: str, *, model: str | None = None) -> str:
        import sys
        url = f"{self.base_url.rstrip('/')}/api/generate"
        model_name = model or self.default_model
        payload = json.dumps({"model": model_name, "prompt": prompt, "stream": False}).encode()
        print(f"[OllamaProvider] URL: {url}", file=sys.stderr)
        print(f"[OllamaProvider] Request: {payload.decode()}", file=sys.stderr)
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read())
                return str(body.get("response", ""))
        except urllib.error.HTTPError as exc:
            print(f"[OllamaProvider] HTTPError: {exc.code} {exc.reason}", file=sys.stderr)
            detail = f"{exc.code} {exc.reason}"
            try:
                resp_body = exc.read().decode("utf-8", errors="replace")
                print(f"[OllamaProvider] Response body: {resp_body[:500]}", file=sys.stderr)
                if resp_body:
                    try:
                        error_data = json.loads(resp_body)
                        detail = error_data.get("error", resp_body[:200])
                    except json.JSONDecodeError:
                        detail = resp_body[:200]
            except Exception as e:
                print(f"[OllamaProvider] Error reading response: {e}", file=sys.stderr)
                pass
            detail = detail or f"{exc.code} {exc.reason}"
            if "not found" in detail.lower() or "unknown" in detail.lower():
                detail = f"{detail}. Make sure '{model_name}' is installed in Ollama (ollama pull {model_name})"
            raise RuntimeError(f"Ollama request failed: {detail}") from exc
        except urllib.error.URLError as exc:
            reason = str(exc.reason) if exc.reason else str(exc)
            print(f"[OllamaProvider] URLError: {reason}", file=sys.stderr)
            raise RuntimeError(f"Ollama request failed: {reason}") from exc
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            print(f"[OllamaProvider] Response parsing error: {exc}", file=sys.stderr)
            raise RuntimeError(f"Ollama returned unexpected response: {exc}") from exc
''',
        "openai": '''\
class OpenAIProvider:
    """OpenAI chat completions — also works with any OpenAI-compatible endpoint."""

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", default_model: str = "gpt-4o-mini", timeout: int = 120):
        self.api_key = api_key
        self.base_url = base_url
        self.default_model = default_model
        self.timeout = timeout

    def complete(self, prompt: str, *, model: str | None = None) -> str:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = json.dumps({
            "model": model or self.default_model,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read())
                return str(body["choices"][0]["message"]["content"])
        except urllib.error.HTTPError as exc:
            try:
                detail = json.loads(exc.read()).get("error", {}).get("message", str(exc))
            except Exception:
                detail = str(exc)
            raise RuntimeError(f"OpenAI request failed: {detail}") from exc
        except urllib.error.URLError as exc:
            reason = str(exc.reason) if exc.reason else str(exc)
            raise RuntimeError(f"OpenAI request failed: {reason}") from exc
        except (json.JSONDecodeError, KeyError, IndexError, ValueError) as exc:
            raise RuntimeError(f"OpenAI returned unexpected response: {exc}") from exc
''',
        "anthropic": '''\
class AnthropicProvider:
    """Anthropic Messages API."""

    def __init__(self, api_key: str, default_model: str = "claude-haiku-4-5", timeout: int = 120):
        self.api_key = api_key
        self.default_model = default_model
        self.timeout = timeout

    def complete(self, prompt: str, *, model: str | None = None) -> str:
        url = "https://api.anthropic.com/v1/messages"
        payload = json.dumps({
            "model": model or self.default_model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read())
                return str(body["content"][0]["text"])
        except urllib.error.HTTPError as exc:
            try:
                detail = json.loads(exc.read()).get("error", {}).get("message", str(exc))
            except Exception:
                detail = str(exc)
            raise RuntimeError(f"Anthropic request failed: {detail}") from exc
        except urllib.error.URLError as exc:
            reason = str(exc.reason) if exc.reason else str(exc)
            raise RuntimeError(f"Anthropic request failed: {reason}") from exc
        except (json.JSONDecodeError, KeyError, IndexError) as exc:
            raise RuntimeError(f"Anthropic returned unexpected response: {exc}") from exc
''',
        "gemini": '''\
class GeminiProvider:
    """Google Gemini generateContent API."""

    def __init__(self, api_key: str, default_model: str = "gemini-2.0-flash", timeout: int = 120):
        self.api_key = api_key
        self.default_model = default_model
        self.timeout = timeout

    def complete(self, prompt: str, *, model: str | None = None) -> str:
        mdl = model or self.default_model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{mdl}:generateContent?key={self.api_key}"
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read())
                return str(body["candidates"][0]["content"]["parts"][0]["text"])
        except urllib.error.HTTPError as exc:
            try:
                detail = json.loads(exc.read()).get("error", {}).get("message", str(exc))
            except Exception:
                detail = str(exc)
            raise RuntimeError(f"Gemini request failed: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Gemini request failed: {exc}") from exc
        except (json.JSONDecodeError, KeyError, IndexError) as exc:
            raise RuntimeError(f"Gemini returned unexpected response: {exc}") from exc
''',
        "deepseek": '''\
class DeepSeekProvider:
    """DeepSeek API (OpenAI-compatible)."""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1", default_model: str = "deepseek-chat", timeout: int = 120):
        self.api_key = api_key
        self.base_url = base_url
        self.default_model = default_model
        self.timeout = timeout

    def complete(self, prompt: str, *, model: str | None = None) -> str:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = json.dumps({
            "model": model or self.default_model,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read())
                return str(body["choices"][0]["message"]["content"])
        except urllib.error.HTTPError as exc:
            try:
                detail = json.loads(exc.read()).get("error", {}).get("message", str(exc))
            except Exception:
                detail = str(exc)
            raise RuntimeError(f"DeepSeek request failed: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"DeepSeek request failed: {exc}") from exc
        except (json.JSONDecodeError, KeyError, IndexError, ValueError) as exc:
            raise RuntimeError(f"DeepSeek returned unexpected response: {exc}") from exc
''',
    }

    def generate(
        self,
        graph: GraphModel,
        project_providers: ProjectProviders,
        project_name: str = "",
        project_root: Path | None = None,
    ) -> str:
        """Generate a complete standalone Python script for the graph."""
        # Collect which providers are actually used
        used_profiles = self._collect_used_profiles(graph, project_providers)
        used_types = {p.type for p in used_profiles.values()}

        # Build mappings
        profile_var_map = {p_id: self._safe_var_name(p.name) for p_id, p in used_profiles.items()}

        # Generate sections
        header = self._render_header(project_name, graph.title)
        imports = self._render_imports()
        provider_classes = self._render_provider_classes(used_types)
        provider_instances = self._render_provider_instances(used_profiles, profile_var_map)
        helpers = self._render_helpers()
        graph_data = self._render_graph_data(graph, used_profiles, profile_var_map)
        node_dispatch = self._render_node_dispatch()
        run_flow = self._render_run_flow()
        main_block = self._render_main_block(graph)

        return "\n\n".join(
            [header, imports, provider_classes, provider_instances, helpers, graph_data, node_dispatch, run_flow, main_block]
        )

    def _collect_used_profiles(
        self, graph: GraphModel, project_providers: ProjectProviders
    ) -> dict[str, ProviderProfile]:
        """Return {profile_id: ProviderProfile} for all providers referenced in the graph."""
        used_ids = set()
        for node in graph.nodes:
            pid = str(node.properties.get("provider_id", "")).strip()
            if pid:
                used_ids.add(pid)

        result = {}
        for profile in project_providers.profiles:
            if profile.id in used_ids:
                result[profile.id] = profile

        # If no profiles were explicitly referenced, add the default profile
        if not result and project_providers.default_profile:
            result[project_providers.default_profile.id] = project_providers.default_profile

        return result

    def _safe_var_name(self, name: str) -> str:
        """Convert a profile name to a safe Python variable name."""
        safe = re.sub(r"[^a-zA-Z0-9_]", "_", name.lower())
        # Remove leading digits and underscores
        safe = re.sub(r"^[0-9_]+", "", safe)
        return f"_provider_{safe}" if safe else "_provider_default"

    def _render_header(self, project_name: str, graph_title: str) -> str:
        """Render the file header comment."""
        lines = [
            "# ──────────────────────────────────────────────────────────────────────────────────",
            "# Auto-generated by PocketFlow Creator — do not edit",
            f"# Project: {project_name}",
            f"# Graph: {graph_title}",
            "# ──────────────────────────────────────────────────────────────────────────────────",
        ]
        return "\n".join(lines)

    def _render_imports(self) -> str:
        """Render the import block."""
        return """\
from __future__ import annotations

import copy
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path"""

    def _render_provider_classes(self, used_types: set[str]) -> str:
        """Render provider class definitions for used types."""
        lines = ["# ── Provider Classes ─────────────────────────────────────────────────────────"]

        # Determine which provider type names map to each class
        type_to_provider_class: dict[str, str] = {
            "ollama": "ollama",
            "lm_studio": "openai",
            "openai_compat": "openai",
            "deepseek": "deepseek",
            "anthropic": "anthropic",
            "gemini": "gemini",
        }

        rendered_classes = set()
        for ptype in used_types:
            provider_key = type_to_provider_class.get(ptype)
            if provider_key and provider_key not in rendered_classes:
                lines.append(self._PROVIDER_SOURCES[provider_key])
                rendered_classes.add(provider_key)

        return "\n".join(lines)

    def _render_provider_instances(self, profiles: dict[str, ProviderProfile], profile_var_map: dict[str, str]) -> str:
        """Render provider instance declarations."""
        lines = ["# ── Provider Instances ───────────────────────────────────────────────────────"]
        lines.append("")

        if not profiles:
            return "\n".join(lines)

        # Check if any cloud provider keys are needed
        cloud_profiles = [p for p in profiles.values() if p.type in ("openai_compat", "anthropic", "gemini", "deepseek", "lm_studio")]
        if any(p.type in ("openai_compat", "anthropic", "gemini", "deepseek") for p in cloud_profiles):
            lines.append("# ── API Keys ──────────────────────────────────────────────────────────────────")
            lines.append("# Set these environment variables before running:")
            seen = set()
            for p in sorted(cloud_profiles, key=lambda x: x.type):
                if p.type not in seen:
                    if p.type == "openai_compat":
                        lines.append("#   export OPENAI_API_KEY='sk-...'")
                        seen.add("openai_compat")
                    elif p.type == "anthropic":
                        lines.append("#   export ANTHROPIC_API_KEY='sk-ant-...'")
                        seen.add("anthropic")
                    elif p.type == "gemini":
                        lines.append("#   export GEMINI_API_KEY='...'")
                        seen.add("gemini")
                    elif p.type == "deepseek":
                        lines.append("#   export DEEPSEEK_API_KEY='sk-...'")
                        seen.add("deepseek")
            lines.append("")

        for p_id, profile in profiles.items():
            var_name = profile_var_map[p_id]
            if profile.type == "ollama":
                base_url = profile.base_url or "http://localhost:11434"
                model = profile.model or "qwen2.5-coder:14b"
                lines.append(f"{var_name} = OllamaProvider(")
                lines.append(f'    base_url="{base_url}",')
                lines.append(f'    default_model="{model}",')
                lines.append(f"    timeout={profile.timeout},")
                lines.append(")")
            elif profile.type == "lm_studio":
                base_url = profile.base_url or "http://localhost:1234/v1"
                model = profile.model or "meta-llama-3.1-8b"
                lines.append(f"{var_name} = OpenAIProvider(")
                lines.append(f"    api_key=os.environ.get('OPENAI_API_KEY', ''),")
                lines.append(f'    base_url="{base_url}",')
                lines.append(f'    default_model="{model}",')
                lines.append(f"    timeout={profile.timeout},")
                lines.append(")")
            elif profile.type == "openai_compat":
                base_url = profile.base_url or "https://api.openai.com/v1"
                model = profile.model or "gpt-4o-mini"
                lines.append(f"{var_name} = OpenAIProvider(")
                lines.append(f"    api_key=os.environ.get('OPENAI_API_KEY', ''),")
                lines.append(f'    base_url="{base_url}",')
                lines.append(f'    default_model="{model}",')
                lines.append(f"    timeout={profile.timeout},")
                lines.append(")")
            elif profile.type == "anthropic":
                model = profile.model or "claude-haiku-4-5"
                lines.append(f"{var_name} = AnthropicProvider(")
                lines.append(f"    api_key=os.environ.get('ANTHROPIC_API_KEY', ''),")
                lines.append(f'    default_model="{model}",')
                lines.append(f"    timeout={profile.timeout},")
                lines.append(")")
            elif profile.type == "gemini":
                model = profile.model or "gemini-2.0-flash"
                lines.append(f"{var_name} = GeminiProvider(")
                lines.append(f"    api_key=os.environ.get('GEMINI_API_KEY', ''),")
                lines.append(f'    default_model="{model}",')
                lines.append(f"    timeout={profile.timeout},")
                lines.append(")")
            elif profile.type == "deepseek":
                base_url = profile.base_url or "https://api.deepseek.com/v1"
                model = profile.model or "deepseek-chat"
                lines.append(f"{var_name} = DeepSeekProvider(")
                lines.append(f"    api_key=os.environ.get('DEEPSEEK_API_KEY', ''),")
                lines.append(f'    base_url="{base_url}",')
                lines.append(f'    default_model="{model}",')
                lines.append(f"    timeout={profile.timeout},")
                lines.append(")")

        return "\n".join(lines)

    def _render_helpers(self) -> str:
        """Render helper functions (_resolve_prompt, _interpolate, etc.)."""
        return r'''\
# ── Helper Functions ──────────────────────────────────────────────────────────

def _resolve_prompt(node_props, project_root=None):
    """Return the prompt string for an LLM node, handling both string and path types."""
    prompt_type = str(node_props.get("prompt_type", "string"))
    raw = str(node_props.get("prompt_file", ""))
    if not raw:
        return ""
    if prompt_type == "path":
        if project_root is None:
            return f"(cannot read prompt file — no project root: {raw})"
        try:
            return (Path(project_root) / raw).read_text(encoding="utf-8")
        except FileNotFoundError:
            return f"(prompt file not found: {raw})"
        except Exception as exc:
            return f"(error reading {raw}: {exc})"
    return raw


def _interpolate(text, shared_store):
    """Replace shared store references in a prompt string.

    Supports:
      {key}            — replaced with str(shared_store[key])
      shared['key']    — replaced with str(shared_store[key])
    """
    def _replace_shared(m):
        key = m.group(1)
        return str(shared_store[key]) if key in shared_store else m.group(0)

    text = re.sub(r"""shared\[['"]([^'"]+)['"]\]""", _replace_shared, text)

    def _replace_brace(m):
        key = m.group(1)
        return str(shared_store[key]) if key in shared_store else m.group(0)

    text = re.sub(r"\{([^}]+)\}", _replace_brace, text)
    return text'''

    def _render_graph_data(
        self,
        graph: GraphModel,
        used_profiles: dict[str, ProviderProfile],
        profile_var_map: dict[str, str],
    ) -> str:
        """Render the graph data (_START, _NODES, _EDGES)."""
        lines = ["# ── Graph Data ────────────────────────────────────────────────────────────────"]
        lines.append("")

        # Start node
        start_node_id = graph.start_node or (graph.nodes[0].id if graph.nodes else "")
        lines.append(f'_START = "{start_node_id}"')
        lines.append("")

        # Build _NODES dict
        lines.append("_NODES = {")
        default_profile_id = list(used_profiles.keys())[0] if used_profiles else ""
        for node in graph.nodes:
            node_type = node.type_id
            node_title = node.title.replace('"', '\\"')
            node_props_repr = repr(node.properties)

            # Determine which provider to use for this node
            provider_ref = "None"
            if "llm" in node_type.lower() or node_type in ("classifier_node", "judge_node", "agent_node"):
                provider_id = str(node.properties.get("provider_id", "")).strip() or default_profile_id
                if provider_id in profile_var_map:
                    provider_ref = profile_var_map[provider_id]

            safe_id = node.id.replace('"', '\\"')
            lines.append(f'    "{safe_id}": {{')
            lines.append(f'        "type": "{node_type}",')
            lines.append(f'        "title": "{node_title}",')
            lines.append(f'        "props": {node_props_repr},')
            lines.append(f'        "provider": {provider_ref},')
            lines.append("    },")
        lines.append("}")
        lines.append("")

        # Build _EDGES list
        lines.append("_EDGES = [")
        for edge in graph.edges:
            from_id = edge.from_node.replace('"', '\\"')
            to_id = edge.to_node.replace('"', '\\"')
            action = edge.action.replace('"', '\\"')
            lines.append(f'    {{"from": "{from_id}", "action": "{action}", "to": "{to_id}"}},')
        lines.append("]")

        return "\n".join(lines)

    def _render_node_dispatch(self) -> str:
        """Render the _run_node() dispatcher function."""
        return '''\
# ── Node Dispatch ────────────────────────────────────────────────────────────

def _run_node(node_id, node, shared, outgoing_actions):
    """Execute a single node; return the chosen next action."""
    node_type = node["type"]
    props = node["props"]
    provider = node["provider"]
    chosen_action = list(outgoing_actions)[0] if outgoing_actions else "default"

    try:
        if node_type in ("start_node", "stop_node", "basic_node"):
            pass  # no-op

        elif "llm" in node_type.lower():
            if provider is None:
                raise RuntimeError(f"No provider configured for {node_type} '{node['title']}'")
            prompt = _interpolate(_resolve_prompt(props), shared)
            if not prompt:
                prompt = f"[{node['title']}]"
            response = provider.complete(prompt, model=props.get("model"))
            output_key = str(props.get("output_key", f"{node_id}_response"))
            shared[output_key] = response

        elif node_type == "classifier_node":
            if provider is None:
                raise RuntimeError(f"No provider configured for classifier '{node['title']}'")
            input_key = str(props.get("input_key", "input"))
            content = str(shared.get(input_key, ""))
            categories = str(props.get("categories", ""))
            resolved = _resolve_prompt(props)
            prompt = _interpolate(
                resolved or f"Classify as exactly one of [{categories}].\\nReply with only the category, nothing else.\\n\\nText: {content}",
                shared,
            )
            response = provider.complete(prompt, model=props.get("model"))
            label = response.strip().lower()
            if label not in outgoing_actions:
                label = next((act for act in outgoing_actions if act in label or label in act), next(iter(outgoing_actions), "default"))
            chosen_action = label
            shared[f"{node_id}_label"] = label

        elif node_type == "judge_node":
            if provider is None:
                raise RuntimeError(f"No provider configured for judge '{node['title']}'")
            input_key = str(props.get("input_key", "content"))
            content = str(shared.get(input_key, ""))
            criteria = str(props.get("criteria", ""))
            prompt = _interpolate(
                _resolve_prompt(props) or f"Evaluate: Criteria: {criteria}\\n\\nContent: {content}\\n\\nReply: 'pass' or 'fail'",
                shared,
            )
            response = provider.complete(prompt, model=props.get("model"))
            verdict = response.strip().lower()
            if "pass" in verdict and "pass" in outgoing_actions:
                chosen_action = "pass"
            elif "fail" in verdict and "fail" in outgoing_actions:
                chosen_action = "fail"
            shared[f"{node_id}_verdict"] = verdict

        elif node_type == "agent_node":
            if provider is None:
                raise RuntimeError(f"No provider configured for agent '{node['title']}'")
            input_key = str(props.get("input_key", "task"))
            task = str(shared.get(input_key, ""))
            prompt = _interpolate(_resolve_prompt(props) or f"Complete: {task}", shared)
            response = provider.complete(prompt, model=props.get("model"))
            output_key = str(props.get("output_key", "result"))
            shared[output_key] = response
            resp_lower = response.strip().lower()
            done_words = ("done", "complete", "finished", "answer")
            if "done" in outgoing_actions and any(w in resp_lower for w in done_words):
                chosen_action = "done"
            elif "continue" in outgoing_actions:
                chosen_action = "continue"

        elif node_type == "human_input_node":
            print(f"\\n[{node['title']}] (human interaction needed — enter input or press Enter)")
            user_input = input("> ")
            output_key = str(props.get("output_key", "input"))
            shared[output_key] = user_input
            chosen_action = "saved" if user_input else "cancelled"

        elif node_type == "human_review_node":
            print(f"\\n[{node['title']}] Review this:")
            input_key = str(props.get("input_key", "content"))
            print(shared.get(input_key, ""))
            verdict = input("Approve? [y/n]: ").strip().lower()
            chosen_action = "approved" if verdict.startswith("y") else "rejected"

        elif node_type == "file_reader_node":
            file_path = str(props.get("file_path", ""))
            if not file_path:
                raise RuntimeError(f"file_reader_node '{node['title']}' has no file_path")
            try:
                content = Path(file_path).read_text(encoding=str(props.get("encoding", "utf-8")))
                output_key = str(props.get("output_key", "content"))
                shared[output_key] = content
            except Exception as e:
                raise RuntimeError(f"Failed to read {file_path}: {e}") from e

        elif node_type == "file_writer_node":
            file_path = str(props.get("file_path", ""))
            if not file_path:
                raise RuntimeError(f"file_writer_node '{node['title']}' has no file_path")
            input_key = str(props.get("input_key", "content"))
            content = str(shared.get(input_key, ""))
            mode = "a" if str(props.get("mode", "write")).lower() == "append" else "w"
            try:
                Path(file_path).write_text(content, mode=mode, encoding=str(props.get("encoding", "utf-8")))
            except Exception as e:
                raise RuntimeError(f"Failed to write {file_path}: {e}") from e

        elif node_type == "router_node":
            # Router returns the first available action; routing is defined by graph edges
            pass

        else:
            # Passthrough for unknown types
            pass

    except Exception as e:
        print(f"ERROR in {node['title']}: {e}", file=sys.stderr)
        raise

    return chosen_action'''

    def _render_run_flow(self) -> str:
        """Render the main run_flow() function."""
        return '''\
# ── Flow Runner ───────────────────────────────────────────────────────────────

def run_flow(shared=None):
    """Execute the flow and return the final shared store state."""
    shared = dict(shared or {})
    edge_map = {}
    for e in _EDGES:
        if e["from"] not in edge_map:
            edge_map[e["from"]] = []
        edge_map[e["from"]].append(e)

    current_id = _START
    visited = 0
    max_steps = 200

    while current_id and visited < max_steps:
        node = _NODES.get(current_id)
        if not node:
            break
        visited += 1

        outgoing = edge_map.get(current_id, [])
        outgoing_actions = {e["action"] for e in outgoing}

        try:
            chosen = _run_node(current_id, node, shared, outgoing_actions)
        except Exception as e:
            print(f"FATAL: Node '{node['title']}' failed: {e}", file=sys.stderr)
            raise

        # Find next edge by chosen action
        next_edge = next((e for e in outgoing if e["action"] == chosen), None)
        if next_edge is None and outgoing:
            # Fallback: try "default" edge, then first edge
            next_edge = next((e for e in outgoing if e["action"] == "default"), outgoing[0])

        current_id = next_edge["to"] if next_edge else ""

    return shared'''

    def _render_main_block(self, graph: GraphModel) -> str:
        """Render the __main__ block."""
        return f'''\
# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Running: {graph.title}")
    try:
        result = run_flow({{}})
        print(f"\\n✓ Flow completed successfully")
        print("\\nFinal shared store:")
        print(json.dumps(result, indent=2, default=str))
    except Exception as e:
        print(f"\\n✗ Flow failed: {{e}}", file=sys.stderr)
        sys.exit(1)'''
