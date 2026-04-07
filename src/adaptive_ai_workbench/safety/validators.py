from __future__ import annotations

import re
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
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_META_ACTION_PATTERN = re.compile(
    r"\b(plan|planning|roadmap|outline|brief|strategy|strategic|brainstorm|frame|framing|workflow|meta|prompt)\b"
)
_PLANNING_GOAL_PATTERN = re.compile(
    r"\b(plan|planning|roadmap|outline|brief|strategy|strategic|brainstorm|approach|framework|process)\b"
)
_STOPWORDS = {
    "a",
    "an",
    "and",
    "assistant",
    "best",
    "build",
    "clear",
    "create",
    "for",
    "from",
    "generate",
    "help",
    "improve",
    "into",
    "me",
    "my",
    "of",
    "on",
    "pack",
    "the",
    "to",
    "use",
    "with",
    "workflow",
    "write",
    "your",
}
_INTENT_ALIASES = {
    "adapt": "rewrite",
    "analyze": "review",
    "brainstorm": "plan",
    "compose": "generate",
    "craft": "generate",
    "create": "generate",
    "design": "plan",
    "develop": "generate",
    "draft": "generate",
    "edit": "rewrite",
    "evaluate": "review",
    "extract": "extract",
    "frame": "plan",
    "generate": "generate",
    "identify": "extract",
    "improve": "rewrite",
    "investigate": "investigate",
    "localize": "translate",
    "outline": "plan",
    "plan": "plan",
    "recommend": "recommend",
    "reply": "generate",
    "research": "investigate",
    "revise": "rewrite",
    "rewrite": "rewrite",
    "strategize": "plan",
    "suggest": "recommend",
    "summarize": "summarize",
    "tailor": "rewrite",
    "translate": "translate",
    "write": "generate",
}


def validate_candidate_pack(candidate: CandidateActionPack) -> CandidateActionPack:
    try:
        validated = CandidateActionPack.model_validate(candidate.model_dump())
    except Exception as exc:
        raise ValidationFailure(f"Candidate pack validation failed: {exc}") from exc
    _validate_unique_action_ids(validated)
    _validate_supported_input_modes(validated)
    _validate_action_prompt_placeholders(validated)
    return validated


def find_generated_candidate_quality_issues(
    candidate: CandidateActionPack,
    goal_text: str,
) -> list[str]:
    issues: list[str] = []
    meta_actions = _find_meta_actions(candidate)
    if meta_actions and not _goal_explicitly_requests_planning(goal_text):
        if len(meta_actions) == len(candidate.actions) or len(meta_actions) > len(candidate.actions) / 2:
            issues.append(
                "The pack is overly meta or planning-heavy for this goal. Replace planning-only actions with direct "
                "task-solving actions. Meta actions: "
                + ", ".join(meta_actions)
            )

    detected_intents = {_primary_intent(action) for action in candidate.actions}
    if len(candidate.actions) >= 3 and len(detected_intents) < 2:
        issues.append(
            "The pack's actions are weakly differentiated. Use meaningfully different action intents instead of "
            "repeating the same action pattern."
        )

    goal_keywords = _keyword_set(goal_text)
    action_keywords = _keyword_set(
        " ".join(
            " ".join(
                [
                    action.action_id,
                    action.name,
                    action.description,
                    action.rationale,
                    " ".join(action.tags),
                ]
            )
            for action in candidate.actions
        )
    )
    if goal_keywords and not goal_keywords.intersection(action_keywords):
        issues.append(
            "The pack's actions do not clearly align with the requested outcome. Use action names and descriptions "
            "that reflect the user's goal rather than a generic or unrelated workflow."
        )

    return issues


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


def _find_meta_actions(candidate: CandidateActionPack) -> list[str]:
    meta_actions: list[str] = []
    for action in candidate.actions:
        action_text = " ".join([action.action_id, action.name, action.description, action.rationale, " ".join(action.tags)])
        if _META_ACTION_PATTERN.search(action_text.casefold()):
            meta_actions.append(action.action_id)
    return meta_actions


def _goal_explicitly_requests_planning(goal_text: str) -> bool:
    return _PLANNING_GOAL_PATTERN.search(goal_text.casefold()) is not None


def _primary_intent(action: ActionDefinition) -> str:
    for token in _tokenize(" ".join([action.action_id, action.name])):
        normalized_intent = _INTENT_ALIASES.get(token)
        if normalized_intent is not None:
            return normalized_intent
        if token in _STOPWORDS:
            continue
        return token
    return "generic"


def _keyword_set(text: str) -> set[str]:
    return {token for token in _tokenize(text) if token not in _STOPWORDS}


def _tokenize(text: str) -> list[str]:
    return [_normalize_token(token) for token in _TOKEN_PATTERN.findall(text.casefold())]


def _normalize_token(token: str) -> str:
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("s") and len(token) > 4:
        return token[:-1]
    return token
