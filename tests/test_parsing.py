import json

import pytest

from adaptive_ai_workbench.domain.errors import ModelOutputError
from adaptive_ai_workbench.safety.parsing import parse_candidate_action_pack


def build_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "pack_id": "client_email_workflow",
        "goal": "Help me write clearer client emails",
        "title": "Client Email Workflow",
        "summary": "Validated workflow for drafting and rewriting emails.",
        "reasoning": "The goal is email-focused.",
        "warnings": [],
        "recommended_preset_ids": ["professional_email"],
        "actions": [
            {
                "action_id": "draft_email",
                "name": "Draft Email",
                "description": "Create a polished email draft from notes.",
                "kind": "template_fill",
                "enabled": True,
                "rationale": "Drafting is a core need for this goal.",
                "input_mode": "single_text",
                "fields": [],
                "system_prompt": "You are an expert email assistant. Write with tone={tone}, language={language}, style={output_style}, length={length}.",
                "user_prompt_template": "Goal: {goal_text}\nInput:\n{input_text}",
                "default_preset_id": "professional_email",
                "tags": ["email", "drafting"],
            }
        ],
    }


def test_parse_clean_json() -> None:
    candidate = parse_candidate_action_pack(json.dumps(build_payload()))
    assert candidate.pack_id == "client_email_workflow"
    assert candidate.recommended_preset_ids == ["professional_email"]


def test_parse_json_wrapped_in_text() -> None:
    wrapped = f"Here is the result:\n{json.dumps(build_payload())}\nThanks."
    candidate = parse_candidate_action_pack(wrapped)
    assert candidate.actions[0].action_id == "draft_email"


def test_parse_raises_when_json_is_missing() -> None:
    with pytest.raises(ModelOutputError):
        parse_candidate_action_pack("No structured payload here.")


def test_parse_surfaces_clear_message_for_missing_required_action_fields() -> None:
    invalid_payload = build_payload()
    invalid_payload["actions"] = [
        {
            "description": "Incomplete action object.",
            "kind": "template_fill",
            "enabled": True,
            "rationale": "This should fail validation.",
            "input_mode": "single_text",
            "fields": [],
            "default_preset_id": "professional_email",
            "tags": [],
        }
    ]

    with pytest.raises(ModelOutputError) as error:
        parse_candidate_action_pack(json.dumps(invalid_payload))

    message = str(error.value)
    assert "Generated workflow is missing required action fields." in message
    assert "action_id" in message
    assert "name" in message
    assert "system_prompt" in message
    assert "user_prompt_template" in message