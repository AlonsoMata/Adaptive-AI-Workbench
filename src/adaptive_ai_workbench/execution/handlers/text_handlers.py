from __future__ import annotations

from typing import Any

from adaptive_ai_workbench.domain.models import ActionDefinition, PresetDefinition


def handle_text_action(
    action: ActionDefinition,
    input_text: str,
    preset: PresetDefinition,
    goal_text: str,
) -> dict[str, Any]:
    return _build_preview("text", action, input_text, preset, goal_text)


def _build_preview(
    handler_name: str,
    action: ActionDefinition,
    input_text: str,
    preset: PresetDefinition,
    goal_text: str,
) -> dict[str, Any]:
    context = {
        "goal_text": goal_text,
        "input_text": input_text,
        "tone": preset.tone,
        "language": preset.language,
        "output_style": preset.output_style,
        "length": preset.length,
        "instruction_text": action.description,
    }
    return {
        "handler": handler_name,
        "action_id": action.action_id,
        "kind": action.kind.value,
        "system_prompt": action.system_prompt.format(**context),
        "user_prompt": action.user_prompt_template.format(**context),
        "preset_id": preset.preset_id,
    }
