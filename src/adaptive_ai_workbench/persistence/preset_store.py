from __future__ import annotations

from pathlib import Path

from adaptive_ai_workbench.domain.errors import StorageError
from adaptive_ai_workbench.domain.models import PresetDefinition


class PresetStore:
    def __init__(self, templates_dir: Path) -> None:
        self._templates_dir = templates_dir / "presets"

    def list_builtin(self) -> list[PresetDefinition]:
        presets = [self.load_builtin(path.stem) for path in sorted(self._templates_dir.glob("*.json"))]
        return sorted(presets, key=lambda preset: preset.name.lower())

    def load_builtin(self, preset_id: str) -> PresetDefinition:
        path = self._templates_dir / f"{preset_id}.json"
        if not path.exists():
            raise StorageError(f"Built-in preset not found: {preset_id}")
        try:
            return PresetDefinition.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise StorageError(f"Failed to load preset from {path}: {exc}") from exc
