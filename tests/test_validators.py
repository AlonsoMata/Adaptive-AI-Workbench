from datetime import datetime, timezone

import pytest

from adaptive_ai_workbench.domain.enums import InputMode, PackSource
from adaptive_ai_workbench.domain.errors import ValidationFailure
from adaptive_ai_workbench.domain.models import ActionDefinition, CandidateActionPack, InputFieldDefinition
from adaptive_ai_workbench.safety.validators import (
    find_generated_candidate_quality_issues,
    install_candidate_pack,
    validate_candidate_pack,
)


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


def test_generated_candidate_quality_accepts_useful_pack() -> None:
    assert find_generated_candidate_quality_issues(build_candidate(), build_candidate().goal) == []


def test_generated_candidate_quality_rejects_meta_planning_heavy_pack() -> None:
    base_action = build_candidate().actions[0]
    candidate = build_candidate().model_copy(
        update={
            "actions": [
                base_action.model_copy(
                    update={
                        "action_id": "plan_email_workflow",
                        "name": "Plan Email Workflow",
                        "description": "Plan how the email work should be handled before any draft is written.",
                        "rationale": "A workflow plan comes first.",
                        "kind": "prompt_transform",
                        "tags": ["planning", "workflow"],
                    }
                ),
                base_action.model_copy(
                    update={
                        "action_id": "outline_email_strategy",
                        "name": "Outline Email Strategy",
                        "description": "Create a strategy outline for approaching the email task.",
                        "rationale": "The strategy should be defined before doing the work.",
                        "kind": "prompt_transform",
                        "tags": ["strategy", "planning"],
                    }
                ),
            ]
        }
    )

    issues = find_generated_candidate_quality_issues(candidate, candidate.goal)

    assert any("overly meta or planning-heavy" in issue for issue in issues)


def test_generated_candidate_quality_rejects_weakly_differentiated_actions() -> None:
    base_action = build_candidate().actions[0]
    candidate = build_candidate().model_copy(
        update={
            "actions": [
                base_action.model_copy(
                    update={
                        "action_id": "draft_email",
                        "name": "Draft Email",
                        "description": "Create an email draft from rough notes.",
                        "rationale": "Drafting is one version of the output.",
                    }
                ),
                base_action.model_copy(
                    update={
                        "action_id": "write_email",
                        "name": "Write Email",
                        "description": "Write an email from the same rough notes.",
                        "rationale": "Writing is another version of the same output.",
                    }
                ),
                base_action.model_copy(
                    update={
                        "action_id": "compose_email",
                        "name": "Compose Email",
                        "description": "Compose an email from the same rough notes.",
                        "rationale": "Composing repeats the same output pattern again.",
                    }
                ),
            ]
        }
    )

    issues = find_generated_candidate_quality_issues(candidate, candidate.goal)

    assert any("weakly differentiated" in issue for issue in issues)


def test_generated_candidate_quality_rejects_pack_that_does_not_match_goal() -> None:
    candidate = build_candidate().model_copy(
        update={
            "actions": [
                build_candidate().actions[0].model_copy(
                    update={
                        "action_id": "analyze_pokemon_team",
                        "name": "Analyze Pokemon Team",
                        "description": "Evaluate a competitive monster team and suggest battle roles.",
                        "rationale": "Battle role analysis helps improve matchups.",
                        "tags": ["pokemon", "battle"],
                    }
                )
            ]
        }
    )

    issues = find_generated_candidate_quality_issues(candidate, candidate.goal)

    assert any("do not clearly align with the requested outcome" in issue for issue in issues)
