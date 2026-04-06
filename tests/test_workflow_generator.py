from pathlib import Path

from adaptive_ai_workbench.model.prompt_loader import load_prompt
from adaptive_ai_workbench.planning.workflow_generator import build_candidate_generation_prompt
from adaptive_ai_workbench.persistence.preset_store import PresetStore


def templates_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "src" / "adaptive_ai_workbench" / "templates"


def test_generation_prompt_mentions_all_required_action_fields() -> None:
    presets = PresetStore(templates_dir()).list_builtin()
    prompt = build_candidate_generation_prompt(
        goal_text="Create a workflow pack that helps generate personalized diet plans for weight gain, weight loss, sports performance, and general health.",
        system_prompt="system prompt placeholder",
        presets=presets,
    )

    required_fields = [
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
    for field_name in required_fields:
        assert f"- {field_name}" in prompt.user_prompt

    assert "Do not return partial, conceptual, or placeholder action objects." in prompt.user_prompt
    assert "Return JSON only." in prompt.user_prompt
    assert "Generated actions must be directly usable by the current dispatcher/runtime model." in prompt.user_prompt


def test_generation_prompt_nudges_research_goals_toward_direct_outputs() -> None:
    presets = PresetStore(templates_dir()).list_builtin()
    prompt = build_candidate_generation_prompt(
        goal_text="Create a workflow pack that helps investigate a concrete topic, provide useful insights, suggest related concepts to explore, and recommend valuable sources.",
        system_prompt="system prompt placeholder",
        presets=presets,
    )

    assert "Prefer execution-oriented actions that help the user get a useful result immediately." in prompt.user_prompt
    assert "For investigation, research, exploration, or discovery goals, prefer direct actions such as investigate_topic, summarize_findings, extract_key_insights, suggest_related_concepts, and recommend_sources." in prompt.user_prompt
    assert "Avoid meta actions such as frame_topic_investigation, create_research_brief, or plan_research_workflow unless the goal explicitly asks for planning the research process itself." in prompt.user_prompt


def test_generation_prompt_template_includes_schema_complete_example() -> None:
    system_prompt = load_prompt("generate_action_pack", templates_dir())

    assert '"pack_id": "client_email_workflow"' in system_prompt
    assert '"action_id": "draft_email"' in system_prompt
    assert '"system_prompt": "You are an expert email assistant.' in system_prompt
    assert '"user_prompt_template": "Goal: {goal_text}' in system_prompt
    assert "Allowed placeholders only: {goal_text}, {input_text}, {tone}, {language}, {output_style}, {length}, {format}, {strictness}, {instruction_text}." in system_prompt
    assert "Complete ActionDefinition objects only." in system_prompt


def test_generation_prompt_template_discourages_meta_research_packs() -> None:
    system_prompt = load_prompt("generate_action_pack", templates_dir())

    assert "Prefer actions that solve the user's task directly." in system_prompt
    assert "For investigation, research, exploration, or discovery goals, prefer direct actions" in system_prompt
    assert "Avoid meta actions such as frame_topic_investigation, create_research_brief, or plan_research_workflow" in system_prompt


def test_generation_prompt_forbids_markdown_fences_and_rule_restatement() -> None:
    presets = PresetStore(templates_dir()).list_builtin()
    prompt = build_candidate_generation_prompt(
        goal_text="Help me create the best competitive pokemon team",
        system_prompt="system prompt placeholder",
        presets=presets,
    )

    assert "Do not use markdown fences." in prompt.user_prompt
    assert "Do not restate the rules, placeholders, or schema in the response." in prompt.user_prompt
    assert "Treat recommended_preset_ids and default_preset_id as universal response-profile ids" in prompt.user_prompt

    system_prompt = load_prompt("generate_action_pack", templates_dir())
    assert "Do not wrap the JSON in ```json fences." in system_prompt
    assert "Do not restate the rules, allowed placeholders, or schema before the JSON object." in system_prompt
    assert "Prefer universal response-profile ids such as professional_clear, concise_structured, analytical_review, formal_report, friendly_polished, or clear_spanish." in system_prompt
