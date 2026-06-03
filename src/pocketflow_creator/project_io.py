from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from pocketflow_creator.model.project import ProjectModel
from pocketflow_creator.model.provider_profile import ProjectProviders

PROJECT_SCHEMA_VERSION = "0.2"
_LEGACY_SCHEMA_VERSION = "0.1"


class ProjectLoader:
    def load(self, path: Path) -> ProjectModel:
        with path.open(encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f)
        version = str(data.get("schema_version", ""))
        if version not in (PROJECT_SCHEMA_VERSION, _LEGACY_SCHEMA_VERSION):
            raise ValueError(
                f"Unsupported project schema version {version!r};"
                f" expected {PROJECT_SCHEMA_VERSION!r}"
            )
        return self._parse_project(data, path.parent, legacy=(version == _LEGACY_SCHEMA_VERSION))

    @staticmethod
    def _parse_project(data: dict[str, Any], root: Path, *, legacy: bool = False) -> ProjectModel:
        """Construct a ProjectModel from a loaded YAML mapping and project root path."""
        if legacy:
            providers = ProjectProviders.default_empty()
        else:
            raw_providers = data.get("providers")
            providers = (
                ProjectProviders.from_dict(raw_providers)
                if isinstance(raw_providers, dict)
                else ProjectProviders.default_empty()
            )
        return ProjectModel(
            name=str(data["name"]),
            package_name=str(data["package_name"]),
            root=root,
            providers=providers,
            graphs=list(data.get("graphs", [])),
            prompts=list(data.get("prompts", [])),
            node_types=list(data.get("node_types", [])),
            shared_store_schema=data.get("shared_store_schema"),
            auto_arrange=dict(data.get("auto_arrange") or {}),
            # legacy fields preserved for migration awareness
            default_provider=str(data.get("default_provider", "")),
            default_model=str(data.get("default_model", "")),
        )


class ProjectSaver:
    def save(self, project: ProjectModel, path: Path | None = None) -> None:
        target = path or project.project_file
        data: dict[str, Any] = {
            "schema_version": PROJECT_SCHEMA_VERSION,
            "name": project.name,
            "package_name": project.package_name,
            "providers": project.providers.to_dict(),
            "graphs": project.graphs,
            "prompts": project.prompts,
            "node_types": project.node_types,
        }
        if project.shared_store_schema is not None:
            data["shared_store_schema"] = project.shared_store_schema
        if project.auto_arrange:
            data["auto_arrange"] = project.auto_arrange
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False)
