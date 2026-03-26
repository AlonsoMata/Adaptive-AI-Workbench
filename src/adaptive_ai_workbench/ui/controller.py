from __future__ import annotations

import json

from adaptive_ai_workbench.domain.errors import ValidationFailure
from adaptive_ai_workbench.domain.models import ActionDefinition, InstalledActionPack, PresetDefinition
from adaptive_ai_workbench.services.workbench_service import WorkbenchService
from adaptive_ai_workbench.ui.state import AppState


class AppController:
    def __init__(self, service: WorkbenchService, state: AppState) -> None:
        self.service = service
        self.state = state
        self._packs: dict[str, InstalledActionPack] = {}
        self._presets: dict[str, PresetDefinition] = {}

    def bootstrap(self) -> None:
        self._reload_catalog()
        self.append_status(self.service.health_status())
        self.append_status(
            f"Discovered {len(self.service.list_builtin_prompt_names())} prompt templates, "
            f"{len(self.state.available_packs)} packs, and {len(self.state.available_presets)} presets."
        )
        if self.state.available_presets and self.state.selected_preset is None:
            self.state.selected_preset = self.state.available_presets[0]
            self.append_status(f"Selected preset: {self.state.selected_preset}")
        if self.state.available_packs:
            self.handle_pack_selected(self.state.available_packs[0])

    def handle_refresh_catalog(self) -> None:
        previous_pack = self.state.selected_pack
        previous_preset = self.state.selected_preset
        previous_action = self.state.selected_action

        self._reload_catalog()
        if previous_preset in self._presets:
            self.state.selected_preset = previous_preset
        elif self.state.available_presets:
            self.state.selected_preset = self.state.available_presets[0]

        if previous_pack in self._packs:
            self.handle_pack_selected(previous_pack)
            if previous_action in self.state.available_actions:
                self.handle_action_selected(previous_action, self.state.goal_text, self.state.input_text)
        elif self.state.available_packs:
            self.handle_pack_selected(self.state.available_packs[0])

        self.append_status("Catalog refreshed from disk.")

    def handle_clear_output(self) -> None:
        self.state.output_text = ""
        self.append_status("Output cleared.")

    def handle_pack_selected(self, pack_id: str | None) -> None:
        if not pack_id or pack_id not in self._packs:
            return

        pack = self._packs[pack_id]
        self.state.selected_pack = pack_id
        self.state.selected_action = None
        self.state.available_actions = [action.action_id for action in pack.actions]
        if pack.recommended_preset_ids and self.state.selected_preset not in pack.recommended_preset_ids:
            self.state.selected_preset = pack.recommended_preset_ids[0]
        self.state.inspector_text = self._render_pack_details(pack)
        self.append_status(f"Selected pack: {pack.name}")

    def handle_action_selected(self, action_id: str | None, goal_text: str, input_text: str) -> None:
        if not action_id or not self.state.selected_pack:
            return

        pack = self._packs.get(self.state.selected_pack)
        if pack is None:
            return

        action = self._find_action(pack, action_id)
        preview = self.service.preview_builtin_action(
            pack_id=pack.pack_id,
            action_id=action.action_id,
            goal_text=goal_text,
            input_text=input_text,
            selected_preset_id=self.state.selected_preset,
        )
        preset = self.service.resolve_preset_for_action(pack, action, self.state.selected_preset)

        self.state.goal_text = goal_text
        self.state.input_text = input_text
        self.state.selected_action = action_id
        self.state.selected_preset = preset.preset_id
        self.state.inspector_text = self._render_action_details(pack, action, preset, preview)
        self.append_status(f"Selected action: {action.name}")

    def handle_preset_selected(self, preset_id: str | None, goal_text: str, input_text: str) -> None:
        if not preset_id or preset_id not in self._presets:
            return

        self.state.goal_text = goal_text
        self.state.input_text = input_text
        self.state.selected_preset = preset_id
        self.append_status(f"Selected preset: {self._presets[preset_id].name}")

        if self.state.selected_pack and self.state.selected_action:
            self.handle_action_selected(self.state.selected_action, goal_text, input_text)
        elif self.state.selected_pack:
            self.state.inspector_text = self._render_pack_details(self._packs[self.state.selected_pack])

    def handle_run_action(self, goal_text: str, input_text: str) -> None:
        self.state.goal_text = goal_text
        self.state.input_text = input_text

        if not self.state.selected_pack:
            self.append_status("Select a built-in pack before running an action.")
            return
        if not self.state.selected_action:
            self.append_status("Select an action before running.")
            return

        preview = self.service.preview_builtin_action(
            pack_id=self.state.selected_pack,
            action_id=self.state.selected_action,
            goal_text=goal_text,
            input_text=input_text,
            selected_preset_id=self.state.selected_preset,
        )
        self.state.output_text = self._render_execution_result(preview)
        self.append_status(
            f"Ran {preview['action_name']} with preset {preview['preset_name']}."
        )

    def append_status(self, message: str) -> None:
        self.state.status_lines.append(message)

    def _reload_catalog(self) -> None:
        packs = self.service.list_builtin_packs_detailed()
        presets = self.service.list_builtin_presets_detailed()
        self._packs = {pack.pack_id: pack for pack in packs}
        self._presets = {preset.preset_id: preset for preset in presets}
        self.state.available_packs = [pack.pack_id for pack in packs]
        self.state.available_presets = [preset.preset_id for preset in presets]

        if self.state.selected_pack not in self._packs:
            self.state.selected_pack = None
            self.state.selected_action = None
            self.state.available_actions = []
        if self.state.selected_preset not in self._presets:
            self.state.selected_preset = None

    @staticmethod
    def _find_action(pack: InstalledActionPack, action_id: str) -> ActionDefinition:
        for action in pack.actions:
            if action.action_id == action_id:
                return action
        raise ValidationFailure(f"Action not found in pack {pack.pack_id}: {action_id}")

    @staticmethod
    def _render_pack_details(pack: InstalledActionPack) -> str:
        action_lines = "\n".join(f"- {action.name} ({action.kind.value})" for action in pack.actions)
        return (
            f"Pack Name: {pack.name}\n"
            f"Pack ID: {pack.pack_id}\n"
            f"Description: {pack.description}\n"
            f"Source: {pack.source.value}\n"
            f"Enabled: {'Yes' if pack.enabled else 'No'}\n"
            f"Recommended Presets: {', '.join(pack.recommended_preset_ids) or 'None'}\n\n"
            f"Available Actions:\n{action_lines}"
        )

    @staticmethod
    def _render_action_details(
        pack: InstalledActionPack,
        action: ActionDefinition,
        preset: PresetDefinition,
        preview: dict[str, object],
    ) -> str:
        return (
            f"Pack: {pack.name}\n"
            f"Action Name: {action.name}\n"
            f"Action ID: {action.action_id}\n"
            f"Kind: {action.kind.value}\n"
            f"Description: {action.description}\n"
            f"Rationale: {action.rationale}\n"
            f"Default Preset: {action.default_preset_id or 'None'}\n"
            f"Selected Preset: {preset.name} ({preset.preset_id})\n"
            f"Enabled: {'Yes' if action.enabled else 'No'}\n\n"
            f"Prompt Preview\n"
            f"System Prompt:\n{preview['system_prompt']}\n\n"
            f"User Prompt:\n{preview['user_prompt']}"
        )

    @staticmethod
    def _render_execution_result(preview: dict[str, object]) -> str:
        metadata = {
            "pack_id": preview["pack_id"],
            "action_id": preview["action_id"],
            "kind": preview["kind"],
            "handler": preview["handler"],
            "preset_id": preview["preset_id"],
        }
        return (
            "Execution Preview\n"
            "This workflow currently returns a structured preview instead of a live model response.\n\n"
            f"Pack: {preview['pack_name']}\n"
            f"Action: {preview['action_name']}\n"
            f"Preset: {preview['preset_name']} ({preview['preset_id']})\n\n"
            f"System Prompt:\n{preview['system_prompt']}\n\n"
            f"User Prompt:\n{preview['user_prompt']}\n\n"
            f"Metadata:\n{json.dumps(metadata, indent=2)}"
        )
