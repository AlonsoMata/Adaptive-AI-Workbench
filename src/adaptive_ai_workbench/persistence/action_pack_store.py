from __future__ import annotations

from pathlib import Path

from adaptive_ai_workbench.domain.errors import StorageError
from adaptive_ai_workbench.domain.models import CandidateActionPack, InstalledActionPack
from adaptive_ai_workbench.safety.validators import install_candidate_pack


class ActionPackStore:
    def __init__(self, data_dir: Path, templates_dir: Path) -> None:
        self._installed_dir = data_dir / "action_packs"
        self._templates_dir = templates_dir / "packs"
        self._installed_dir.mkdir(parents=True, exist_ok=True)

    def list_installed(self) -> list[InstalledActionPack]:
        packs = [self._load_path(path) for path in sorted(self._installed_dir.glob("*.json"))]
        return sorted(packs, key=lambda pack: pack.name.lower())

    def load_installed(self, pack_id: str) -> InstalledActionPack:
        path = self._installed_dir / f"{pack_id}.json"
        if not path.exists():
            raise StorageError(f"Installed action pack not found: {pack_id}")
        return self._load_path(path)

    def save_installed(self, pack: InstalledActionPack) -> Path:
        path = self._installed_dir / f"{pack.pack_id}.json"
        path.write_text(pack.model_dump_json(indent=2), encoding="utf-8")
        return path

    def install_candidate(self, candidate: CandidateActionPack) -> InstalledActionPack:
        installed = install_candidate_pack(candidate)
        self.save_installed(installed)
        return installed

    def list_builtin_templates(self) -> list[str]:
        if not self._templates_dir.exists():
            return []
        return sorted(path.stem for path in self._templates_dir.glob("*.json") if path.is_file())

    def load_builtin_template(self, pack_id: str) -> InstalledActionPack:
        path = self._templates_dir / f"{pack_id}.json"
        if not path.exists():
            raise StorageError(f"Built-in template pack not found: {pack_id}")
        return self._load_path(path)

    @staticmethod
    def _load_path(path: Path) -> InstalledActionPack:
        try:
            return InstalledActionPack.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise StorageError(f"Failed to load action pack from {path}: {exc}") from exc
