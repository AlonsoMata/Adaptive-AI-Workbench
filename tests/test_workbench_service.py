from contextlib import contextmanager
from pathlib import Path
import shutil
from uuid import uuid4

from adaptive_ai_workbench.model.gateway import ModelGateway, TextGenerationRequest, TextGenerationResult
from adaptive_ai_workbench.services.workbench_service import WorkbenchService
from adaptive_ai_workbench.settings import Settings
from adaptive_ai_workbench.ui.controller import AppController
from adaptive_ai_workbench.ui.state import AppState


class StubLiveGateway(ModelGateway):
    def __init__(self) -> None:
        self.last_request: TextGenerationRequest | None = None

    def is_configured(self) -> bool:
        return True

    def build_text_request(self, system_prompt: str, user_prompt: str) -> TextGenerationRequest:
        return TextGenerationRequest(
            model="gpt-test-model",
            instructions=system_prompt,
            input_text=user_prompt,
        )

    def generate_text(self, system_prompt: str, user_prompt: str) -> TextGenerationResult:
        request = self.build_text_request(system_prompt=system_prompt, user_prompt=user_prompt)
        self.last_request = request
        return TextGenerationResult(
            output_text="Live model response for built-in workflow execution.",
            request=request,
        )


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


def test_service_preview_builtin_action_uses_goal_input_and_selected_preset() -> None:
    with scratch_data_dir() as data_dir:
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


def test_service_execute_builtin_action_gracefully_handles_unconfigured_model() -> None:
    with scratch_data_dir() as data_dir:
        settings = Settings(
            data_dir=data_dir,
            templates_dir=templates_dir(),
            openai_api_key=None,
            openai_model=None,
        )
        service = WorkbenchService(settings)

        result = service.execute_builtin_action(
            pack_id="email_assistant",
            action_id="draft_email",
            goal_text="Write a polished client update",
            input_text="We fixed the issue and can deploy tomorrow morning.",
            selected_preset_id="professional_email",
        )

        assert result["mode"] == "unavailable"
        assert "OPENAI_API_KEY" in str(result["message"])
        assert result["preview"]["action_name"] == "Draft Email"


def test_controller_selection_flow_populates_inspector_and_unavailable_output() -> None:
    with scratch_data_dir() as data_dir:
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

        assert "Live Execution Unavailable" in state.output_text
        assert "Email Assistant" in state.output_text
        assert "Draft Email" in state.output_text


def test_controller_run_action_uses_live_gateway_output() -> None:
    with scratch_data_dir() as data_dir:
        settings = Settings(
            data_dir=data_dir,
            templates_dir=templates_dir(),
            openai_api_key="unused-by-stub",
            openai_model="gpt-test-model",
        )
        gateway = StubLiveGateway()
        service = WorkbenchService(settings, gateway=gateway)
        state = AppState()
        controller = AppController(service=service, state=state)

        controller.bootstrap()
        controller.handle_pack_selected("email_assistant")
        controller.handle_action_selected(
            action_id="draft_email",
            goal_text="Write a polished client update",
            input_text="We fixed the issue and can deploy tomorrow morning.",
        )
        controller.handle_run_action(
            goal_text="Write a polished client update",
            input_text="We fixed the issue and can deploy tomorrow morning.",
        )

        assert gateway.last_request is not None
        assert "Live Execution Result" in state.output_text
        assert "Live model response for built-in workflow execution." in state.output_text
        assert "gpt-test-model" in state.output_text