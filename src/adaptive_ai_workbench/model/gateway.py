from __future__ import annotations

from abc import ABC, abstractmethod

from adaptive_ai_workbench.settings import Settings


class ModelGateway(ABC):
    @abstractmethod
    def is_configured(self) -> bool:
        raise NotImplementedError


class OpenAIModelGateway(ModelGateway):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def is_configured(self) -> bool:
        return bool(self._settings.openai_api_key and self._settings.openai_model)
