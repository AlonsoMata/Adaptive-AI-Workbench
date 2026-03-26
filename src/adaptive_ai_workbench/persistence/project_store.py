from __future__ import annotations

from pathlib import Path

from adaptive_ai_workbench.domain.errors import StorageError
from adaptive_ai_workbench.domain.models import WorkbenchProject


class ProjectStore:
    def __init__(self, data_dir: Path) -> None:
        self._projects_dir = data_dir / "projects"
        self._projects_dir.mkdir(parents=True, exist_ok=True)

    def save_project(self, project: WorkbenchProject) -> Path:
        path = self._projects_dir / f"{project.project_id}.json"
        path.write_text(project.model_dump_json(indent=2), encoding="utf-8")
        return path

    def load_project(self, project_id: str) -> WorkbenchProject:
        path = self._projects_dir / f"{project_id}.json"
        if not path.exists():
            raise StorageError(f"Project not found: {project_id}")
        try:
            return WorkbenchProject.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise StorageError(f"Failed to load project from {path}: {exc}") from exc
