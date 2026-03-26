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
