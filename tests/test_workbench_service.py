from contextlib import contextmanager
from pathlib import Path
import shutil
import tempfile

from adaptive_ai_workbench.services.workbench_service import WorkbenchService
from adaptive_ai_workbench.settings import Settings
from adaptive_ai_workbench.ui.controller import AppController
from adaptive_ai_workbench.ui.state import AppState


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


def test_service_preview_builtin_action_uses_goal_input_and_selected_preset() -> None:
    with scratch_dir() as data_dir:
        settings = Settings(
            data_dir=data_dir,
            templates_dir=templates_dir(),
            openai_api_key=None,
            openai_model=None,
        )
        service = WorkbenchService(settings)

        preview = service.preview_builtin_action(
            pack_id="email_assistant",
            action_id="draft_email",
            goal_text="Help me write a clear client follow-up",
            input_text="Need to confirm next Tuesday and share the revised timeline.",
            selected_preset_id="professional_email",
        )

        assert preview["pack_name"] == "Email Assistant"
        assert preview["action_name"] == "Draft Email"
        assert preview["preset_id"] == "professional_email"
        assert "Help me write a clear client follow-up" in str(preview["user_prompt"])
        assert "Need to confirm next Tuesday" in str(preview["user_prompt"])


def test_controller_selection_flow_populates_inspector_and_output() -> None:
    with scratch_dir() as data_dir:
        settings = Settings(
            data_dir=data_dir,
            templates_dir=templates_dir(),
            openai_api_key=None,
            openai_model=None,
        )
        service = WorkbenchService(settings)
        state = AppState()
        controller = AppController(service=service, state=state)

        controller.bootstrap()
        controller.handle_pack_selected("email_assistant")

        assert "Pack Name: Email Assistant" in state.inspector_text
        assert "draft_email" in state.available_actions
        assert state.selected_preset == "professional_email"

        controller.handle_action_selected(
            action_id="draft_email",
            goal_text="Write a polished client update",
            input_text="We fixed the issue and can deploy tomorrow morning.",
        )

        assert "Action Name: Draft Email" in state.inspector_text
        assert "Prompt Preview" in state.inspector_text

        controller.handle_run_action(
            goal_text="Write a polished client update",
            input_text="We fixed the issue and can deploy tomorrow morning.",
        )

        assert "Execution Preview" in state.output_text
        assert "Email Assistant" in state.output_text
        assert "Draft Email" in state.output_text
