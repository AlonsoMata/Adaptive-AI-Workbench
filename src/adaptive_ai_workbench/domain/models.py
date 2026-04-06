from __future__ import annotations

import re
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from adaptive_ai_workbench.domain.enums import ActionKind, InputMode, PackSource

SLUG_PATTERN = re.compile(r"^[a-z0-9_-]+$")

TONE_OPTIONS = (
    "professional",
    "friendly",
    "formal",
    "informal",
    "direct",
    "neutral",
)
LENGTH_OPTIONS = ("short", "medium", "long")
LANGUAGE_OPTIONS = ("en", "es", "bilingual")
STYLE_OPTIONS = (
    "clear",
    "polished",
    "structured",
    "analytical",
    "concise",
    "simple",
    "persuasive",
)
FORMAT_OPTIONS = (
    "paragraph",
    "bullet_points",
    "step_by_step",
    "summary",
    "report",
    "email",
)
STRICTNESS_OPTIONS = ("low", "medium", "high")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def _validate_slug(value: str, field_name: str) -> str:
    if not SLUG_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must match ^[a-z0-9_-]+$")
    return value


def _validate_choice(value: str, field_name: str, options: tuple[str, ...]) -> str:
    if value not in options:
        raise ValueError(f"{field_name} must be one of: {', '.join(options)}")
    return value


class InputFieldDefinition(StrictModel):
    name: str
    label: str
    required: bool = True
    placeholder: str = ""

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _validate_slug(value, "name")


class ResponseControls(StrictModel):
    tone: str = "professional"
    language: str = "en"
    output_style: str = "clear"
    length: str = "medium"
    format: str = "paragraph"
    strictness: str = "medium"

    tone_options: ClassVar[tuple[str, ...]] = TONE_OPTIONS
    language_options: ClassVar[tuple[str, ...]] = LANGUAGE_OPTIONS
    style_options: ClassVar[tuple[str, ...]] = STYLE_OPTIONS
    length_options: ClassVar[tuple[str, ...]] = LENGTH_OPTIONS
    format_options: ClassVar[tuple[str, ...]] = FORMAT_OPTIONS
    strictness_options: ClassVar[tuple[str, ...]] = STRICTNESS_OPTIONS

    @field_validator("tone")
    @classmethod
    def validate_tone(cls, value: str) -> str:
        return _validate_choice(value, "tone", TONE_OPTIONS)

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        return _validate_choice(value, "language", LANGUAGE_OPTIONS)

    @field_validator("output_style")
    @classmethod
    def validate_output_style(cls, value: str) -> str:
        return _validate_choice(value, "output_style", STYLE_OPTIONS)

    @field_validator("length")
    @classmethod
    def validate_length(cls, value: str) -> str:
        return _validate_choice(value, "length", LENGTH_OPTIONS)

    @field_validator("format")
    @classmethod
    def validate_format(cls, value: str) -> str:
        return _validate_choice(value, "format", FORMAT_OPTIONS)

    @field_validator("strictness")
    @classmethod
    def validate_strictness(cls, value: str) -> str:
        return _validate_choice(value, "strictness", STRICTNESS_OPTIONS)


class ActionDefinition(StrictModel):
    action_id: str
    name: str
    description: str
    kind: ActionKind
    enabled: bool = True
    rationale: str
    input_mode: InputMode = InputMode.single_text
    fields: list[InputFieldDefinition] = Field(default_factory=list)
    system_prompt: str
    user_prompt_template: str
    default_preset_id: str | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("action_id")
    @classmethod
    def validate_action_id(cls, value: str) -> str:
        return _validate_slug(value, "action_id")

    @field_validator("default_preset_id")
    @classmethod
    def validate_default_preset_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_slug(value, "default_preset_id")

    @field_validator("system_prompt", "user_prompt_template")
    @classmethod
    def validate_prompt_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("prompt text must not be empty")
        return value


class PresetDefinition(ResponseControls):
    schema_version: str = "1.0"
    preset_id: str
    name: str
    description: str

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        if not value:
            raise ValueError("schema_version is required")
        return value

    @field_validator("preset_id")
    @classmethod
    def validate_preset_id(cls, value: str) -> str:
        return _validate_slug(value, "preset_id")

    def to_response_controls(self) -> ResponseControls:
        return ResponseControls(
            tone=self.tone,
            language=self.language,
            output_style=self.output_style,
            length=self.length,
            format=self.format,
            strictness=self.strictness,
        )


class CandidateActionPack(StrictModel):
    schema_version: str = "1.0"
    pack_id: str
    goal: str
    title: str
    summary: str
    reasoning: str
    warnings: list[str] = Field(default_factory=list)
    actions: list[ActionDefinition]
    recommended_preset_ids: list[str] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        if not value:
            raise ValueError("schema_version is required")
        return value

    @field_validator("pack_id")
    @classmethod
    def validate_pack_id(cls, value: str) -> str:
        return _validate_slug(value, "pack_id")

    @field_validator("recommended_preset_ids")
    @classmethod
    def validate_recommended_preset_ids(cls, values: list[str]) -> list[str]:
        return [_validate_slug(value, "recommended_preset_id") for value in values]

    @model_validator(mode="after")
    def validate_actions(self) -> "CandidateActionPack":
        if not self.actions:
            raise ValueError("actions must not be empty")
        return self


class InstalledActionPack(StrictModel):
    schema_version: str = "1.0"
    pack_id: str
    name: str
    description: str
    source: PackSource
    origin_goal: str | None = None
    installed_at: str
    enabled: bool = True
    actions: list[ActionDefinition]
    recommended_preset_ids: list[str] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        if not value:
            raise ValueError("schema_version is required")
        return value

    @field_validator("pack_id")
    @classmethod
    def validate_pack_id(cls, value: str) -> str:
        return _validate_slug(value, "pack_id")

    @field_validator("recommended_preset_ids")
    @classmethod
    def validate_recommended_preset_ids(cls, values: list[str]) -> list[str]:
        return [_validate_slug(value, "recommended_preset_id") for value in values]

    @model_validator(mode="after")
    def validate_actions(self) -> "InstalledActionPack":
        if not self.actions:
            raise ValueError("actions must not be empty")
        return self


class WorkbenchProject(StrictModel):
    schema_version: str = "1.0"
    project_id: str
    goal_text: str
    input_text: str
    selected_pack_id: str | None = None
    selected_preset_id: str | None = None
    selected_controls: ResponseControls | None = None

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        if not value:
            raise ValueError("schema_version is required")
        return value

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, value: str) -> str:
        return _validate_slug(value, "project_id")

    @field_validator("selected_pack_id", "selected_preset_id")
    @classmethod
    def validate_optional_slugs(cls, value: str | None, info: object) -> str | None:
        if value is None:
            return None
        field_name = getattr(info, "field_name", "value")
        return _validate_slug(value, field_name)
