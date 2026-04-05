from __future__ import annotations

from dataclasses import dataclass

from adaptive_ai_workbench.domain.enums import ActionKind
from adaptive_ai_workbench.domain.models import PresetDefinition


@dataclass(slots=True)
class WorkflowGenerationPrompt:
    system_prompt: str
    user_prompt: str


def describe_generation_scope() -> str:
    return (
        "Generate validated workflow packs from a user goal using approved action "
        "types and reviewable prompt templates."
    )


def build_candidate_generation_prompt(
    goal_text: str,
    system_prompt: str,
    presets: list[PresetDefinition],
) -> WorkflowGenerationPrompt:
    approved_kinds = "\n".join(f"- {kind.value}" for kind in ActionKind)
    preset_lines = "\n".join(
        (
            f"- {preset.preset_id}: {preset.description} "
            f"(tone={preset.tone}, language={preset.language}, "
            f"style={preset.output_style}, length={preset.length})"
        )
        for preset in presets
    )
    allowed_preset_ids = ", ".join(preset.preset_id for preset in presets) or "none"

    user_prompt = (
        f"User goal:\n{goal_text}\n\n"
        "Return one CandidateActionPack JSON object only.\n\n"
        "Required top-level keys:\n"
        "- schema_version\n"
        "- pack_id\n"
        "- goal\n"
        "- title\n"
        "- summary\n"
        "- reasoning\n"
        "- warnings\n"
        "- recommended_preset_ids\n"
        "- actions\n\n"
        "Workflow rules:\n"
        "- Create 2 to 4 actions.\n"
        "- Use only approved action kinds.\n"
        "- recommended_preset_ids must use only these preset ids: "
        f"{allowed_preset_ids}.\n"
        "- Each action default_preset_id must be null or one of those preset ids.\n"
        "- Use only Python str.format placeholders in prompts: "
        "{goal_text}, {input_text}, {tone}, {language}, {output_style}, {length}, {instruction_text}.\n"
        "- Keep the workflow practical, reusable, and safe.\n"
        "- Do not mention tools, shell commands, plugins, autonomous steps, or code execution.\n"
        "- Warnings should be concise and optional.\n\n"
        f"Approved action kinds:\n{approved_kinds}\n\n"
        f"Available presets:\n{preset_lines}\n"
    )
    return WorkflowGenerationPrompt(system_prompt=system_prompt, user_prompt=user_prompt)