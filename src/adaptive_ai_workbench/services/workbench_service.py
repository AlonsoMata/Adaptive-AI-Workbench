from __future__ import annotations

from pathlib import Path
from typing import Any

from adaptive_ai_workbench.domain.errors import ConfigurationError, StorageError, ValidationFailure
from adaptive_ai_workbench.domain.models import ActionDefinition, CandidateActionPack, InstalledActionPack, PresetDefinition
from adaptive_ai_workbench.execution.dispatcher import ExecutionDispatcher
from adaptive_ai_workbench.model.gateway import ModelGateway, OpenAIModelGateway
from adaptive_ai_workbench.model.prompt_loader import load_prompt
from adaptive_ai_workbench.persistence.action_pack_store import ActionPackStore
from adaptive_ai_workbench.persistence.preset_store import PresetStore
from adaptive_ai_workbench.planning.goal_analyzer import normalize_goal_text
from adaptive_ai_workbench.planning.workflow_generator import build_candidate_generation_prompt
from adaptive_ai_workbench.safety.parsing import parse_candidate_action_pack
from adaptive_ai_workbench.safety.validators import validate_candidate_pack
from adaptive_ai_workbench.settings import Settings


class WorkbenchService:
    def __init__(self, settings: Settings, gateway: ModelGateway | None = None) -> None:
        self.settings = settings
        self.gateway = gateway or OpenAIModelGateway(settings)
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
            return "Model gateway configured. You can generate workflow packs from a goal and run installed workflows live."
        return "Model gateway not configured. You can inspect built-in workflows locally, but workflow generation and live execution require OPENAI_API_KEY and AI_WORKBENCH_MODEL."

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

    def list_catalog_packs_detailed(self) -> list[InstalledActionPack]:
        catalog = {pack.pack_id: pack for pack in self.list_builtin_packs_detailed()}
        for pack in self.action_pack_store.list_installed():
            catalog[pack.pack_id] = pack
        return sorted(catalog.values(), key=lambda pack: pack.name.lower())

    def get_builtin_pack(self, pack_id: str) -> InstalledActionPack:
        return self.action_pack_store.load_builtin_template(pack_id)

    def get_catalog_pack(self, pack_id: str) -> InstalledActionPack:
        try:
            return self.action_pack_store.load_installed(pack_id)
        except StorageError:
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

    def generate_candidate_workflow(self, goal_text: str) -> CandidateActionPack:
        normalized_goal = normalize_goal_text(goal_text)
        if not normalized_goal:
            raise ValidationFailure("Enter a goal before generating a workflow.")
        if not self.gateway.is_configured():
            raise ConfigurationError(
                "Workflow generation is unavailable because OPENAI_API_KEY or AI_WORKBENCH_MODEL is not configured."
            )

        generation_prompt = build_candidate_generation_prompt(
            goal_text=normalized_goal,
            system_prompt=load_prompt("generate_action_pack", self.settings.templates_dir),
            presets=self.list_builtin_presets_detailed(),
        )
        result = self.gateway.generate_text(
            system_prompt=generation_prompt.system_prompt,
            user_prompt=generation_prompt.user_prompt,
        )
        candidate = parse_candidate_action_pack(result.output_text)
        return self.validate_candidate_workflow(candidate)

    def validate_candidate_workflow(self, candidate: CandidateActionPack) -> CandidateActionPack:
        validated_candidate = validate_candidate_pack(candidate)
        self._validate_candidate_presets(validated_candidate)
        return validated_candidate

    def install_candidate_workflow(self, candidate: CandidateActionPack) -> InstalledActionPack:
        validated_candidate = self.validate_candidate_workflow(candidate)
        if validated_candidate.pack_id in {pack.pack_id for pack in self.list_catalog_packs_detailed()}:
            raise ValidationFailure(
                f"A workflow pack with id '{validated_candidate.pack_id}' already exists in the catalog."
            )
        return self.action_pack_store.install_candidate(validated_candidate)

    def preview_action(
        self,
        pack_id: str,
        action_id: str,
        goal_text: str,
        input_text: str,
        selected_preset_id: str | None,
    ) -> dict[str, Any]:
        pack = self.get_catalog_pack(pack_id)
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

    def preview_builtin_action(
        self,
        pack_id: str,
        action_id: str,
        goal_text: str,
        input_text: str,
        selected_preset_id: str | None,
    ) -> dict[str, Any]:
        return self.preview_action(
            pack_id=pack_id,
            action_id=action_id,
            goal_text=goal_text,
            input_text=input_text,
            selected_preset_id=selected_preset_id,
        )

    def execute_action(
        self,
        pack_id: str,
        action_id: str,
        goal_text: str,
        input_text: str,
        selected_preset_id: str | None,
    ) -> dict[str, Any]:
        preview = self.preview_action(
            pack_id=pack_id,
            action_id=action_id,
            goal_text=goal_text,
            input_text=input_text,
            selected_preset_id=selected_preset_id,
        )

        if not self.gateway.is_configured():
            return {
                "mode": "unavailable",
                "message": (
                    "Live execution is unavailable. Configure OPENAI_API_KEY and AI_WORKBENCH_MODEL in .env "
                    "to run installed workflows against the model gateway."
                ),
                "preview": preview,
            }

        try:
            generation = self.gateway.generate_text(
                system_prompt=str(preview["system_prompt"]),
                user_prompt=str(preview["user_prompt"]),
            )
        except Exception as exc:
            return {
                "mode": "error",
                "message": f"Live execution failed: {exc}",
                "preview": preview,
            }

        return {
            "mode": "live",
            "output_text": generation.output_text,
            "preview": preview,
            "request": generation.request.to_dict(),
        }

    def execute_builtin_action(
        self,
        pack_id: str,
        action_id: str,
        goal_text: str,
        input_text: str,
        selected_preset_id: str | None,
    ) -> dict[str, Any]:
        return self.execute_action(
            pack_id=pack_id,
            action_id=action_id,
            goal_text=goal_text,
            input_text=input_text,
            selected_preset_id=selected_preset_id,
        )

    def _validate_candidate_presets(self, candidate: CandidateActionPack) -> None:
        valid_preset_ids = {preset.preset_id for preset in self.list_builtin_presets_detailed()}
        invalid_recommended = [preset_id for preset_id in candidate.recommended_preset_ids if preset_id not in valid_preset_ids]
        if invalid_recommended:
            raise ValidationFailure(
                "Candidate workflow references unknown recommended presets: "
                + ", ".join(sorted(invalid_recommended))
            )

        invalid_defaults = [
            action.default_preset_id
            for action in candidate.actions
            if action.default_preset_id and action.default_preset_id not in valid_preset_ids
        ]
        if invalid_defaults:
            raise ValidationFailure(
                "Candidate workflow references unknown action default presets: "
                + ", ".join(sorted(set(invalid_defaults)))
            )

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