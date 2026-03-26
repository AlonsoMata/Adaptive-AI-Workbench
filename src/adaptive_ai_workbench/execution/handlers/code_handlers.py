from __future__ import annotations

from typing import Any

from adaptive_ai_workbench.domain.models import ActionDefinition, PresetDefinition
from adaptive_ai_workbench.execution.handlers.text_handlers import _build_preview


def handle_code_action(
    action: ActionDefinition,
    input_text: str,
    preset: PresetDefinition,
    goal_text: str,
) -> dict[str, Any]:
    return _build_preview("code", action, input_text, preset, goal_text)
