from contextlib import contextmanager
from pathlib import Path
import shutil
from uuid import uuid4

from adaptive_ai_workbench.model.gateway import OpenAIModelGateway
from adaptive_ai_workbench.settings import Settings


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


def test_gateway_builds_live_text_request_from_system_and_user_prompts() -> None:
    with scratch_data_dir() as data_dir:
        settings = Settings(
            data_dir=data_dir,
            templates_dir=templates_dir(),
            openai_api_key="test-key",
            openai_model="gpt-test-model",
        )
        gateway = OpenAIModelGateway(settings)

        request = gateway.build_text_request(
            system_prompt="You are a precise writing assistant.",
            user_prompt="Rewrite this text for a client update.",
            max_output_tokens=2200,
        )

        assert request.model == "gpt-test-model"
        assert request.instructions == "You are a precise writing assistant."
        assert request.input_text == "Rewrite this text for a client update."
        assert request.max_output_tokens == 2200
        assert request.temperature == 0.4
