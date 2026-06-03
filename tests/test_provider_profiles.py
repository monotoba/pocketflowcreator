"""Tests for ProviderProfile model, factory, project IO, and per-node resolver."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from pocketflow_creator.model.provider_profile import (
    DEFAULT_MODELS,
    ProjectProviders,
    ProviderProfile,
)
from pocketflow_creator.project_io import ProjectLoader, ProjectSaver
from pocketflow_creator.runtime.providers import (
    AnthropicProvider,
    GeminiProvider,
    MockProvider,
    OpenAIProvider,
    build_provider_from_profile,
)

# ── ProviderProfile ────────────────────────────────────────────────────────────


def test_new_profile_has_uuid_id() -> None:
    p = ProviderProfile.new("My API", "openai_compat")
    assert len(p.id) == 36  # UUID4 format
    assert p.name == "My API"
    assert p.type == "openai_compat"
    assert p.model == DEFAULT_MODELS["openai_compat"]


def test_new_profile_defaults_to_openai_compat() -> None:
    p = ProviderProfile.new("Test")
    assert p.type == "openai_compat"


def test_to_dict_excludes_api_key_by_default() -> None:
    p = ProviderProfile.new("X")
    p.api_key = "secret-key"
    d = p.to_dict()
    assert "api_key" not in d


def test_to_dict_includes_api_key_when_requested() -> None:
    p = ProviderProfile.new("X")
    p.api_key = "secret-key"
    d = p.to_dict(include_api_key=True)
    assert d["api_key"] == "secret-key"


def test_to_dict_omits_empty_base_url() -> None:
    p = ProviderProfile(id="abc", name="Claude", type="anthropic", model="claude-haiku-4-5")
    d = p.to_dict()
    assert "base_url" not in d


def test_to_dict_includes_base_url_when_set() -> None:
    p = ProviderProfile.new("Local")
    p.base_url = "http://localhost:11434/v1"
    d = p.to_dict()
    assert d["base_url"] == "http://localhost:11434/v1"


def test_from_dict_round_trip() -> None:
    original = ProviderProfile.new("Gemini Flash", "gemini")
    original.api_key = "key123"
    d = original.to_dict(include_api_key=True)
    restored = ProviderProfile.from_dict(d)
    assert restored.id == original.id
    assert restored.name == original.name
    assert restored.type == original.type
    assert restored.model == original.model
    assert restored.api_key == "key123"


# ── ProjectProviders ───────────────────────────────────────────────────────────


def test_project_providers_default_profile() -> None:
    p1 = ProviderProfile.new("A")
    p2 = ProviderProfile.new("B")
    pp = ProjectProviders(profiles=[p1, p2], default_profile_id=p2.id)
    assert pp.default_profile is p2


def test_project_providers_fallback_to_first_when_no_default() -> None:
    p1 = ProviderProfile.new("A")
    pp = ProjectProviders(profiles=[p1])
    assert pp.default_profile is p1


def test_project_providers_empty_returns_none() -> None:
    pp = ProjectProviders()
    assert pp.default_profile is None


def test_project_providers_by_id() -> None:
    p = ProviderProfile.new("X")
    pp = ProjectProviders(profiles=[p])
    assert pp.by_id(p.id) is p
    assert pp.by_id("nonexistent") is None


def test_project_providers_to_dict_excludes_keys_by_default() -> None:
    p = ProviderProfile.new("A")
    p.api_key = "secret"
    pp = ProjectProviders(profiles=[p], include_api_keys=False)
    d = pp.to_dict()
    assert d["include_api_keys"] is False
    assert "api_key" not in d["profiles"][0]


def test_project_providers_to_dict_includes_keys_when_flagged() -> None:
    p = ProviderProfile.new("A")
    p.api_key = "secret"
    pp = ProjectProviders(profiles=[p], include_api_keys=True)
    d = pp.to_dict()
    assert d["profiles"][0]["api_key"] == "secret"


def test_project_providers_from_dict_round_trip() -> None:
    p = ProviderProfile.new("Haiku", "anthropic")
    p.api_key = "ant-key"
    pp = ProjectProviders(profiles=[p], default_profile_id=p.id, include_api_keys=True)
    restored = ProjectProviders.from_dict(pp.to_dict())
    assert len(restored.profiles) == 1
    assert restored.default_profile_id == p.id
    assert restored.include_api_keys is True
    assert restored.profiles[0].api_key == "ant-key"


# ── Project IO serialization ───────────────────────────────────────────────────


def test_project_saves_and_loads_providers(tmp_path: Path) -> None:
    from pocketflow_creator.model.project import ProjectModel

    p = ProviderProfile.new("Sonnet", "anthropic")
    p.model = "claude-sonnet-4-6"
    providers = ProjectProviders(profiles=[p], default_profile_id=p.id, include_api_keys=False)
    project = ProjectModel(
        name="TestProject",
        package_name="test_project",
        root=tmp_path,
        providers=providers,
    )
    save_path = tmp_path / "TestProject.pfcproj.yaml"
    ProjectSaver().save(project, save_path)

    loaded = ProjectLoader().load(save_path)
    assert len(loaded.providers.profiles) == 1
    assert loaded.providers.profiles[0].name == "Sonnet"
    assert loaded.providers.profiles[0].type == "anthropic"
    assert loaded.providers.default_profile_id == p.id
    assert loaded.providers.include_api_keys is False


def test_project_api_key_excluded_when_flag_false(tmp_path: Path) -> None:
    from pocketflow_creator.model.project import ProjectModel

    p = ProviderProfile.new("GPT", "openai_compat")
    p.api_key = "sk-secret"
    providers = ProjectProviders(profiles=[p], default_profile_id=p.id, include_api_keys=False)
    project = ProjectModel(name="Proj", package_name="proj", root=tmp_path, providers=providers)
    save_path = tmp_path / "Proj.pfcproj.yaml"
    ProjectSaver().save(project, save_path)

    text = save_path.read_text()
    assert "sk-secret" not in text

    loaded = ProjectLoader().load(save_path)
    assert loaded.providers.profiles[0].api_key == ""


def test_project_api_key_included_when_flag_true(tmp_path: Path) -> None:
    from pocketflow_creator.model.project import ProjectModel

    p = ProviderProfile.new("GPT", "openai_compat")
    p.api_key = "sk-visible"
    providers = ProjectProviders(profiles=[p], default_profile_id=p.id, include_api_keys=True)
    project = ProjectModel(name="Proj2", package_name="proj2", root=tmp_path, providers=providers)
    save_path = tmp_path / "Proj2.pfcproj.yaml"
    ProjectSaver().save(project, save_path)

    text = save_path.read_text()
    assert "sk-visible" in text

    loaded = ProjectLoader().load(save_path)
    assert loaded.providers.profiles[0].api_key == "sk-visible"


def test_legacy_schema_loads_without_providers(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy.pfcproj.yaml"
    legacy.write_text("schema_version: '0.1'\nname: Legacy\npackage_name: legacy\ndefault_provider: ollama_local\ndefault_model: llama3\n")
    loaded = ProjectLoader().load(legacy)
    assert loaded.name == "Legacy"
    assert loaded.default_provider == "ollama_local"
    assert loaded.providers.profiles == []


# ── build_provider_from_profile factory ───────────────────────────────────────


def test_factory_openai_compat() -> None:
    p = ProviderProfile.new("OpenAI", "openai_compat")
    p.base_url = "https://api.openai.com/v1"
    provider = build_provider_from_profile(p, "sk-test")
    assert isinstance(provider, OpenAIProvider)
    assert provider.api_key == "sk-test"
    assert provider.base_url == "https://api.openai.com/v1"
    assert provider.default_model == p.model


def test_factory_anthropic() -> None:
    p = ProviderProfile(id="x", name="Claude", type="anthropic", model="claude-haiku-4-5", timeout=60)
    provider = build_provider_from_profile(p, "ant-key")
    assert isinstance(provider, AnthropicProvider)
    assert provider.api_key == "ant-key"
    assert provider.default_model == "claude-haiku-4-5"
    assert provider.timeout == 60


def test_factory_gemini() -> None:
    p = ProviderProfile(id="y", name="Gemini", type="gemini", model="gemini-2.0-flash", timeout=90)
    provider = build_provider_from_profile(p, "gem-key")
    assert isinstance(provider, GeminiProvider)
    assert provider.api_key == "gem-key"
    assert provider.default_model == "gemini-2.0-flash"


def test_factory_uses_profile_api_key_if_no_override() -> None:
    p = ProviderProfile.new("GPT", "openai_compat")
    p.api_key = "profile-key"
    provider = build_provider_from_profile(p)
    assert isinstance(provider, OpenAIProvider)
    assert provider.api_key == "profile-key"


def test_factory_override_key_wins_over_profile_key() -> None:
    p = ProviderProfile.new("GPT", "openai_compat")
    p.api_key = "profile-key"
    provider = build_provider_from_profile(p, "override-key")
    assert isinstance(provider, OpenAIProvider)
    assert provider.api_key == "override-key"


def test_factory_unknown_type_falls_back_to_openai_compat() -> None:
    p = ProviderProfile(id="z", name="Unknown", type="future_type", model="x")
    provider = build_provider_from_profile(p, "k")
    assert isinstance(provider, OpenAIProvider)


# ── FlowRunner per-node resolver ───────────────────────────────────────────────


def _mock_http(content: str) -> MagicMock:
    body = json.dumps({"choices": [{"message": {"content": content}}]}).encode()
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=MagicMock(read=MagicMock(return_value=body)))
    cm.__exit__ = MagicMock(return_value=False)
    return cm


def test_runner_uses_default_provider_when_no_override() -> None:
    from pocketflow_creator.model.graph_model import GraphModel, NodeModel
    from pocketflow_creator.runtime.runner import FlowRunner

    default = MockProvider(response="default-answer")
    node = NodeModel(id="n1", type_id="llm_prompt_node", title="LLM")
    node.properties["prompt_file"] = "say something"
    graph = GraphModel(id="g", title="G", start_node="n1", nodes=[node], edges=[])

    steps = list(FlowRunner().steps(graph, default))
    assert steps[0].response == "default-answer"


def test_runner_uses_resolver_when_provider_id_set() -> None:
    from pocketflow_creator.model.graph_model import GraphModel, NodeModel
    from pocketflow_creator.runtime.runner import FlowRunner

    default = MockProvider(response="default")
    override = MockProvider(response="override-answer")

    node = NodeModel(id="n1", type_id="llm_prompt_node", title="LLM")
    node.properties["prompt_file"] = "say something"
    node.properties["provider_id"] = "profile-xyz"
    graph = GraphModel(id="g", title="G", start_node="n1", nodes=[node], edges=[])

    def _resolver(pid: str) -> MockProvider:
        return override if pid == "profile-xyz" else default

    steps = list(FlowRunner().steps(graph, default, provider_resolver=_resolver))
    assert steps[0].response == "override-answer"


def test_runner_falls_back_to_default_on_bad_profile_id() -> None:
    from pocketflow_creator.model.graph_model import GraphModel, NodeModel
    from pocketflow_creator.runtime.runner import FlowRunner

    default = MockProvider(response="fallback")

    node = NodeModel(id="n1", type_id="llm_prompt_node", title="LLM")
    node.properties["prompt_file"] = "hi"
    node.properties["provider_id"] = "nonexistent-profile"
    graph = GraphModel(id="g", title="G", start_node="n1", nodes=[node], edges=[])

    def _resolver(pid: str) -> MockProvider:
        raise KeyError(f"No profile: {pid}")

    steps = list(FlowRunner().steps(graph, default, provider_resolver=_resolver))
    assert steps[0].response == "fallback"
