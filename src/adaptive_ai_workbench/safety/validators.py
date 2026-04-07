from __future__ import annotations

import string
from datetime import datetime, timezone

from adaptive_ai_workbench.domain.enums import InputMode, PackSource
from adaptive_ai_workbench.domain.errors import ValidationFailure
from adaptive_ai_workbench.domain.models import ActionDefinition, CandidateActionPack, InstalledActionPack

_ALLOWED_PROMPT_PLACEHOLDERS = {
    "goal_text",
    "input_text",
    "tone",
    "language",
    "output_style",
    "length",
    "format",
    "strictness",
    "instruction_text",
}
_PROMPT_FORMATTER = string.Formatter()


def validate_candidate_pack(candidate: CandidateActionPack) -> CandidateActionPack:
    try:
        validated = CandidateActionPack.model_validate(candidate.model_dump())
    except Exception as exc:
        raise ValidationFailure(f"Candidate pack validation failed: {exc}") from exc
    _validate_unique_action_ids(validated)
    _validate_supported_input_modes(validated)
    _validate_action_prompt_placeholders(validated)
    return validated


def install_candidate_pack(
    candidate: CandidateActionPack,
    source: PackSource = PackSource.generated,
) -> InstalledActionPack:
    validated = validate_candidate_pack(candidate)
    try:
        return InstalledActionPack(
            schema_version=validated.schema_version,
            pack_id=validated.pack_id,
            name=validated.title,
            description=validated.summary,
            source=source,
            origin_goal=validated.goal,
            installed_at=datetime.now(timezone.utc).isoformat(),
            enabled=True,
            actions=validated.actions,
            recommended_preset_ids=validated.recommended_preset_ids,
        )
    except Exception as exc:
        raise ValidationFailure(f"Installed pack conversion failed: {exc}") from exc


def _validate_unique_action_ids(candidate: CandidateActionPack) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for action in candidate.actions:
        if action.action_id in seen:
            duplicates.add(action.action_id)
        seen.add(action.action_id)
    if duplicates:
        duplicate_list = ", ".join(sorted(duplicates))
        raise ValidationFailure(
            "Candidate pack validation failed: action_id values must be unique. "
            f"Duplicate ids: {duplicate_list}"
        )


def _validate_supported_input_modes(candidate: CandidateActionPack) -> None:
    unsupported_actions = [
        action.action_id
        for action in candidate.actions
        if action.input_mode == InputMode.structured_fields
    ]
    if unsupported_actions:
        action_list = ", ".join(sorted(unsupported_actions))
        raise ValidationFailure(
            "Candidate pack validation failed: structured_fields actions are not currently supported "
            f"by the candidate review and execution flow. Unsupported actions: {action_list}"
        )


def _validate_action_prompt_placeholders(candidate: CandidateActionPack) -> None:
    for action in candidate.actions:
        _validate_template_placeholders(action, "system_prompt", action.system_prompt)
        _validate_template_placeholders(action, "user_prompt_template", action.user_prompt_template)


def _validate_template_placeholders(action: ActionDefinition, field_name: str, template: str) -> None:
    invalid_fields = sorted(
        {
            placeholder
            for _, placeholder, _, _ in _PROMPT_FORMATTER.parse(template)
            if placeholder and placeholder not in _ALLOWED_PROMPT_PLACEHOLDERS
        }
    )
    if invalid_fields:
        invalid_list = ", ".join(invalid_fields)
        allowed_list = ", ".join(sorted(_ALLOWED_PROMPT_PLACEHOLDERS))
        raise ValidationFailure(
            "Candidate pack validation failed: "
            f"action '{action.action_id}' uses unsupported placeholders in {field_name}: {invalid_list}. "
            f"Allowed placeholders: {allowed_list}"
        )
