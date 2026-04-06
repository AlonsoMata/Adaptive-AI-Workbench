from pathlib import Path


def load_prompt(name: str, templates_dir: Path) -> str:
    prompt_path = templates_dir / "prompts" / f"{name}.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {name}")
    return prompt_path.read_text(encoding="utf-8-sig")

