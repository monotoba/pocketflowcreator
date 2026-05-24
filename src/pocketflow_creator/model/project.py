from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class ProjectModel:
    name: str
    package_name: str
    root: Path
    default_provider: str = "ollama_local"
    default_model: str = "qwen2.5-coder:14b"
    graphs: list[str] = field(default_factory=list)

    @property
    def project_file(self) -> Path:
        return self.root / f"{self.name}.pfcproj.yaml"
