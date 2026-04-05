from __future__ import annotations

import json
from typing import Any, Callable

from adaptive_ai_workbench.domain.errors import ConfigurationError, ValidationFailure, WorkbenchError
from adaptive_ai_workbench.domain.models import (
    ActionDefinition,
    CandidateActionPack,
    InstalledActionPack,
    PresetDefinition,
)
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
            f"{len(self.state.available_packs)} installed packs, and {len(self.state.available_presets)} presets."
        )
        if self.state.available_presets and self.state.selected_preset is None:
            self.state.selected_preset = self.state.available_presets[0]
            self.append_status(f"Selected preset: {self.state.selected_preset}")
        if self.state.available_packs:
            self.handle_pack_selected(self.state.available_packs[0])

    def handle_refresh_catalog(self) -> None:
        if self.state.busy:
            self.append_status("Wait for the current operation to finish before refreshing the catalog.")
            return

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

    def begin_generate_workflow(self, goal_text: str) -> Callable[[], CandidateActionPack] | None:
        if self.state.busy:
            self.append_status("Wait for the current operation to finish before generating another workflow.")
            return None

        self.state.goal_text = goal_text
        self.state.busy = True
        self.state.inspector_text = "Generating workflow candidate...\nThe candidate preview will appear here when the model responds."
        self.append_status("Generating workflow candidate from the current goal...")
        return lambda: self.service.generate_candidate_workflow(goal_text)

    def finish_generate_workflow(self, candidate: CandidateActionPack) -> None:
        self.state.busy = False
        self.state.candidate_pack = candidate
        self.state.inspector_text = self._render_candidate_details(candidate)
        self.append_status(
            f"Generated candidate workflow: {candidate.title}. Review it and install when ready."
        )

    def fail_generate_workflow(self, error: Exception) -> None:
        self.state.busy = False
        self.state.candidate_pack = None
        if isinstance(error, ConfigurationError):
            self.state.inspector_text = self._render_generation_error(
                "Workflow Generation Unavailable",
                str(error),
            )
            self.append_status(str(error))
            return
        if isinstance(error, WorkbenchError):
            self.state.inspector_text = self._render_generation_error(
                "Workflow Generation Failed",
                str(error),
            )
            self.append_status(f"Workflow generation failed: {error}")
            return

        self.state.inspector_text = self._render_generation_error(
            "Workflow Generation Failed",
            f"Unexpected error: {error}",
        )
        self.append_status(f"Workflow generation failed unexpectedly: {error}")

    def handle_generate_workflow(self, goal_text: str) -> None:
        task = self.begin_generate_workflow(goal_text)
        if task is None:
            return
        try:
            candidate = task()
        except Exception as exc:
            self.fail_generate_workflow(exc)
            return
        self.finish_generate_workflow(candidate)

    def handle_install_candidate(self) -> None:
        if self.state.busy:
            self.append_status("Wait for the current operation to finish before installing a workflow.")
            return
        if self.state.candidate_pack is None:
            self.append_status("Generate a candidate workflow before installing it.")
            return

        try:
            installed = self.service.install_candidate_workflow(self.state.candidate_pack)
        except WorkbenchError as exc:
            self.state.inspector_text = self._render_generation_error("Workflow Installation Failed", str(exc))
            self.append_status(f"Workflow installation failed: {exc}")
            return

        self.state.candidate_pack = None
        self._reload_catalog()
        self.handle_pack_selected(installed.pack_id)
        self.append_status(f"Installed workflow pack: {installed.name}.")

    def handle_pack_selected(self, pack_id: str | None) -> None:
        if self.state.busy or not pack_id or pack_id not in self._packs:
            return

        pack = self._packs[pack_id]
        self.state.selected_pack = pack_id
        self.state.selected_action = None
        self.state.available_actions = [action.action_id for action in pack.actions]
        if pack.recommended_preset_ids and self.state.selected_preset not in pack.recommended_preset_ids:
            self.state.selected_preset = pack.recommended_preset_ids[0]
        self.state.inspector_text = self._render_pack_details(pack)
        self.append_status(f"Selected installed pack: {pack.name}")

    def handle_action_selected(self, action_id: str | None, goal_text: str, input_text: str) -> None:
        if self.state.busy or not action_id or not self.state.selected_pack:
            return

        pack = self._packs.get(self.state.selected_pack)
        if pack is None:
            return

        action = self._find_action(pack, action_id)
        preview = self.service.preview_action(
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
        if self.state.busy or not preset_id or preset_id not in self._presets:
            return

        self.state.goal_text = goal_text
        self.state.input_text = input_text
        self.state.selected_preset = preset_id
        self.append_status(f"Selected preset: {self._presets[preset_id].name}")

        if self.state.selected_pack and self.state.selected_action:
            self.handle_action_selected(self.state.selected_action, goal_text, input_text)
        elif self.state.selected_pack:
            self.state.inspector_text = self._render_pack_details(self._packs[self.state.selected_pack])

    def begin_run_action(self, goal_text: str, input_text: str) -> Callable[[], dict[str, Any]] | None:
        self.state.goal_text = goal_text
        self.state.input_text = input_text

        if self.state.busy:
            self.append_status("Wait for the current operation to finish before running another action.")
            return None
        if not self.state.selected_pack:
            self.append_status("Select an installed workflow pack before running an action.")
            return None
        if not self.state.selected_action:
            self.append_status("Select an action before running.")
            return None

        pack_id = self.state.selected_pack
        action_id = self.state.selected_action
        selected_preset_id = self.state.selected_preset

        self.state.busy = True
        self.state.output_text = "Running workflow action...\nThe result will appear here when the model responds."
        self.append_status("Running installed workflow action...")
        return lambda: self.service.execute_action(
            pack_id=pack_id,
            action_id=action_id,
            goal_text=goal_text,
            input_text=input_text,
            selected_preset_id=selected_preset_id,
        )

    def finish_run_action(self, result: dict[str, Any]) -> None:
        self.state.busy = False
        mode = str(result["mode"])
        preview = result["preview"]

        if mode == "live":
            self.state.output_text = self._render_live_execution_result(result)
            self.append_status(
                f"Ran {preview['action_name']} live with preset {preview['preset_name']}."
            )
            return

        if mode == "unavailable":
            self.state.output_text = self._render_unavailable_result(result)
            self.append_status(str(result["message"]))
            return

        self.state.output_text = self._render_error_result(result)
        self.append_status(str(result["message"]))

    def fail_run_action(self, error: Exception) -> None:
        self.state.busy = False
        self.state.output_text = "Live Execution Failed\nUnexpected error while running the selected action."
        self.append_status(f"Unexpected run failure: {error}")

    def handle_run_action(self, goal_text: str, input_text: str) -> None:
        task = self.begin_run_action(goal_text, input_text)
        if task is None:
            return
        try:
            result = task()
        except Exception as exc:
            self.fail_run_action(exc)
            return
        self.finish_run_action(result)

    def append_status(self, message: str) -> None:
        self.state.status_lines.append(message)

    def _reload_catalog(self) -> None:
        packs = self.service.list_catalog_packs_detailed()
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
            f"Installed Workflow\n"
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
            f"Installed Workflow: {pack.name}\n"
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
    def _render_candidate_details(candidate: CandidateActionPack) -> str:
        action_lines = []
        for action in candidate.actions:
            action_lines.append(
                f"- {action.name} ({action.kind.value})\n"
                f"  Description: {action.description}\n"
                f"  Rationale: {action.rationale}\n"
                f"  Default Preset: {action.default_preset_id or 'None'}"
            )
        warnings = "\n".join(f"- {warning}" for warning in candidate.warnings) or "None"
        recommended_presets = ", ".join(candidate.recommended_preset_ids) or "None"
        generated_actions = "\n\n".join(action_lines)
        return (
            "Candidate Workflow\n"
            "Status: Candidate only. Review before installation.\n"
            f"Pack Title: {candidate.title}\n"
            f"Pack ID: {candidate.pack_id}\n"
            f"Summary: {candidate.summary}\n"
            f"Reasoning: {candidate.reasoning}\n"
            f"Warnings:\n{warnings}\n\n"
            f"Recommended Presets: {recommended_presets}\n\n"
            f"Generated Actions:\n{generated_actions}"
        )

    @staticmethod
    def _render_generation_error(title: str, message: str) -> str:
        return f"{title}\n{message}"

    @classmethod
    def _render_live_execution_result(cls, result: dict[str, object]) -> str:
        preview = result["preview"]
        request = result["request"]
        return (
            "Live Execution Result\n"
            f"Pack: {preview['pack_name']}\n"
            f"Action: {preview['action_name']}\n"
            f"Preset: {preview['preset_name']} ({preview['preset_id']})\n"
            f"Model: {request['model']}\n\n"
            "Generated Output:\n"
            f"{result['output_text']}\n\n"
            f"{cls._render_preview_block(preview)}"
        )

    @classmethod
    def _render_unavailable_result(cls, result: dict[str, object]) -> str:
        return (
            "Live Execution Unavailable\n"
            f"{result['message']}\n\n"
            f"{cls._render_preview_block(result['preview'])}"
        )

    @classmethod
    def _render_error_result(cls, result: dict[str, object]) -> str:
        return (
            "Live Execution Failed\n"
            f"{result['message']}\n\n"
            f"{cls._render_preview_block(result['preview'])}"
        )

    @staticmethod
    def _render_preview_block(preview: dict[str, object]) -> str:
        metadata = {
            "pack_id": preview["pack_id"],
            "action_id": preview["action_id"],
            "kind": preview["kind"],
            "handler": preview["handler"],
            "preset_id": preview["preset_id"],
        }
        return (
            "Execution Request Preview\n"
            f"Pack: {preview['pack_name']}\n"
            f"Action: {preview['action_name']}\n"
            f"Preset: {preview['preset_name']} ({preview['preset_id']})\n\n"
            f"System Prompt:\n{preview['system_prompt']}\n\n"
            f"User Prompt:\n{preview['user_prompt']}\n\n"
            f"Metadata:\n{json.dumps(metadata, indent=2)}"
        )
