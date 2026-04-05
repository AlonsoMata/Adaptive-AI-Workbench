from contextlib import contextmanager
from pathlib import Path
import json
import shutil
from uuid import uuid4

from adaptive_ai_workbench.domain.models import ActionDefinition, CandidateActionPack, WorkbenchProject
from adaptive_ai_workbench.persistence.action_pack_store import ActionPackStore
from adaptive_ai_workbench.persistence.preset_store import PresetStore
from adaptive_ai_workbench.persistence.project_store import ProjectStore


def templates_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "src" / "adaptive_ai_workbench" / "templates"


@contextmanager
def scratch_data_dir() -> Path:
    scratch_root = Path(__file__).resolve().parents[1] / ".scratch_runtime"
    scratch_root.mkdir(parents=True, exist_ok=True)
    path = scratch_root / f"aawb_test_{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
        if scratch_root.exists() and not any(scratch_root.iterdir()):
            scratch_root.rmdir()


def build_candidate() -> CandidateActionPack:
    return CandidateActionPack(
        pack_id="generated_email_helper",
        goal="Help me draft and rewrite professional emails",
        title="Generated Email Helper",
        summary="Generated workflow for drafting and improving professional emails.",
        reasoning="The goal is centered on email drafting and rewriting.",
        recommended_preset_ids=["professional_email"],
        actions=[
            ActionDefinition(
                action_id="draft_email",
                name="Draft Email",
                description="Create a polished email draft from notes.",
                kind="template_fill",
                enabled=True,
                rationale="Drafting is central to the requested workflow.",
                input_mode="single_text",
                fields=[],
                system_prompt="You are an expert email assistant. Write with tone={tone}, language={language}, style={output_style}, length={length}.",
                user_prompt_template="Goal: {goal_text}\nInput:\n{input_text}",
                default_preset_id="professional_email",
                tags=["email"],
            )
        ],
    )


def test_action_pack_store_roundtrip_and_builtin_loading() -> None:
    with scratch_data_dir() as data_dir:
        store = ActionPackStore(data_dir=data_dir, templates_dir=templates_dir())
        builtin = store.load_builtin_template("email_assistant")
        save_path = store.save_installed(builtin)
        reloaded = store.load_installed("email_assistant")

        assert save_path.exists()
        assert reloaded.pack_id == "email_assistant"
        assert len(reloaded.actions) >= 2


def test_action_pack_store_installs_generated_candidate_and_reloads_it() -> None:
    with scratch_data_dir() as data_dir:
        store = ActionPackStore(data_dir=data_dir, templates_dir=templates_dir())
        installed = store.install_candidate(build_candidate())
        reloaded = store.load_installed(installed.pack_id)

        assert installed.source.value == "generated"
        assert reloaded.pack_id == "generated_email_helper"
        assert reloaded.recommended_preset_ids == ["professional_email"]


def test_preset_store_loads_builtin_presets() -> None:
    store = PresetStore(templates_dir())
    presets = store.list_builtin()

    assert {preset.preset_id for preset in presets} >= {
        "professional_email",
        "concise_cv",
        "strict_code_review",
    }


def test_project_store_roundtrip() -> None:
    with scratch_data_dir() as data_dir:
        store = ProjectStore(data_dir=data_dir)
        project = WorkbenchProject(
            project_id="demo_project",
            goal_text="Help me improve emails",
            input_text="Initial content",
            selected_pack_id="email_assistant",
            selected_preset_id="professional_email",
        )

        path = store.save_project(project)
        loaded = store.load_project("demo_project")

        assert path.exists()
        assert loaded.selected_pack_id == "email_assistant"