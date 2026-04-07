from contextlib import contextmanager
from pathlib import Path
import json
import shutil
from uuid import uuid4

import pytest

from adaptive_ai_workbench.domain.errors import ValidationFailure
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

    def build_text_request(self, system_prompt: str, user_prompt: str, *, max_output_tokens: int | None = None) -> TextGenerationRequest:
        return TextGenerationRequest(
            model="gpt-test-model",
            instructions=system_prompt,
            input_text=user_prompt,
            max_output_tokens=max_output_tokens or 900,
        )

    def generate_text(self, system_prompt: str, user_prompt: str, *, max_output_tokens: int | None = None) -> TextGenerationResult:
        request = self.build_text_request(system_prompt=system_prompt, user_prompt=user_prompt, max_output_tokens=max_output_tokens)
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
        "recommended_preset_ids": ["concise_structured"],
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
                "system_prompt": "You summarize meeting notes with tone={tone}, language={language}, style={output_style}, length={length}, format={format}, and strictness={strictness}.",
                "user_prompt_template": "Goal: {goal_text}\nMeeting notes:\n{input_text}",
                "default_preset_id": "concise_structured",
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
                "system_prompt": "You extract action items with tone={tone}, language={language}, style={output_style}, length={length}, format={format}, and strictness={strictness}.",
                "user_prompt_template": "Goal: {goal_text}\nMeeting notes:\n{input_text}",
                "default_preset_id": "analytical_review",
                "tags": ["meeting", "actions"],
            }
        ],
    }


def build_meta_candidate_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "pack_id": "meeting_workflow_planner",
        "goal": "Help me summarize meeting notes and extract action items",
        "title": "Meeting Workflow Planner",
        "summary": "Workflow for planning how to handle meeting notes before doing the actual work.",
        "reasoning": "The pack focuses on planning the workflow before generating outputs.",
        "warnings": [],
        "recommended_preset_ids": ["concise_structured"],
        "actions": [
            {
                "action_id": "plan_meeting_workflow",
                "name": "Plan Meeting Workflow",
                "description": "Plan how the meeting notes should be processed before producing any output.",
                "kind": "prompt_transform",
                "enabled": True,
                "rationale": "Planning the workflow comes first.",
                "input_mode": "single_text",
                "fields": [],
                "system_prompt": "You plan workflows with tone={tone}, language={language}, style={output_style}, length={length}, format={format}, and strictness={strictness}.",
                "user_prompt_template": "Goal: {goal_text}\nMeeting notes:\n{input_text}",
                "default_preset_id": "concise_structured",
                "tags": ["planning", "workflow"],
            },
            {
                "action_id": "outline_meeting_strategy",
                "name": "Outline Meeting Strategy",
                "description": "Create a strategy outline for how the meeting request should be approached.",
                "kind": "prompt_transform",
                "enabled": True,
                "rationale": "A strategy outline should be produced before solving the task.",
                "input_mode": "single_text",
                "fields": [],
                "system_prompt": "You outline strategies with tone={tone}, language={language}, style={output_style}, length={length}, format={format}, and strictness={strictness}.",
                "user_prompt_template": "Goal: {goal_text}\nMeeting notes:\n{input_text}",
                "default_preset_id": "concise_structured",
                "tags": ["strategy", "planning"],
            },
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


def build_controller(outputs: list[str], configured: bool = True) -> tuple[WorkbenchService, AppState, AppController]:
    data_dir_context = scratch_data_dir()
    data_dir = data_dir_context.__enter__()
    gateway = QueueGateway(outputs=outputs, configured=configured)
    settings = Settings(
        data_dir=data_dir,
        templates_dir=templates_dir(),
        openai_api_key="unused-by-stub" if configured else None,
        openai_model="gpt-test-model" if configured else None,
    )
    service = WorkbenchService(settings, gateway=gateway)
    state = AppState()
    controller = AppController(service=service, state=state)
    controller._test_context = data_dir_context  # type: ignore[attr-defined]
    return service, state, controller


def cleanup_controller(controller: AppController) -> None:
    controller._test_context.__exit__(None, None, None)  # type: ignore[attr-defined]


def test_service_preview_builtin_action_uses_goal_input_and_selected_controls() -> None:
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
            selected_controls=service.build_response_controls(
                tone="friendly",
                length="medium",
                language="en",
                output_style="polished",
                format="email",
                strictness="low",
            ),
        )

        assert preview["pack_name"] == "Email Assistant"
        assert preview["action_name"] == "Draft Email"
        assert preview["tone"] == "friendly"
        assert preview["format"] == "email"
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
            selected_controls=service.build_response_controls(
                tone="professional",
                length="medium",
                language="en",
                output_style="clear",
                format="email",
                strictness="medium",
            ),
        )

        assert result["mode"] == "unavailable"
        assert "OPENAI_API_KEY" in str(result["message"])
        assert result["preview"]["action_name"] == "Draft Email"


def test_service_generate_candidate_workflow_builds_request_from_goal_and_profiles() -> None:
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
        assert "professional_clear" in generation_request.input_text
        assert "analytical_review" in generation_request.input_text
        assert generation_request.max_output_tokens == 2200


def test_service_retries_generation_once_when_candidate_fails_quality_gate() -> None:
    with scratch_data_dir() as data_dir:
        gateway = QueueGateway(outputs=[json.dumps(build_meta_candidate_payload()), json.dumps(build_candidate_payload())])
        settings = Settings(
            data_dir=data_dir,
            templates_dir=templates_dir(),
            openai_api_key="unused-by-stub",
            openai_model="gpt-test-model",
        )
        service = WorkbenchService(settings, gateway=gateway)

        candidate = service.generate_candidate_workflow("Help me summarize meeting notes and extract action items")

        assert candidate.pack_id == "generated_meeting_helper"
        assert len(gateway.requests) == 2
        assert "Quality retry requirements:" in gateway.requests[1].input_text
        assert "overly meta or planning-heavy" in gateway.requests[1].input_text


def test_service_rejects_candidate_after_quality_retry_is_exhausted() -> None:
    with scratch_data_dir() as data_dir:
        gateway = QueueGateway(outputs=[json.dumps(build_meta_candidate_payload()), json.dumps(build_meta_candidate_payload())])
        settings = Settings(
            data_dir=data_dir,
            templates_dir=templates_dir(),
            openai_api_key="unused-by-stub",
            openai_model="gpt-test-model",
        )
        service = WorkbenchService(settings, gateway=gateway)

        with pytest.raises(ValidationFailure) as error:
            service.generate_candidate_workflow("Help me summarize meeting notes and extract action items")

        assert "quality gating after one regeneration attempt" in str(error.value)
        assert len(gateway.requests) == 2


def test_service_supports_legacy_profile_aliases() -> None:
    with scratch_data_dir() as data_dir:
        settings = Settings(
            data_dir=data_dir,
            templates_dir=templates_dir(),
            openai_api_key=None,
            openai_model=None,
        )
        service = WorkbenchService(settings)

        profile = service.get_response_profile("professional_email")
        assert profile.preset_id == "professional_clear"


def test_service_normalizes_legacy_profile_aliases_in_generated_candidates() -> None:
    payload = build_candidate_payload()
    payload["recommended_preset_ids"] = ["professional_email", "professional_clear"]
    payload["actions"][0]["default_preset_id"] = "professional_email"

    with scratch_data_dir() as data_dir:
        gateway = QueueGateway(outputs=[json.dumps(payload)])
        settings = Settings(
            data_dir=data_dir,
            templates_dir=templates_dir(),
            openai_api_key="unused-by-stub",
            openai_model="gpt-test-model",
        )
        service = WorkbenchService(settings, gateway=gateway)

        candidate = service.generate_candidate_workflow("Help me summarize meeting notes and extract action items")

        assert candidate.recommended_preset_ids == ["professional_clear"]
        assert candidate.actions[0].default_preset_id == "professional_clear"


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
            selected_controls=service.build_response_controls(
                tone="neutral",
                length="medium",
                language="en",
                output_style="structured",
                format="summary",
                strictness="medium",
            ),
        )

        assert any(pack.pack_id == "generated_meeting_helper" for pack in service.list_catalog_packs_detailed())
        assert result["mode"] == "live"
        assert result["output_text"] == "Generated live response."
        assert result["preview"]["pack_id"] == "generated_meeting_helper"
        assert result["preview"]["format"] == "summary"


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
        controller.handle_response_controls_changed(
            tone="friendly",
            length="medium",
            language="en",
            output_style="polished",
            format="email",
            strictness="low",
            goal_text="Write a polished client update",
            input_text="We fixed the issue and can deploy tomorrow morning.",
        )
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
        assert "friendly" in state.output_text
        assert "email" in state.output_text


def test_controller_can_edit_candidate_metadata() -> None:
    service, state, controller = build_controller([json.dumps(build_candidate_payload())])
    try:
        controller.bootstrap()
        controller.handle_generate_workflow("Help me summarize meeting notes and extract action items")

        controller.handle_apply_candidate_edits(
            title="Edited Meeting Workflow",
            summary="Shorter edited summary.",
            reasoning="Edited reasoning for the review pass.",
            recommended_preset_ids_text="concise_structured, analytical_review",
            action_name="Summarize Notes",
            action_description="Summarize raw meeting notes into a clear digest.",
            action_rationale="Meeting notes usually need an overview before deeper extraction.",
            action_default_preset_id="concise_structured",
            action_enabled=True,
        )

        assert state.candidate_pack is not None
        assert state.candidate_pack.title == "Edited Meeting Workflow"
        assert state.candidate_pack.summary == "Shorter edited summary."
        assert state.candidate_pack.reasoning == "Edited reasoning for the review pass."
        assert state.candidate_pack.recommended_preset_ids == ["concise_structured", "analytical_review"]
    finally:
        cleanup_controller(controller)


def test_controller_can_remove_candidate_action() -> None:
    service, state, controller = build_controller([json.dumps(build_candidate_payload())])
    try:
        controller.bootstrap()
        controller.handle_generate_workflow("Help me summarize meeting notes and extract action items")
        controller.handle_candidate_action_selected("extract_actions")
        controller.handle_remove_candidate_action()

        assert state.candidate_pack is not None
        assert [action.action_id for action in state.candidate_pack.actions] == ["summarize_notes"]
        assert state.selected_candidate_action == "summarize_notes"
    finally:
        cleanup_controller(controller)


def test_controller_can_change_candidate_action_default_profile() -> None:
    service, state, controller = build_controller([json.dumps(build_candidate_payload())])
    try:
        controller.bootstrap()
        controller.handle_generate_workflow("Help me summarize meeting notes and extract action items")
        controller.handle_candidate_action_selected("extract_actions")
        controller.handle_apply_candidate_edits(
            title=state.candidate_pack.title,
            summary=state.candidate_pack.summary,
            reasoning=state.candidate_pack.reasoning,
            recommended_preset_ids_text="concise_structured",
            action_name="Extract Action Items",
            action_description="Extract owners, due dates, and next steps from meeting notes.",
            action_rationale="Action extraction is a direct requirement in the goal.",
            action_default_preset_id="analytical_review",
            action_enabled=True,
        )

        assert state.candidate_pack is not None
        edited_action = next(action for action in state.candidate_pack.actions if action.action_id == "extract_actions")
        assert edited_action.default_preset_id == "analytical_review"
    finally:
        cleanup_controller(controller)


def test_controller_installs_edited_candidate_successfully() -> None:
    service, state, controller = build_controller([json.dumps(build_candidate_payload())])
    try:
        controller.bootstrap()
        controller.handle_generate_workflow("Help me summarize meeting notes and extract action items")
        controller.handle_apply_candidate_edits(
            title="Edited Meeting Workflow",
            summary="Install the edited candidate.",
            reasoning=state.candidate_pack.reasoning,
            recommended_preset_ids_text="concise_structured",
            action_name="Summarize Notes",
            action_description="Installable edited summary action.",
            action_rationale="Still needed before extraction.",
            action_default_preset_id="concise_structured",
            action_enabled=False,
        )
        controller.handle_install_candidate()

        installed = service.get_catalog_pack("generated_meeting_helper")
        assert state.candidate_pack is None
        assert state.available_candidate_actions == []
        assert state.selected_candidate_action is None
        assert installed.name == "Edited Meeting Workflow"
        assert installed.description == "Install the edited candidate."
        assert installed.actions[0].enabled is False
        assert installed.actions[0].description == "Installable edited summary action."
    finally:
        cleanup_controller(controller)


def test_controller_rejects_invalid_candidate_edit() -> None:
    service, state, controller = build_controller([json.dumps(build_candidate_payload())])
    try:
        controller.bootstrap()
        controller.handle_generate_workflow("Help me summarize meeting notes and extract action items")
        original_title = state.candidate_pack.title
        controller.handle_apply_candidate_edits(
            title="Broken Candidate",
            summary=state.candidate_pack.summary,
            reasoning=state.candidate_pack.reasoning,
            recommended_preset_ids_text="concise_structured",
            action_name="Summarize Notes",
            action_description="Summarize raw meeting notes into a clear digest.",
            action_rationale="Meeting notes usually need an overview before deeper extraction.",
            action_default_preset_id="unknown_profile",
            action_enabled=True,
        )

        assert state.candidate_pack is not None
        assert state.candidate_pack.title == original_title
        assert "Candidate Edit Rejected" in state.inspector_text
    finally:
        cleanup_controller(controller)


def test_controller_generation_failure_surfaces_missing_required_action_fields() -> None:
    incomplete_payload = build_candidate_payload()
    incomplete_payload["actions"] = [
        {
            "description": "Incomplete action object.",
            "kind": "template_fill",
            "enabled": True,
            "rationale": "This should fail validation.",
            "input_mode": "single_text",
            "fields": [],
            "default_preset_id": "professional_clear",
            "tags": [],
        }
    ]

    with scratch_data_dir() as data_dir:
        gateway = QueueGateway(outputs=[json.dumps(incomplete_payload)])
        settings = Settings(
            data_dir=data_dir,
            templates_dir=templates_dir(),
            openai_api_key="unused-by-stub",
            openai_model="gpt-test-model",
        )
        service = WorkbenchService(settings, gateway=gateway)
        controller = AppController(service=service, state=AppState())

        controller.bootstrap()
        controller.handle_generate_workflow("Create a workflow pack for personalized diet plans")

        assert "Generated workflow is missing required action fields." in controller.state.inspector_text
        assert "action_id" in controller.state.inspector_text
        assert controller.state.candidate_pack is None


def test_candidate_action_list_populates_after_generation() -> None:
    service, state, controller = build_controller([json.dumps(build_candidate_payload())])
    try:
        controller.bootstrap()
        controller.handle_generate_workflow("Help me summarize meeting notes and extract action items")

        assert state.available_candidate_actions == ["summarize_notes", "extract_actions"]
    finally:
        cleanup_controller(controller)


def test_first_candidate_action_is_auto_selected_after_generation() -> None:
    service, state, controller = build_controller([json.dumps(build_candidate_payload())])
    try:
        controller.bootstrap()
        controller.handle_generate_workflow("Help me summarize meeting notes and extract action items")

        assert state.selected_candidate_action == "summarize_notes"
    finally:
        cleanup_controller(controller)


def test_candidate_action_selection_syncs_editor_state() -> None:
    service, state, controller = build_controller([json.dumps(build_candidate_payload())])
    try:
        controller.bootstrap()
        controller.handle_generate_workflow("Help me summarize meeting notes and extract action items")
        controller.handle_candidate_action_selected("extract_actions")

        assert state.selected_candidate_action == "extract_actions"
        assert "Candidate Workflow Action" in state.inspector_text
        assert "Action Name: Extract Action Items" in state.inspector_text
    finally:
        cleanup_controller(controller)


def test_candidate_action_removal_updates_list_and_selection() -> None:
    service, state, controller = build_controller([json.dumps(build_candidate_payload())])
    try:
        controller.bootstrap()
        controller.handle_generate_workflow("Help me summarize meeting notes and extract action items")
        controller.handle_candidate_action_selected("extract_actions")
        controller.handle_remove_candidate_action()

        assert state.available_candidate_actions == ["summarize_notes"]
        assert state.selected_candidate_action == "summarize_notes"
        assert "Action Name: Summarize Notes" in state.inspector_text
    finally:
        cleanup_controller(controller)


def test_controller_generation_failure_includes_model_output_snippet() -> None:
    raw_output = "I will explain first. Use placeholders like {goal_text}. Then JSON later maybe."

    with scratch_data_dir() as data_dir:
        gateway = QueueGateway(outputs=[raw_output])
        settings = Settings(
            data_dir=data_dir,
            templates_dir=templates_dir(),
            openai_api_key="unused-by-stub",
            openai_model="gpt-test-model",
        )
        service = WorkbenchService(settings, gateway=gateway)
        controller = AppController(service=service, state=AppState())

        controller.bootstrap()
        controller.handle_generate_workflow("Help me create the best competitive pokemon team")

        assert "Workflow Generation Failed" in controller.state.inspector_text
        assert "Model output snippet:" in controller.state.inspector_text
        assert "Use placeholders like {goal_text}" in controller.state.inspector_text
        assert controller.state.candidate_pack is None


def test_controller_updates_universal_controls_in_state() -> None:
    service, state, controller = build_controller([])
    try:
        controller.bootstrap()
        controller.handle_response_controls_changed(
            tone="friendly",
            length="short",
            language="es",
            output_style="simple",
            format="summary",
            strictness="low",
            goal_text="Help me rewrite a message",
            input_text="Original content",
        )

        assert state.selected_tone == "friendly"
        assert state.selected_length == "short"
        assert state.selected_language == "es"
        assert state.selected_style == "simple"
        assert state.selected_format == "summary"
        assert state.selected_strictness == "low"
    finally:
        cleanup_controller(controller)




