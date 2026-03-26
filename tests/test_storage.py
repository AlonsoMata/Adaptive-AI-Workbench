from contextlib import contextmanager
from pathlib import Path
import shutil
import tempfile

from adaptive_ai_workbench.domain.models import WorkbenchProject
from adaptive_ai_workbench.persistence.action_pack_store import ActionPackStore
from adaptive_ai_workbench.persistence.preset_store import PresetStore
from adaptive_ai_workbench.persistence.project_store import ProjectStore


def templates_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "src" / "adaptive_ai_workbench" / "templates"


@contextmanager
def scratch_dir() -> Path:
    scratch_root = Path(__file__).resolve().parents[1] / ".scratch_runtime"
    scratch_root.mkdir(parents=True, exist_ok=True)
    path = Path(tempfile.mkdtemp(prefix="aawb_test_", dir=scratch_root))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
        if scratch_root.exists() and not any(scratch_root.iterdir()):
            scratch_root.rmdir()


def test_action_pack_store_roundtrip_and_builtin_loading() -> None:
    with scratch_dir() as data_dir:
        store = ActionPackStore(data_dir=data_dir, templates_dir=templates_dir())
        builtin = store.load_builtin_template("email_assistant")
        save_path = store.save_installed(builtin)
        reloaded = store.load_installed("email_assistant")

        assert save_path.exists()
        assert reloaded.pack_id == "email_assistant"
        assert len(reloaded.actions) >= 2


def test_preset_store_loads_builtin_presets() -> None:
    store = PresetStore(templates_dir())
    presets = store.list_builtin()

    assert {preset.preset_id for preset in presets} >= {
        "professional_email",
        "concise_cv",
        "strict_code_review",
    }


def test_project_store_roundtrip() -> None:
    with scratch_dir() as data_dir:
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
