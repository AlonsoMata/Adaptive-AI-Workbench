from types import SimpleNamespace

import pytest

from adaptive_ai_workbench.domain.enums import ActionKind
from adaptive_ai_workbench.domain.errors import ValidationFailure
from adaptive_ai_workbench.domain.models import ActionDefinition, ResponseControls
from adaptive_ai_workbench.execution.dispatcher import ExecutionDispatcher


def build_action(kind: ActionKind) -> ActionDefinition:
    return ActionDefinition(
        action_id=f"{kind.value}_action",
        name="Test Action",
        description="Preview this action.",
        kind=kind,
        enabled=True,
        rationale="Used in dispatcher tests.",
        input_mode="single_text",
        fields=[],
        system_prompt="Use tone={tone}, language={language}, style={output_style}, length={length}, format={format}, strictness={strictness}.",
        user_prompt_template="Goal: {goal_text}\nInput:\n{input_text}",
        default_preset_id="professional_clear",
        tags=["test"],
    )


def build_controls() -> ResponseControls:
    return ResponseControls(
        tone="professional",
        language="en",
        output_style="clear",
        length="medium",
        format="paragraph",
        strictness="medium",
    )


@pytest.mark.parametrize(
    ("kind", "expected_handler"),
    [
        (ActionKind.prompt_transform, "text"),
        (ActionKind.text_rewrite, "text"),
        (ActionKind.summarization, "text"),
        (ActionKind.translation, "text"),
        (ActionKind.extraction, "text"),
        (ActionKind.template_fill, "text"),
        (ActionKind.code_review, "code"),
        (ActionKind.code_refactor_prompt, "code"),
        (ActionKind.cv_improvement, "cv"),
    ],
)
def test_dispatcher_routes_supported_kinds(kind: ActionKind, expected_handler: str) -> None:
    dispatcher = ExecutionDispatcher()
    result = dispatcher.dispatch(
        action=build_action(kind),
        input_text="Sample input",
        response_controls=build_controls(),
        goal_text="Sample goal",
    )

    assert result["handler"] == expected_handler
    assert result["kind"] == kind.value
    assert result["format"] == "paragraph"
    assert result["strictness"] == "medium"


def test_dispatcher_rejects_unknown_kind() -> None:
    dispatcher = ExecutionDispatcher()
    unknown_action = SimpleNamespace(kind="unsupported_kind")

    with pytest.raises(ValidationFailure):
        dispatcher.dispatch(
            action=unknown_action,
            input_text="Sample input",
            response_controls=build_controls(),
            goal_text="Sample goal",
        )
