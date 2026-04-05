from datetime import datetime, timezone

from adaptive_ai_workbench.domain.enums import PackSource
from adaptive_ai_workbench.domain.models import ActionDefinition, CandidateActionPack
from adaptive_ai_workbench.safety.validators import install_candidate_pack


def build_candidate() -> CandidateActionPack:
    return CandidateActionPack(
        pack_id="client_email_workflow",
        goal="Help me write clearer client emails",
        title="Client Email Workflow",
        summary="Validated workflow for drafting and rewriting emails.",
        reasoning="The goal is email-focused.",
        recommended_preset_ids=["professional_email"],
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
                system_prompt="You are an expert email assistant. Write with tone={tone}, language={language}, style={output_style}, length={length}.",
                user_prompt_template="Goal: {goal_text}\nInput:\n{input_text}",
                default_preset_id="professional_email",
                tags=["email", "drafting"],
            )
        ],
    )


def test_install_candidate_pack_preserves_actions_source_and_presets() -> None:
    installed = install_candidate_pack(build_candidate(), source=PackSource.generated)

    assert installed.pack_id == "client_email_workflow"
    assert installed.name == "Client Email Workflow"
    assert installed.source is PackSource.generated
    assert installed.actions[0].action_id == "draft_email"
    assert installed.recommended_preset_ids == ["professional_email"]


def test_install_candidate_pack_uses_timezone_aware_utc_timestamp() -> None:
    installed = install_candidate_pack(build_candidate())
    timestamp = datetime.fromisoformat(installed.installed_at)

    assert timestamp.tzinfo is not None
    assert timestamp.utcoffset() == timezone.utc.utcoffset(timestamp)