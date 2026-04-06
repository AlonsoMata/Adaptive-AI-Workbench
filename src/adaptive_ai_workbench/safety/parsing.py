from __future__ import annotations

import json
import re

from pydantic import ValidationError

from adaptive_ai_workbench.domain.errors import ModelOutputError
from adaptive_ai_workbench.domain.models import CandidateActionPack
from adaptive_ai_workbench.safety.repair import repair_candidate_payload

_CODE_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)
_MAX_SNIPPET_LENGTH = 280
_REQUIRED_TOP_LEVEL_FIELDS = {
    "pack_id",
    "goal",
    "title",
    "summary",
    "reasoning",
    "actions",
}
_KNOWN_TOP_LEVEL_FIELDS = _REQUIRED_TOP_LEVEL_FIELDS | {"schema_version", "warnings", "recommended_preset_ids"}
_CANDIDATE_SIGNAL_SCAN_LIMIT = 5000
_TRUNCATION_SIGNAL_THRESHOLD = 3


def extract_first_json_object(raw_text: str) -> str:
    normalized_text = _strip_code_fences(raw_text).strip()
    starts = [index for index, char in enumerate(normalized_text) if char == "{"]
    if not starts:
        raise ModelOutputError(_with_output_snippet("No JSON object found in model output.", raw_text))

    saw_balanced_candidate = False
    best_candidate_text: str | None = None
    best_candidate_score = -1
    best_candidate_completeness = -1
    best_unbalanced_signal = -1

    for start in starts:
        try:
            candidate_text = _extract_balanced_object_from_start(normalized_text, start)
        except ModelOutputError:
            best_unbalanced_signal = max(best_unbalanced_signal, _candidate_field_signal(normalized_text, start))
            continue

        saw_balanced_candidate = True
        try:
            parsed_candidate = json.loads(candidate_text)
        except json.JSONDecodeError:
            continue

        if not isinstance(parsed_candidate, dict):
            continue

        score = len(_KNOWN_TOP_LEVEL_FIELDS.intersection(parsed_candidate.keys()))
        completeness = len(_REQUIRED_TOP_LEVEL_FIELDS.intersection(parsed_candidate.keys()))
        if completeness == len(_REQUIRED_TOP_LEVEL_FIELDS):
            return candidate_text

        if completeness > best_candidate_completeness or (
            completeness == best_candidate_completeness and score > best_candidate_score
        ):
            best_candidate_text = candidate_text
            best_candidate_score = score
            best_candidate_completeness = completeness

    if best_unbalanced_signal >= _TRUNCATION_SIGNAL_THRESHOLD and best_candidate_completeness < best_unbalanced_signal:
        raise ModelOutputError(
            _with_output_snippet(
                "The model output appears to contain an incomplete candidate workflow JSON object. "
                "The response may have been truncated before the full pack was closed.",
                raw_text,
            )
        )

    if best_candidate_text is not None:
        return best_candidate_text

    if saw_balanced_candidate:
        raise ModelOutputError(
            _with_output_snippet("Could not find a valid JSON object in model output.", raw_text)
        )

    raise ModelOutputError(
        _with_output_snippet("Could not extract a balanced JSON object from model output.", raw_text)
    )


def parse_candidate_action_pack(raw_text: str) -> CandidateActionPack:
    payload = _parse_json_payload(raw_text)
    repaired_payload = repair_candidate_payload(payload)
    try:
        return CandidateActionPack.model_validate(repaired_payload)
    except ValidationError as exc:
        raise ModelOutputError(_build_candidate_validation_message(exc, raw_text)) from exc
    except Exception as exc:
        raise ModelOutputError(
            _with_output_snippet(f"Candidate action pack validation failed: {exc}", raw_text)
        ) from exc


def _parse_json_payload(raw_text: str) -> dict[str, object]:
    normalized_text = _strip_code_fences(raw_text).strip()
    try:
        payload = json.loads(normalized_text)
    except json.JSONDecodeError:
        extracted = extract_first_json_object(normalized_text)
        try:
            payload = json.loads(extracted)
        except json.JSONDecodeError as exc:
            raise ModelOutputError(
                _with_output_snippet("Unable to parse extracted JSON object.", raw_text)
            ) from exc

    if not isinstance(payload, dict):
        raise ModelOutputError(_with_output_snippet("Model output must be a JSON object.", raw_text))
    return payload


def _extract_balanced_object_from_start(raw_text: str, start: int) -> str:
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(raw_text)):
        char = raw_text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return raw_text[start : index + 1]

    raise ModelOutputError("Unbalanced JSON object candidate.")


def _candidate_field_signal(raw_text: str, start: int) -> int:
    window = raw_text[start : start + _CANDIDATE_SIGNAL_SCAN_LIMIT]
    return sum(1 for field_name in _REQUIRED_TOP_LEVEL_FIELDS if f'"{field_name}"' in window)


def _strip_code_fences(raw_text: str) -> str:
    stripped = raw_text.strip()
    match = _CODE_FENCE_PATTERN.match(stripped)
    if match:
        return match.group(1).strip()
    return raw_text


def _build_candidate_validation_message(error: ValidationError, raw_text: str) -> str:
    missing_top_level_fields = sorted(
        {
            str(details["loc"][-1])
            for details in error.errors()
            if details.get("type") == "missing"
            and isinstance(details.get("loc"), tuple)
            and len(details["loc"]) == 1
        }
    )
    if missing_top_level_fields:
        missing_list = ", ".join(missing_top_level_fields)
        return _with_output_snippet(
            "Generated workflow is missing required top-level fields. "
            f"Missing fields include: {missing_list}.\n"
            f"Candidate action pack validation failed: {error}",
            raw_text,
        )

    missing_action_fields = sorted(
        {
            str(details["loc"][-1])
            for details in error.errors()
            if details.get("type") == "missing"
            and isinstance(details.get("loc"), tuple)
            and len(details["loc"]) >= 3
            and details["loc"][0] == "actions"
        }
    )
    detailed_message = f"Candidate action pack validation failed: {error}"
    if not missing_action_fields:
        return _with_output_snippet(detailed_message, raw_text)

    missing_list = ", ".join(missing_action_fields)
    return _with_output_snippet(
        "Generated workflow is missing required action fields. "
        f"Missing fields include: {missing_list}.\n"
        f"{detailed_message}",
        raw_text,
    )


def _with_output_snippet(message: str, raw_text: str) -> str:
    return f"{message}\nModel output snippet: {_build_output_snippet(raw_text)}"


def _build_output_snippet(raw_text: str) -> str:
    collapsed = " ".join(raw_text.split())
    if not collapsed:
        return "<empty>"
    if len(collapsed) <= _MAX_SNIPPET_LENGTH:
        return collapsed
    return collapsed[: _MAX_SNIPPET_LENGTH - 3] + "..."
