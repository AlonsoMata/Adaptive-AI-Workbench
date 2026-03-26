from __future__ import annotations

from typing import Any

TOP_LEVEL_KEYS = {
    "schema_version",
    "pack_id",
    "goal",
    "title",
    "summary",
    "reasoning",
    "warnings",
    "actions",
}
ACTION_KEYS = {
    "action_id",
    "name",
    "description",
    "kind",
    "enabled",
    "rationale",
    "input_mode",
    "fields",
    "system_prompt",
    "user_prompt_template",
    "default_preset_id",
    "tags",
}
FIELD_KEYS = {"name", "label", "required", "placeholder"}


def repair_candidate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    repaired: dict[str, Any] = {}
    for key, value in payload.items():
        if key not in TOP_LEVEL_KEYS:
            continue
        repaired[key] = _sanitize_value(value, key)

    repaired.setdefault("schema_version", "1.0")
    return repaired


def _sanitize_value(value: Any, key: str | None = None) -> Any:
    if isinstance(value, str):
        normalized = value.strip()
        lowered = normalized.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        return normalized

    if isinstance(value, list):
        if key == "actions":
            return [_sanitize_action(item) for item in value if isinstance(item, dict)]
        if key == "fields":
            return [_sanitize_field(item) for item in value if isinstance(item, dict)]
        return [_sanitize_value(item) for item in value]

    if isinstance(value, dict):
        return {nested_key: _sanitize_value(nested_value) for nested_key, nested_value in value.items()}

    return value


def _sanitize_action(action: dict[str, Any]) -> dict[str, Any]:
    repaired: dict[str, Any] = {}
    for key, value in action.items():
        if key not in ACTION_KEYS:
            continue
        repaired[key] = _sanitize_value(value, key)
    return repaired


def _sanitize_field(field: dict[str, Any]) -> dict[str, Any]:
    repaired: dict[str, Any] = {}
    for key, value in field.items():
        if key not in FIELD_KEYS:
            continue
        repaired[key] = _sanitize_value(value, key)
    return repaired
