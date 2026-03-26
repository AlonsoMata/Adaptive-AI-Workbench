from __future__ import annotations

from pathlib import Path
from typing import Any

from adaptive_ai_workbench.domain.errors import ValidationFailure
from adaptive_ai_workbench.domain.models import ActionDefinition, InstalledActionPack, PresetDefinition
from adaptive_ai_workbench.execution.dispatcher import ExecutionDispatcher
from adaptive_ai_workbench.model.gateway import OpenAIModelGateway
from adaptive_ai_workbench.persistence.action_pack_store import ActionPackStore
from adaptive_ai_workbench.persistence.preset_store import PresetStore
from adaptive_ai_workbench.settings import Settings


class WorkbenchService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.gateway = OpenAIModelGateway(settings)
        self.dispatcher = ExecutionDispatcher()
        self.action_pack_store = ActionPackStore(
            data_dir=settings.data_dir,
            templates_dir=settings.templates_dir,
        )
        self.preset_store = PresetStore(settings.templates_dir)

    def get_app_metadata(self) -> dict[str, str]:
        return {
            "app_name": self.settings.app_name,
            "model": self.settings.openai_model or "unconfigured",
            "data_dir": str(self.settings.data_dir),
        }

    def health_status(self) -> str:
        if self.gateway.is_configured():
            return "Model gateway configured."
        return "Model gateway not configured. UI is available and local templates can be explored."

    def list_builtin_prompt_names(self) -> list[str]:
        return self._list_template_names(self.settings.templates_dir / "prompts", ".txt")

    def list_builtin_pack_names(self) -> list[str]:
        return self.action_pack_store.list_builtin_templates()

    def list_builtin_preset_names(self) -> list[str]:
        return sorted(preset.preset_id for preset in self.preset_store.list_builtin())

    def list_builtin_packs_detailed(self) -> list[InstalledActionPack]:
        return [
            self.action_pack_store.load_builtin_template(pack_id)
            for pack_id in self.action_pack_store.list_builtin_templates()
        ]

    def list_builtin_presets_detailed(self) -> list[PresetDefinition]:
        return self.preset_store.list_builtin()

    def get_builtin_pack(self, pack_id: str) -> InstalledActionPack:
        return self.action_pack_store.load_builtin_template(pack_id)

    def get_builtin_preset(self, preset_id: str) -> PresetDefinition:
        return self.preset_store.load_builtin(preset_id)

    def resolve_preset_for_action(
        self,
        pack: InstalledActionPack,
        action: ActionDefinition,
        selected_preset_id: str | None,
    ) -> PresetDefinition:
        candidate_ids = [
            selected_preset_id,
            action.default_preset_id,
            *(pack.recommended_preset_ids or []),
        ]
        for preset_id in candidate_ids:
            if preset_id:
                return self.get_builtin_preset(preset_id)

        presets = self.list_builtin_presets_detailed()
        if not presets:
            raise ValidationFailure("No built-in presets are available.")
        return presets[0]

    def preview_builtin_action(
        self,
        pack_id: str,
        action_id: str,
        goal_text: str,
        input_text: str,
        selected_preset_id: str | None,
    ) -> dict[str, Any]:
        pack = self.get_builtin_pack(pack_id)
        action = self._find_action(pack, action_id)
        preset = self.resolve_preset_for_action(pack, action, selected_preset_id)
        preview = self.dispatcher.dispatch(
            action=action,
            input_text=input_text,
            preset=preset,
            goal_text=goal_text,
        )
        preview["pack_id"] = pack.pack_id
        preview["pack_name"] = pack.name
        preview["action_name"] = action.name
        preview["preset_name"] = preset.name
        preview["preset_id"] = preset.preset_id
        return preview

    @staticmethod
    def _find_action(pack: InstalledActionPack, action_id: str) -> ActionDefinition:
        for action in pack.actions:
            if action.action_id == action_id:
                return action
        raise ValidationFailure(f"Action not found in pack {pack.pack_id}: {action_id}")

    @staticmethod
    def _list_template_names(directory: Path, suffix: str) -> list[str]:
        if not directory.exists():
            return []
        return sorted(path.stem for path in directory.glob(f"*{suffix}") if path.is_file())
