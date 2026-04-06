from __future__ import annotations

from adaptive_ai_workbench.domain.models import ActionDefinition, ResponseControls
from adaptive_ai_workbench.execution.handlers.text_handlers import _build_preview


def handle_code_action(
    action: ActionDefinition,
    input_text: str,
    response_controls: ResponseControls,
    goal_text: str,
) -> dict[str, object]:
    return _build_preview("code", action, input_text, response_controls, goal_text)
