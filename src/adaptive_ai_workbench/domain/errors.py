from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class WorkbenchError(Exception):
    """Base application error."""


class ConfigurationError(WorkbenchError):
    """Raised when configuration is invalid."""


class ModelOutputError(WorkbenchError):
    """Raised when model output cannot be parsed safely."""


class ValidationFailure(WorkbenchError):
    """Raised when a structured payload fails validation."""


class StorageError(WorkbenchError):
    """Raised when reading or writing persisted data fails."""


class CandidateGenerationFailureReason(str, Enum):
    incomplete_model_response = "incomplete_model_response"
    model_failure = "model_failure"
    parse_failure = "parse_failure"
    structural_validation_failure = "structural_validation_failure"
    unsupported_runtime_shape = "unsupported_runtime_shape"
    semantic_quality_rejection = "semantic_quality_rejection"


@dataclass(slots=True, frozen=True)
class CandidateGenerationFeedback:
    reason_code: CandidateGenerationFailureReason
    category_label: str
    summary: str
    action: str
    technical_details: str | None = None


class CandidateGenerationFailure(WorkbenchError):
    """Raised when candidate generation fails with normalized user-facing feedback."""

    def __init__(self, feedback: CandidateGenerationFeedback) -> None:
        super().__init__(feedback.summary)
        self.feedback = feedback
