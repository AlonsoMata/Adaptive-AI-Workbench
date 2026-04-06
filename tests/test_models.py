from pydantic import ValidationError
import pytest

from adaptive_ai_workbench.domain.models import ActionDefinition, CandidateActionPack, ResponseControls


def build_action(kind: str = "template_fill") -> dict[str, object]:
    return {
        "action_id": "draft_email",
        "name": "Draft Email",
        "description": "Create a polished draft.",
        "kind": kind,
        "enabled": True,
        "rationale": "Drafting is a core workflow.",
        "input_mode": "single_text",
        "fields": [],
        "system_prompt": "Write with tone={tone}, language={language}, style={output_style}, length={length}, format={format}, strictness={strictness}.",
        "user_prompt_template": "Goal: {goal_text}\nInput:\n{input_text}",
        "default_preset_id": "professional_clear",
        "tags": ["email"],
    }


def test_valid_models_are_accepted() -> None:
    candidate = CandidateActionPack(
        pack_id="client_email_workflow",
        goal="Help me write clearer emails",
        title="Client Email Workflow",
        summary="Reusable email workflows.",
        reasoning="Email work needs drafting and rewriting support.",
        actions=[ActionDefinition(**build_action())],
        recommended_preset_ids=["professional_clear"],
    )

    assert candidate.schema_version == "1.0"
    assert candidate.actions[0].kind.value == "template_fill"


def test_unknown_kind_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ActionDefinition(**build_action(kind="run_shell"))


def test_ids_with_spaces_are_rejected() -> None:
    with pytest.raises(ValidationError):
        CandidateActionPack(
            pack_id="bad id",
            goal="Goal",
            title="Title",
            summary="Summary",
            reasoning="Reasoning",
            actions=[ActionDefinition(**build_action())],
        )


def test_empty_action_list_is_rejected() -> None:
    with pytest.raises(ValidationError):
        CandidateActionPack(
            pack_id="empty_pack",
            goal="Goal",
            title="Title",
            summary="Summary",
            reasoning="Reasoning",
            actions=[],
        )


def test_response_controls_validation_is_strict() -> None:
    controls = ResponseControls(
        tone="professional",
        length="medium",
        language="en",
        output_style="clear",
        format="paragraph",
        strictness="medium",
    )

    assert controls.tone == "professional"
    assert controls.format == "paragraph"

    with pytest.raises(ValidationError):
        ResponseControls(
            tone="confident",
            length="balanced",
            language="en",
            output_style="technical",
            format="essay",
            strictness="extreme",
        )
