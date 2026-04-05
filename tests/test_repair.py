from adaptive_ai_workbench.safety.repair import repair_candidate_payload


def test_repair_candidate_payload_is_conservative() -> None:
    payload = {
        "pack_id": "  generated_email_helper  ",
        "goal": "  Help me write better emails  ",
        "title": "  Generated Email Helper  ",
        "summary": "  Generated workflow summary.  ",
        "reasoning": "  Email-focused goal.  ",
        "recommended_preset_ids": [" professional_email "],
        "warnings": [" keep outputs concise "],
        "actions": [
            {
                "action_id": " draft_email ",
                "name": " Draft Email ",
                "description": " Build a draft ",
                "kind": "template_fill",
                "enabled": "true",
                "rationale": " Drafting is useful ",
                "input_mode": "single_text",
                "fields": [],
                "system_prompt": " Use tone={tone}. ",
                "user_prompt_template": " Goal: {goal_text} ",
                "unknown_action_key": "ignored",
            }
        ],
        "unknown_top_level": "ignored",
    }

    repaired = repair_candidate_payload(payload)

    assert repaired["schema_version"] == "1.0"
    assert repaired["pack_id"] == "generated_email_helper"
    assert repaired["recommended_preset_ids"] == ["professional_email"]
    assert repaired["actions"][0]["enabled"] is True
    assert "unknown_top_level" not in repaired
    assert "unknown_action_key" not in repaired["actions"][0]