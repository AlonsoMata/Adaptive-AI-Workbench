from __future__ import annotations

from dataclasses import dataclass

from adaptive_ai_workbench.domain.enums import ActionKind
from adaptive_ai_workbench.domain.models import PresetDefinition

REQUIRED_ACTION_FIELDS = [
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
]

ALLOWED_PLACEHOLDERS = [
    "{goal_text}",
    "{input_text}",
    "{tone}",
    "{language}",
    "{output_style}",
    "{length}",
    "{instruction_text}",
]


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
    required_action_fields = "\n".join(f"- {field_name}" for field_name in REQUIRED_ACTION_FIELDS)
    preset_lines = "\n".join(
        (
            f"- {preset.preset_id}: {preset.description} "
            f"(tone={preset.tone}, language={preset.language}, "
            f"style={preset.output_style}, length={preset.length})"
        )
        for preset in presets
    )
    allowed_preset_ids = ", ".join(preset.preset_id for preset in presets) or "none"
    allowed_placeholders = ", ".join(ALLOWED_PLACEHOLDERS)

    user_prompt = (
        f"User goal:\n{goal_text}\n\n"
        "Return one CandidateActionPack JSON object only.\n"
        "Return JSON only. Do not include prose before or after the JSON object.\n\n"
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
        "Every item in actions must be a complete ActionDefinition object.\n"
        "Do not return partial, conceptual, or placeholder action objects.\n"
        "Required keys for every action object:\n"
        f"{required_action_fields}\n\n"
        "Workflow rules:\n"
        "- Create 2 to 4 actions.\n"
        "- Use only approved action kinds.\n"
        "- recommended_preset_ids must use only these preset ids: "
        f"{allowed_preset_ids}.\n"
        "- Each action default_preset_id must be null or one of those preset ids.\n"
        "- Use only these Python str.format placeholders in prompts: "
        f"{allowed_placeholders}.\n"
        "- Generated actions must be directly usable by the current dispatcher/runtime model.\n"
        "- Prefer execution-oriented actions that help the user get a useful result immediately.\n"
        "- Do not make the pack primarily about planning, framing, or designing the workflow unless the user explicitly asks for planning.\n"
        "- For investigation, research, exploration, or discovery goals, prefer direct actions such as investigate_topic, summarize_findings, extract_key_insights, suggest_related_concepts, and recommend_sources.\n"
        "- Avoid meta actions such as frame_topic_investigation, create_research_brief, or plan_research_workflow unless the goal explicitly asks for planning the research process itself.\n"
        "- Keep the workflow practical, reusable, and safe.\n"
        "- Do not mention tools, shell commands, plugins, autonomous steps, or code execution.\n"
        "- Warnings should be concise and optional. Use [] if none.\n"
        "- fields and tags must always be present. Use [] if empty.\n"
        "- Never omit action_id, name, system_prompt, or user_prompt_template.\n\n"
        f"Approved action kinds:\n{approved_kinds}\n\n"
        f"Available presets:\n{preset_lines}\n"
    )
    return WorkflowGenerationPrompt(system_prompt=system_prompt, user_prompt=user_prompt)