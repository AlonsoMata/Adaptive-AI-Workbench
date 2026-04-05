from contextlib import contextmanager
from pathlib import Path
import json
import shutil
from uuid import uuid4

from adaptive_ai_workbench.model.gateway import ModelGateway, TextGenerationRequest, TextGenerationResult
from adaptive_ai_workbench.services.workbench_service import WorkbenchService
from adaptive_ai_workbench.settings import Settings
from adaptive_ai_workbench.ui.controller import AppController
from adaptive_ai_workbench.ui.state import AppState


class QueueGateway(ModelGateway):
    def __init__(self, outputs: list[str], configured: bool = True) -> None:
        self.outputs = list(outputs)
        self.configured = configured
        self.requests: list[TextGenerationRequest] = []

    def is_configured(self) -> bool:
        return self.configured

    def build_text_request(self, system_prompt: str, user_prompt: str) -> TextGenerationRequest:
        return TextGenerationRequest(
            model="gpt-test-model",
            instructions=system_prompt,
            input_text=user_prompt,
        )

    def generate_text(self, system_prompt: str, user_prompt: str) -> TextGenerationResult:
        request = self.build_text_request(system_prompt=system_prompt, user_prompt=user_prompt)
        self.requests.append(request)
        output_text = self.outputs.pop(0) if self.outputs else "Stub output"
        return TextGenerationResult(output_text=output_text, request=request)


def build_candidate_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "pack_id": "generated_meeting_helper",
        "goal": "Help me summarize meeting notes and extract action items",
        "title": "Generated Meeting Helper",
        "summary": "Workflow for summarizing notes, extracting action items, and drafting follow-ups.",
        "reasoning": "The goal is meeting-focused, so the workflow emphasizes summarization, extraction, and follow-up drafting.",
        "warnings": ["Review action items before sharing externally."],
        "recommended_preset_ids": ["professional_email"],
        "actions": [
            {
                "action_id": "summarize_notes",
                "name": "Summarize Notes",
                "description": "Summarize raw meeting notes into a clear digest.",
                "kind": "summarization",
                "enabled": True,
                "rationale": "Meeting notes usually need an overview before deeper extraction.",
                "input_mode": "single_text",
                "fields": [],
                "system_prompt": "You summarize meeting notes with tone={tone}, language={language}, style={output_style}, length={length}.",
                "user_prompt_template": "Goal: {goal_text}\nMeeting notes:\n{input_text}",
                "default_preset_id": "professional_email",
                "tags": ["meeting", "summary"],
            },
            {
                "action_id": "extract_actions",
                "name": "Extract Action Items",
                "description": "Extract owners, due dates, and next steps from meeting notes.",
                "kind": "extraction",
                "enabled": True,
                "rationale": "Action extraction is a direct requirement in the goal.",
                "input_mode": "single_text",
                "fields": [],
                "system_prompt": "You extract action items with tone={tone}, language={language}, style={output_style}, length={length}.",
                "user_prompt_template": "Goal: {goal_text}\nMeeting notes:\n{input_text}",
                "default_preset_id": "professional_email",
                "tags": ["meeting", "actions"],
            }
        ],
    }


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


def test_service_generate_candidate_workflow_builds_request_from_goal_and_presets() -> None:
    with scratch_data_dir() as data_dir:
        gateway = QueueGateway(outputs=[json.dumps(build_candidate_payload())])
        settings = Settings(
            data_dir=data_dir,
            templates_dir=templates_dir(),
            openai_api_key="unused-by-stub",
            openai_model="gpt-test-model",
        )
        service = WorkbenchService(settings, gateway=gateway)

        candidate = service.generate_candidate_workflow(
            "Help me summarize meeting notes and extract action items"
        )

        assert candidate.pack_id == "generated_meeting_helper"
        assert gateway.requests
        generation_request = gateway.requests[0]
        assert "Help me summarize meeting notes and extract action items" in generation_request.input_text
        assert "professional_email" in generation_request.input_text
        assert "strict_code_review" in generation_request.input_text


def test_controller_generate_workflow_gracefully_handles_unconfigured_model() -> None:
    with scratch_data_dir() as data_dir:
        settings = Settings(
            data_dir=data_dir,
            templates_dir=templates_dir(),
            openai_api_key=None,
            openai_model=None,
        )
        service = WorkbenchService(settings)
        controller = AppController(service=service, state=AppState())

        controller.bootstrap()
        controller.handle_generate_workflow("Help me draft and reply to emails")

        assert "Workflow Generation Unavailable" in controller.state.inspector_text
        assert controller.state.candidate_pack is None


def test_controller_generate_and_install_workflow_updates_catalog() -> None:
    with scratch_data_dir() as data_dir:
        gateway = QueueGateway(outputs=[json.dumps(build_candidate_payload())])
        settings = Settings(
            data_dir=data_dir,
            templates_dir=templates_dir(),
            openai_api_key="unused-by-stub",
            openai_model="gpt-test-model",
        )
        service = WorkbenchService(settings, gateway=gateway)
        state = AppState()
        controller = AppController(service=service, state=state)

        controller.bootstrap()
        controller.handle_generate_workflow("Help me summarize meeting notes and extract action items")

        assert state.candidate_pack is not None
        assert "Candidate Workflow" in state.inspector_text
        assert "Generated Meeting Helper" in state.inspector_text

        controller.handle_install_candidate()

        assert state.candidate_pack is None
        assert "generated_meeting_helper" in state.available_packs
        assert state.selected_pack == "generated_meeting_helper"
        assert "Installed Workflow" in state.inspector_text


def test_service_executes_installed_generated_pack_through_existing_runtime() -> None:
    with scratch_data_dir() as data_dir:
        gateway = QueueGateway(outputs=[json.dumps(build_candidate_payload()), "Generated live response."])
        settings = Settings(
            data_dir=data_dir,
            templates_dir=templates_dir(),
            openai_api_key="unused-by-stub",
            openai_model="gpt-test-model",
        )
        service = WorkbenchService(settings, gateway=gateway)

        candidate = service.generate_candidate_workflow(
            "Help me summarize meeting notes and extract action items"
        )
        installed = service.install_candidate_workflow(candidate)
        result = service.execute_action(
            pack_id=installed.pack_id,
            action_id="summarize_notes",
            goal_text="Help me summarize meeting notes and extract action items",
            input_text="Alice will prepare the roadmap draft by Friday. Bob will schedule the customer review.",
            selected_preset_id="professional_email",
        )

        assert any(pack.pack_id == "generated_meeting_helper" for pack in service.list_catalog_packs_detailed())
        assert result["mode"] == "live"
        assert result["output_text"] == "Generated live response."
        assert result["preview"]["pack_id"] == "generated_meeting_helper"


def test_controller_generation_failure_surfaces_invalid_payload() -> None:
    with scratch_data_dir() as data_dir:
        gateway = QueueGateway(outputs=["Not valid JSON"]) 
        settings = Settings(
            data_dir=data_dir,
            templates_dir=templates_dir(),
            openai_api_key="unused-by-stub",
            openai_model="gpt-test-model",
        )
        service = WorkbenchService(settings, gateway=gateway)
        controller = AppController(service=service, state=AppState())

        controller.bootstrap()
        controller.handle_generate_workflow("Help me improve my CV for AI engineering roles")

        assert "Workflow Generation Failed" in controller.state.inspector_text
        assert controller.state.candidate_pack is None


def test_controller_run_action_uses_live_gateway_output() -> None:
    with scratch_data_dir() as data_dir:
        gateway = QueueGateway(outputs=["Live model response for built-in workflow execution."])
        settings = Settings(
            data_dir=data_dir,
            templates_dir=templates_dir(),
            openai_api_key="unused-by-stub",
            openai_model="gpt-test-model",
        )
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

        assert gateway.requests
        assert "Live Execution Result" in state.output_text
        assert "Live model response for built-in workflow execution." in state.output_text
        assert "gpt-test-model" in state.output_text