from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pocketflow_creator.model.provider_profile import ProjectProviders


@dataclass(slots=True)
class ProjectModel:
    """Top-level project configuration persisted in ``<name>.pfcproj.yaml``.

    ``auto_arrange`` stores the last-used layout-algorithm settings
    (algorithm, connector_style, h_gap, v_gap, max_cols) so the dialog
    reopens with the user's previous choices.

    ``providers`` holds named LLM provider profiles. Individual graph nodes
    may reference a profile by id via their ``provider_id`` property; if
    unset they use the profile marked as default.
    """

    name: str
    package_name: str
    root: Path
    providers: ProjectProviders = field(default_factory=ProjectProviders.default_empty)
    graphs: list[str] = field(default_factory=list)
    prompts: list[str] = field(default_factory=list)
    node_types: list[str] = field(default_factory=list)
    shared_store_schema: str | None = None
    auto_arrange: dict[str, Any] = field(default_factory=dict)

    # Legacy fields kept for migration from older project files.
    default_provider: str = ""
    default_model: str = ""

    @property
    def project_file(self) -> Path:
        return self.root / f"{self.name}.pfcproj.yaml"
