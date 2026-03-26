from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass

from openai import OpenAI

from adaptive_ai_workbench.domain.errors import ConfigurationError, ValidationFailure
from adaptive_ai_workbench.settings import Settings


@dataclass(slots=True)
class TextGenerationRequest:
    model: str
    instructions: str
    input_text: str
    max_output_tokens: int = 900
    temperature: float = 0.4

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class TextGenerationResult:
    output_text: str
    request: TextGenerationRequest


class ModelGateway(ABC):
    @abstractmethod
    def is_configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def build_text_request(self, system_prompt: str, user_prompt: str) -> TextGenerationRequest:
        raise NotImplementedError

    @abstractmethod
    def generate_text(self, system_prompt: str, user_prompt: str) -> TextGenerationResult:
        raise NotImplementedError


class OpenAIModelGateway(ModelGateway):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: OpenAI | None = None

    def is_configured(self) -> bool:
        return bool(self._settings.openai_api_key and self._settings.openai_model)

    def build_text_request(self, system_prompt: str, user_prompt: str) -> TextGenerationRequest:
        if not self._settings.openai_model:
            raise ConfigurationError("AI_WORKBENCH_MODEL is not configured.")
        return TextGenerationRequest(
            model=self._settings.openai_model,
            instructions=system_prompt,
            input_text=user_prompt,
        )

    def generate_text(self, system_prompt: str, user_prompt: str) -> TextGenerationResult:
        if not self.is_configured():
            raise ConfigurationError(
                "Live execution is unavailable because OPENAI_API_KEY or AI_WORKBENCH_MODEL is not configured."
            )

        request = self.build_text_request(system_prompt=system_prompt, user_prompt=user_prompt)
        response = self._get_client().responses.create(
            model=request.model,
            instructions=request.instructions,
            input=request.input_text,
            max_output_tokens=request.max_output_tokens,
            temperature=request.temperature,
        )
        output_text = (response.output_text or "").strip()
        if not output_text:
            raise ValidationFailure("The model returned an empty response.")
        return TextGenerationResult(output_text=output_text, request=request)

    def _get_client(self) -> OpenAI:
        if self._client is None:
            if not self._settings.openai_api_key:
                raise ConfigurationError("OPENAI_API_KEY is not configured.")
            self._client = OpenAI(
                api_key=self._settings.openai_api_key,
                timeout=self._settings.request_timeout_seconds,
            )
        return self._client