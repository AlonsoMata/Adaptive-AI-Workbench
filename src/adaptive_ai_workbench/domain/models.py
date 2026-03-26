from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from adaptive_ai_workbench.domain.enums import ActionKind, InputMode, PackSource

SLUG_PATTERN = re.compile(r"^[a-z0-9_-]+$")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def _validate_slug(value: str, field_name: str) -> str:
    if not SLUG_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must match ^[a-z0-9_-]+$")
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


class PresetDefinition(StrictModel):
    schema_version: str = "1.0"
    preset_id: str
    name: str
    description: str
    tone: str = "professional"
    language: str = "en"
    output_style: str = "clear"
    length: str = "balanced"

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


class CandidateActionPack(StrictModel):
    schema_version: str = "1.0"
    pack_id: str
    goal: str
    title: str
    summary: str
    reasoning: str
    warnings: list[str] = Field(default_factory=list)
    actions: list[ActionDefinition]

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
