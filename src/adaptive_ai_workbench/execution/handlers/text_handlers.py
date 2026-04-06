from __future__ import annotations

from typing import Any

from adaptive_ai_workbench.domain.models import ActionDefinition, ResponseControls


def handle_text_action(
    action: ActionDefinition,
    input_text: str,
    response_controls: ResponseControls,
    goal_text: str,
) -> dict[str, Any]:
    return _build_preview("text", action, input_text, response_controls, goal_text)


def _build_preview(
    handler_name: str,
    action: ActionDefinition,
    input_text: str,
    response_controls: ResponseControls,
    goal_text: str,
) -> dict[str, Any]:
    context = {
        "goal_text": goal_text,
        "input_text": input_text,
        "tone": response_controls.tone,
        "language": response_controls.language,
        "output_style": response_controls.output_style,
        "length": response_controls.length,
        "format": response_controls.format,
        "strictness": response_controls.strictness,
        "instruction_text": action.description,
    }
    formatted_system_prompt = action.system_prompt.format(**context)
    formatted_user_prompt = action.user_prompt_template.format(**context)
    control_suffix = (
        f"\n\nUniversal response controls: tone={response_controls.tone}, "
        f"language={response_controls.language}, style={response_controls.output_style}, "
        f"length={response_controls.length}, format={response_controls.format}, "
        f"strictness={response_controls.strictness}."
    )
    return {
        "handler": handler_name,
        "action_id": action.action_id,
        "kind": action.kind.value,
        "system_prompt": formatted_system_prompt + control_suffix,
        "user_prompt": formatted_user_prompt,
        "tone": response_controls.tone,
        "language": response_controls.language,
        "output_style": response_controls.output_style,
        "length": response_controls.length,
        "format": response_controls.format,
        "strictness": response_controls.strictness,
    }
