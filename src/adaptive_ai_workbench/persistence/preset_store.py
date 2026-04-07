from __future__ import annotations

from pathlib import Path

from adaptive_ai_workbench.domain.errors import StorageError
from adaptive_ai_workbench.domain.models import PresetDefinition

LEGACY_PRESET_ALIASES = {
    "professional_email": "professional_clear",
    "concise_cv": "concise_structured",
    "strict_code_review": "analytical_review",
}


class PresetStore:
    def __init__(self, templates_dir: Path) -> None:
        self._templates_dir = templates_dir / "presets"

    def list_builtin(self) -> list[PresetDefinition]:
        presets = [self.load_builtin(path.stem) for path in sorted(self._templates_dir.glob("*.json"))]
        return sorted(presets, key=lambda preset: preset.name.lower())

    def load_builtin(self, preset_id: str) -> PresetDefinition:
        resolved_preset_id = self.resolve_preset_id(preset_id)
        path = self._templates_dir / f"{resolved_preset_id}.json"
        if not path.exists():
            raise StorageError(f"Built-in response profile not found: {preset_id}")
        try:
            return PresetDefinition.model_validate_json(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            raise StorageError(f"Failed to load response profile from {path}: {exc}") from exc

    def is_known_preset_id(self, preset_id: str) -> bool:
        resolved_preset_id = self.resolve_preset_id(preset_id)
        return (self._templates_dir / f"{resolved_preset_id}.json").exists()

    def resolve_preset_id(self, preset_id: str) -> str:
        return LEGACY_PRESET_ALIASES.get(preset_id, preset_id)

