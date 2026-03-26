from __future__ import annotations

from collections.abc import Callable
from typing import Any

from adaptive_ai_workbench.domain.enums import ActionKind
from adaptive_ai_workbench.domain.errors import ValidationFailure
from adaptive_ai_workbench.domain.models import ActionDefinition, PresetDefinition
from adaptive_ai_workbench.execution.handlers import (
    handle_code_action,
    handle_cv_action,
    handle_text_action,
)


HandlerFunc = Callable[[ActionDefinition, str, PresetDefinition, str], dict[str, Any]]


class ExecutionDispatcher:
    def __init__(self) -> None:
        self._handlers: dict[ActionKind, HandlerFunc] = {
            ActionKind.prompt_transform: handle_text_action,
            ActionKind.text_rewrite: handle_text_action,
            ActionKind.summarization: handle_text_action,
            ActionKind.translation: handle_text_action,
            ActionKind.extraction: handle_text_action,
            ActionKind.template_fill: handle_text_action,
            ActionKind.code_review: handle_code_action,
            ActionKind.code_refactor_prompt: handle_code_action,
            ActionKind.cv_improvement: handle_cv_action,
        }

    def get_supported_kinds(self) -> list[ActionKind]:
        return sorted(self._handlers.keys(), key=lambda kind: kind.value)

    def dispatch(
        self,
        action: ActionDefinition,
        input_text: str,
        preset: PresetDefinition,
        goal_text: str,
    ) -> dict[str, Any]:
        handler = self._handlers.get(action.kind)
        if handler is None:
            raise ValidationFailure(f"Unsupported action kind: {action.kind}")
        return handler(action, input_text, preset, goal_text)
