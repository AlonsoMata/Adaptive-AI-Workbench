from __future__ import annotations

from pathlib import Path
from typing import Any

from adaptive_ai_workbench.domain.errors import (
    CandidateGenerationFailure,
    CandidateGenerationFailureReason,
    CandidateGenerationFeedback,
    ConfigurationError,
    ModelOutputError,
    StorageError,
    ValidationFailure,
)
from adaptive_ai_workbench.domain.models import (
    ActionDefinition,
    CandidateActionPack,
    InstalledActionPack,
    PresetDefinition,
    ResponseControls,
)
from adaptive_ai_workbench.execution.dispatcher import ExecutionDispatcher
from adaptive_ai_workbench.model.gateway import ModelGateway, OpenAIModelGateway
from adaptive_ai_workbench.model.prompt_loader import load_prompt
from adaptive_ai_workbench.persistence.action_pack_store import ActionPackStore
from adaptive_ai_workbench.persistence.preset_store import PresetStore
from adaptive_ai_workbench.planning.goal_analyzer import normalize_goal_text
from adaptive_ai_workbench.planning.workflow_generator import build_candidate_generation_prompt
from adaptive_ai_workbench.safety.parsing import parse_candidate_action_pack
from adaptive_ai_workbench.safety.validators import find_generated_candidate_quality_issues, validate_candidate_pack
from adaptive_ai_workbench.settings import Settings


class WorkbenchService:
    WORKFLOW_GENERATION_MAX_OUTPUT_TOKENS = 2200
    WORKFLOW_GENERATION_MAX_QUALITY_RETRIES = 1

    def __init__(self, settings: Settings, gateway: ModelGateway | None = None) -> None:
        self.settings = settings
        self.gateway = gateway or OpenAIModelGateway(settings)
        self.dispatcher = ExecutionDispatcher()
        self.action_pack_store = ActionPackStore(
            data_dir=settings.data_dir,
            templates_dir=settings.templates_dir,
        )
        self.preset_store = PresetStore(settings.templates_dir)

    def get_app_metadata(self) -> dict[str, str]:
        return {
            "app_name": self.settings.app_name,
            "model": self.settings.openai_model or "unconfigured",
            "data_dir": str(self.settings.data_dir),
        }

    def health_status(self) -> str:
        if self.gateway.is_configured():
            return "Model gateway configured. You can generate workflow packs from a goal and run installed workflows live."
        return "Model gateway not configured. You can inspect built-in workflows locally, but workflow generation and live execution require OPENAI_API_KEY and AI_WORKBENCH_MODEL."

    def list_builtin_prompt_names(self) -> list[str]:
        return self._list_template_names(self.settings.templates_dir / "prompts", ".txt")

    def list_builtin_pack_names(self) -> list[str]:
        return self.action_pack_store.list_builtin_templates()

    def list_response_profile_names(self) -> list[str]:
        return sorted(profile.preset_id for profile in self.preset_store.list_builtin())

    def list_builtin_preset_names(self) -> list[str]:
        return self.list_response_profile_names()

    def list_builtin_packs_detailed(self) -> list[InstalledActionPack]:
        return [
            self.action_pack_store.load_builtin_template(pack_id)
            for pack_id in self.action_pack_store.list_builtin_templates()
        ]

    def list_response_profiles_detailed(self) -> list[PresetDefinition]:
        return self.preset_store.list_builtin()

    def list_builtin_presets_detailed(self) -> list[PresetDefinition]:
        return self.list_response_profiles_detailed()

    def list_response_control_options(self) -> dict[str, list[str]]:
        return {
            "tone": list(ResponseControls.tone_options),
            "length": list(ResponseControls.length_options),
            "language": list(ResponseControls.language_options),
            "style": list(ResponseControls.style_options),
            "format": list(ResponseControls.format_options),
            "strictness": list(ResponseControls.strictness_options),
        }

    def get_default_response_controls(self) -> ResponseControls:
        profiles = self.list_response_profiles_detailed()
        if profiles:
            return profiles[0].to_response_controls()
        return ResponseControls()

    def get_response_profile(self, profile_id: str) -> PresetDefinition:
        return self.preset_store.load_builtin(profile_id)

    def list_catalog_packs_detailed(self) -> list[InstalledActionPack]:
        catalog = {pack.pack_id: pack for pack in self.list_builtin_packs_detailed()}
        for pack in self.action_pack_store.list_installed():
            catalog[pack.pack_id] = pack
        return sorted(catalog.values(), key=lambda pack: pack.name.lower())

    def get_builtin_pack(self, pack_id: str) -> InstalledActionPack:
        return self.action_pack_store.load_builtin_template(pack_id)

    def get_catalog_pack(self, pack_id: str) -> InstalledActionPack:
        try:
            return self.action_pack_store.load_installed(pack_id)
        except StorageError:
            return self.action_pack_store.load_builtin_template(pack_id)

    def build_response_controls(
        self,
        *,
        tone: str,
        length: str,
        language: str,
        output_style: str,
        format: str,
        strictness: str,
    ) -> ResponseControls:
        return ResponseControls(
            tone=tone,
            length=length,
            language=language,
            output_style=output_style,
            format=format,
            strictness=strictness,
        )

    def apply_response_profile(self, profile_id: str) -> ResponseControls:
        return self.get_response_profile(profile_id).to_response_controls()

    def resolve_response_controls_for_action(
        self,
        pack: InstalledActionPack,
        action: ActionDefinition,
        selected_controls: ResponseControls | None,
    ) -> tuple[ResponseControls, PresetDefinition | None]:
        if selected_controls is not None:
            return ResponseControls.model_validate(selected_controls.model_dump()), None

        profile_ids = [
            action.default_preset_id,
            *(pack.recommended_preset_ids or []),
        ]
        for profile_id in profile_ids:
            if profile_id and self.preset_store.is_known_preset_id(profile_id):
                profile = self.get_response_profile(profile_id)
                return profile.to_response_controls(), profile

        return self.get_default_response_controls(), None

    def generate_candidate_workflow(self, goal_text: str) -> CandidateActionPack:
        normalized_goal = normalize_goal_text(goal_text)
        if not normalized_goal:
            raise ValidationFailure("Enter a goal before generating a workflow.")
        if not self.gateway.is_configured():
            raise ConfigurationError(
                "Workflow generation is unavailable because OPENAI_API_KEY or AI_WORKBENCH_MODEL is not configured."
            )
        system_prompt = load_prompt("generate_action_pack", self.settings.templates_dir)
        presets = self.list_response_profiles_detailed()
        quality_feedback: list[str] | None = None

        for attempt in range(self.WORKFLOW_GENERATION_MAX_QUALITY_RETRIES + 1):
            generation_prompt = build_candidate_generation_prompt(
                goal_text=normalized_goal,
                system_prompt=system_prompt,
                presets=presets,
                quality_feedback=quality_feedback,
            )
            try:
                result = self.gateway.generate_text(
                    system_prompt=generation_prompt.system_prompt,
                    user_prompt=generation_prompt.user_prompt,
                    max_output_tokens=self.WORKFLOW_GENERATION_MAX_OUTPUT_TOKENS,
                )
                candidate = parse_candidate_action_pack(result.output_text)
                validated_candidate = self.validate_candidate_workflow(candidate)
            except CandidateGenerationFailure:
                raise
            except (ModelOutputError, ValidationFailure) as error:
                raise self._normalize_candidate_generation_error(error) from error

            quality_issues = find_generated_candidate_quality_issues(validated_candidate, normalized_goal)
            if not quality_issues:
                return validated_candidate
            if attempt < self.WORKFLOW_GENERATION_MAX_QUALITY_RETRIES:
                quality_feedback = quality_issues
                continue
            raise CandidateGenerationFailure(
                CandidateGenerationFeedback(
                    reason_code=CandidateGenerationFailureReason.semantic_quality_rejection,
                    category_label="Semantic Quality Rejection",
                    summary=(
                        "The generated workflow was structurally valid, but it was rejected because it did not pass "
                        "the usefulness checks for this goal."
                    ),
                    action=(
                        "Try Generate Workflow again with a more concrete goal or specify the outputs you want the "
                        "workflow to produce."
                    ),
                    technical_details=" ".join(quality_issues),
                )
            )

        raise CandidateGenerationFailure(
            CandidateGenerationFeedback(
                reason_code=CandidateGenerationFailureReason.semantic_quality_rejection,
                category_label="Semantic Quality Rejection",
                summary="The generated workflow was rejected by the quality gate.",
                action="Try Generate Workflow again with a more concrete goal.",
            )
        )

    def validate_candidate_workflow(self, candidate: CandidateActionPack) -> CandidateActionPack:
        validated_candidate = validate_candidate_pack(candidate)
        normalized_candidate = self._normalize_candidate_profiles(validated_candidate)
        self._validate_candidate_profiles(normalized_candidate)
        return normalized_candidate

    def install_candidate_workflow(self, candidate: CandidateActionPack) -> InstalledActionPack:
        validated_candidate = self.validate_candidate_workflow(candidate)
        if validated_candidate.pack_id in {pack.pack_id for pack in self.list_catalog_packs_detailed()}:
            raise ValidationFailure(
                f"A workflow pack with id '{validated_candidate.pack_id}' already exists in the catalog."
            )
        return self.action_pack_store.install_candidate(validated_candidate)

    def preview_action(
        self,
        pack_id: str,
        action_id: str,
        goal_text: str,
        input_text: str,
        selected_controls: ResponseControls | None,
    ) -> dict[str, Any]:
        pack = self.get_catalog_pack(pack_id)
        action = self._find_action(pack, action_id)
        response_controls, profile = self.resolve_response_controls_for_action(pack, action, selected_controls)
        preview = self.dispatcher.dispatch(
            action=action,
            input_text=input_text,
            response_controls=response_controls,
            goal_text=goal_text,
        )
        preview["pack_id"] = pack.pack_id
        preview["pack_name"] = pack.name
        preview["action_name"] = action.name
        preview["control_profile_id"] = profile.preset_id if profile else None
        preview["control_profile_name"] = profile.name if profile else None
        return preview

    def preview_builtin_action(
        self,
        pack_id: str,
        action_id: str,
        goal_text: str,
        input_text: str,
        selected_controls: ResponseControls | None,
    ) -> dict[str, Any]:
        return self.preview_action(
            pack_id=pack_id,
            action_id=action_id,
            goal_text=goal_text,
            input_text=input_text,
            selected_controls=selected_controls,
        )

    def execute_action(
        self,
        pack_id: str,
        action_id: str,
        goal_text: str,
        input_text: str,
        selected_controls: ResponseControls | None,
    ) -> dict[str, Any]:
        preview = self.preview_action(
            pack_id=pack_id,
            action_id=action_id,
            goal_text=goal_text,
            input_text=input_text,
            selected_controls=selected_controls,
        )

        if not self.gateway.is_configured():
            return {
                "mode": "unavailable",
                "message": (
                    "Live execution is unavailable. Configure OPENAI_API_KEY and AI_WORKBENCH_MODEL in .env "
                    "to run installed workflows against the model gateway."
                ),
                "preview": preview,
            }

        try:
            generation = self.gateway.generate_text(
                system_prompt=str(preview["system_prompt"]),
                user_prompt=str(preview["user_prompt"]),
            )
        except Exception as exc:
            return {
                "mode": "error",
                "message": f"Live execution failed: {exc}",
                "preview": preview,
            }

        return {
            "mode": "live",
            "output_text": generation.output_text,
            "preview": preview,
            "request": generation.request.to_dict(),
        }

    def execute_builtin_action(
        self,
        pack_id: str,
        action_id: str,
        goal_text: str,
        input_text: str,
        selected_controls: ResponseControls | None,
    ) -> dict[str, Any]:
        return self.execute_action(
            pack_id=pack_id,
            action_id=action_id,
            goal_text=goal_text,
            input_text=input_text,
            selected_controls=selected_controls,
        )

    def _validate_candidate_profiles(self, candidate: CandidateActionPack) -> None:
        invalid_recommended = [
            profile_id for profile_id in candidate.recommended_preset_ids if not self.preset_store.is_known_preset_id(profile_id)
        ]
        if invalid_recommended:
            raise ValidationFailure(
                "Candidate workflow references unknown response profiles: "
                + ", ".join(sorted(invalid_recommended))
            )

        invalid_defaults = [
            action.default_preset_id
            for action in candidate.actions
            if action.default_preset_id and not self.preset_store.is_known_preset_id(action.default_preset_id)
        ]
        if invalid_defaults:
            raise ValidationFailure(
                "Candidate workflow references unknown action default response profiles: "
                + ", ".join(sorted(set(invalid_defaults)))
            )

    def _normalize_candidate_profiles(self, candidate: CandidateActionPack) -> CandidateActionPack:
        seen_recommended: set[str] = set()
        normalized_recommended: list[str] = []
        for profile_id in candidate.recommended_preset_ids:
            resolved_profile_id = self.preset_store.resolve_preset_id(profile_id)
            if resolved_profile_id not in seen_recommended:
                normalized_recommended.append(resolved_profile_id)
                seen_recommended.add(resolved_profile_id)

        normalized_actions = [
            action.model_copy(
                update={
                    "default_preset_id": (
                        self.preset_store.resolve_preset_id(action.default_preset_id)
                        if action.default_preset_id
                        else None
                    )
                }
            )
            for action in candidate.actions
        ]

        return candidate.model_copy(
            update={
                "recommended_preset_ids": normalized_recommended,
                "actions": normalized_actions,
            }
        )

    @staticmethod
    def _find_action(pack: InstalledActionPack, action_id: str) -> ActionDefinition:
        for action in pack.actions:
            if action.action_id == action_id:
                return action
        raise ValidationFailure(f"Action not found in pack {pack.pack_id}: {action_id}")

    @staticmethod
    def _list_template_names(directory: Path, suffix: str) -> list[str]:
        if not directory.exists():
            return []
        return sorted(path.stem for path in directory.glob(f"*{suffix}") if path.is_file())

    @staticmethod
    def _normalize_candidate_generation_error(
        error: ModelOutputError | ValidationFailure,
    ) -> CandidateGenerationFailure:
        message = str(error)
        lowered = message.casefold()

        if "incomplete response" in lowered:
            return CandidateGenerationFailure(
                CandidateGenerationFeedback(
                    reason_code=CandidateGenerationFailureReason.incomplete_model_response,
                    category_label="Incomplete Model Response",
                    summary="The model started the workflow candidate but did not finish it.",
                    action=(
                        "Try Generate Workflow again. If this keeps happening, shorten the goal or ask for a smaller "
                        "workflow pack."
                    ),
                    technical_details=message,
                )
            )

        if isinstance(error, ModelOutputError):
            if any(
                phrase in lowered
                for phrase in (
                    "no json object found in model output",
                    "could not find a valid json object in model output",
                    "could not extract a balanced json object from model output",
                    "unable to parse extracted json object",
                    "model output must be a json object",
                    "appears to contain an incomplete candidate workflow json object",
                )
            ):
                return CandidateGenerationFailure(
                    CandidateGenerationFeedback(
                        reason_code=CandidateGenerationFailureReason.parse_failure,
                        category_label="Parse Failure",
                        summary="The model response could not be read as a complete workflow candidate.",
                        action=(
                            "Try Generate Workflow again. If it keeps failing, make the goal more specific or split "
                            "it into a smaller request."
                        ),
                        technical_details=message,
                    )
                )

            return CandidateGenerationFailure(
                CandidateGenerationFeedback(
                    reason_code=CandidateGenerationFailureReason.structural_validation_failure,
                    category_label="Structural Validation Failure",
                    summary="The model returned a workflow candidate, but required fields or values were invalid.",
                    action="Try Generate Workflow again. If it keeps failing, simplify the goal and review the details.",
                    technical_details=message,
                )
            )

        if "structured_fields actions are not currently supported" in lowered:
            return CandidateGenerationFailure(
                CandidateGenerationFeedback(
                    reason_code=CandidateGenerationFailureReason.unsupported_runtime_shape,
                    category_label="Unsupported Action Shape",
                    summary=(
                        "The generated workflow uses action inputs that the current review and execution flow does "
                        "not support."
                    ),
                    action=(
                        "Try Generate Workflow again and ask for actions that work from a single text input or a "
                        "text-plus-instruction flow."
                    ),
                    technical_details=message,
                )
            )

        if any(
            phrase in lowered
            for phrase in (
                "model generation failed",
                "model generation did not complete successfully",
                "the model returned an empty response",
            )
        ):
            return CandidateGenerationFailure(
                CandidateGenerationFeedback(
                    reason_code=CandidateGenerationFailureReason.model_failure,
                    category_label="Model or Gateway Failure",
                    summary="The model did not return a usable workflow candidate.",
                    action="Try Generate Workflow again. If the problem persists, check the model configuration and retry.",
                    technical_details=message,
                )
            )

        return CandidateGenerationFailure(
            CandidateGenerationFeedback(
                reason_code=CandidateGenerationFailureReason.structural_validation_failure,
                category_label="Structural Validation Failure",
                summary="The generated workflow candidate did not pass validation.",
                action="Try Generate Workflow again. If it keeps failing, review the details and simplify the goal.",
                technical_details=message,
            )
        )



