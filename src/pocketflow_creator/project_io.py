from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from pocketflow_creator.model.project import ProjectModel

PROJECT_SCHEMA_VERSION = "0.1"


class ProjectLoader:
    def load(self, path: Path) -> ProjectModel:
        with path.open(encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f)
        version = str(data.get("schema_version", ""))
        if version != PROJECT_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported project schema version {version!r};"
                f" expected {PROJECT_SCHEMA_VERSION!r}"
            )
        return ProjectModel(
            name=str(data["name"]),
            package_name=str(data["package_name"]),
            root=path.parent,
            default_provider=str(data.get("default_provider", "ollama_local")),
            default_model=str(data.get("default_model", "qwen2.5-coder:14b")),
            graphs=list(data.get("graphs", [])),
            prompts=list(data.get("prompts", [])),
            node_types=list(data.get("node_types", [])),
            shared_store_schema=data.get("shared_store_schema"),
        )


class ProjectSaver:
    def save(self, project: ProjectModel, path: Path | None = None) -> None:
        target = path or project.project_file
        data: dict[str, Any] = {
            "schema_version": PROJECT_SCHEMA_VERSION,
            "name": project.name,
            "package_name": project.package_name,
            "default_provider": project.default_provider,
            "default_model": project.default_model,
            "graphs": project.graphs,
            "prompts": project.prompts,
            "node_types": project.node_types,
        }
        if project.shared_store_schema is not None:
            data["shared_store_schema"] = project.shared_store_schema
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False)
