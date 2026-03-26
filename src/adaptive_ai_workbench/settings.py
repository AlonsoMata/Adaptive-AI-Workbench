from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import tempfile

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    app_name: str = "Adaptive AI Workbench"
    openai_api_key: str | None = None
    openai_model: str | None = None
    log_level: str = "INFO"
    data_dir: Path = Path(tempfile.gettempdir()) / "AdaptiveAIWorkbench"
    templates_dir: Path = Path("templates")
    request_timeout_seconds: float = 60.0

    @classmethod
    def from_env(cls) -> "Settings":
        package_root = Path(__file__).resolve().parent
        project_root = package_root.parents[1]
        load_dotenv(project_root / ".env", override=False)

        raw_data_dir = (os.getenv("AI_WORKBENCH_DATA_DIR") or "").strip()
        if raw_data_dir:
            data_dir = Path(raw_data_dir)
            if not data_dir.is_absolute():
                data_dir = Path(tempfile.gettempdir()) / raw_data_dir
        else:
            data_dir = Path(tempfile.gettempdir()) / "AdaptiveAIWorkbench"

        templates_dir = package_root / "templates"
        data_dir.mkdir(parents=True, exist_ok=True)

        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY") or None,
            openai_model=os.getenv("AI_WORKBENCH_MODEL") or None,
            log_level=os.getenv("AI_WORKBENCH_LOG_LEVEL", "INFO"),
            data_dir=data_dir,
            templates_dir=templates_dir,
            request_timeout_seconds=60.0,
        )