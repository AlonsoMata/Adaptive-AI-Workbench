from __future__ import annotations

import json

from pydantic import ValidationError

from adaptive_ai_workbench.domain.errors import ModelOutputError
from adaptive_ai_workbench.domain.models import CandidateActionPack
from adaptive_ai_workbench.safety.repair import repair_candidate_payload


def extract_first_json_object(raw_text: str) -> str:
    start = raw_text.find("{")
    if start == -1:
        raise ModelOutputError("No JSON object found in model output.")

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

    raise ModelOutputError("Could not extract a balanced JSON object from model output.")


def parse_candidate_action_pack(raw_text: str) -> CandidateActionPack:
    payload = _parse_json_payload(raw_text)
    repaired_payload = repair_candidate_payload(payload)
    try:
        return CandidateActionPack.model_validate(repaired_payload)
    except ValidationError as exc:
        raise ModelOutputError(_build_candidate_validation_message(exc)) from exc
    except Exception as exc:
        raise ModelOutputError(f"Candidate action pack validation failed: {exc}") from exc


def _parse_json_payload(raw_text: str) -> dict[str, object]:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        extracted = extract_first_json_object(raw_text)
        try:
            payload = json.loads(extracted)
        except json.JSONDecodeError as exc:
            raise ModelOutputError("Unable to parse extracted JSON object.") from exc

    if not isinstance(payload, dict):
        raise ModelOutputError("Model output must be a JSON object.")
    return payload


def _build_candidate_validation_message(error: ValidationError) -> str:
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
        return detailed_message

    missing_list = ", ".join(missing_action_fields)
    return (
        "Generated workflow is missing required action fields. "
        f"Missing fields include: {missing_list}.\n"
        f"{detailed_message}"
    )