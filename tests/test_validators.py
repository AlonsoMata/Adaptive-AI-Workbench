from datetime import datetime, timezone

import pytest

from adaptive_ai_workbench.domain.enums import InputMode, PackSource
from adaptive_ai_workbench.domain.errors import ValidationFailure
from adaptive_ai_workbench.domain.models import ActionDefinition, CandidateActionPack, InputFieldDefinition
from adaptive_ai_workbench.safety.validators import install_candidate_pack, validate_candidate_pack


def build_candidate() -> CandidateActionPack:
    return CandidateActionPack(
        pack_id="client_email_workflow",
        goal="Help me write clearer client emails",
        title="Client Email Workflow",
        summary="Validated workflow for drafting and rewriting emails.",
        reasoning="The goal is email-focused.",
        recommended_preset_ids=["professional_clear"],
        actions=[
            ActionDefinition(
                action_id="draft_email",
                name="Draft Email",
                description="Create a polished email draft from notes.",
                kind="template_fill",
                enabled=True,
                rationale="Drafting is a core need for this goal.",
                input_mode="single_text",
                fields=[],
                system_prompt="You are an expert email assistant. Write with tone={tone}, language={language}, style={output_style}, length={length}, format={format}, strictness={strictness}.",
                user_prompt_template="Goal: {goal_text}\nInput:\n{input_text}",
                default_preset_id="professional_clear",
                tags=["email", "drafting"],
            )
        ],
    )


def test_install_candidate_pack_preserves_actions_source_and_profiles() -> None:
    installed = install_candidate_pack(build_candidate(), source=PackSource.generated)

    assert installed.pack_id == "client_email_workflow"
    assert installed.name == "Client Email Workflow"
    assert installed.source is PackSource.generated
    assert installed.actions[0].action_id == "draft_email"
    assert installed.recommended_preset_ids == ["professional_clear"]


def test_install_candidate_pack_uses_timezone_aware_utc_timestamp() -> None:
    installed = install_candidate_pack(build_candidate())
    timestamp = datetime.fromisoformat(installed.installed_at)

    assert timestamp.tzinfo is not None
    assert timestamp.utcoffset() == timezone.utc.utcoffset(timestamp)


def test_validate_candidate_pack_rejects_duplicate_action_ids() -> None:
    candidate = build_candidate().model_copy(
        update={
            "actions": [
                build_candidate().actions[0],
                build_candidate().actions[0].model_copy(update={"name": "Second Draft"}),
            ]
        }
    )

    with pytest.raises(ValidationFailure) as error:
        validate_candidate_pack(candidate)

    assert "action_id values must be unique" in str(error.value)


def test_validate_candidate_pack_rejects_unsupported_prompt_placeholders() -> None:
    candidate = build_candidate().model_copy(
        update={
            "actions": [
                build_candidate().actions[0].model_copy(
                    update={"user_prompt_template": "Job description:\n{job_description}"}
                )
            ]
        }
    )

    with pytest.raises(ValidationFailure) as error:
        validate_candidate_pack(candidate)

    message = str(error.value)
    assert "unsupported placeholders" in message
    assert "job_description" in message


def test_validate_candidate_pack_rejects_structured_fields_actions() -> None:
    candidate = build_candidate().model_copy(
        update={
            "actions": [
                build_candidate().actions[0].model_copy(
                    update={
                        "input_mode": InputMode.structured_fields,
                        "fields": [
                            InputFieldDefinition(
                                name="job_title",
                                label="Job Title",
                                required=True,
                                placeholder="Senior ML Engineer",
                            )
                        ],
                    }
                )
            ]
        }
    )

    with pytest.raises(ValidationFailure) as error:
        validate_candidate_pack(candidate)

    assert "structured_fields actions are not currently supported" in str(error.value)
