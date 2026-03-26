from __future__ import annotations

from datetime import datetime, timezone

from adaptive_ai_workbench.domain.enums import PackSource
from adaptive_ai_workbench.domain.errors import ValidationFailure
from adaptive_ai_workbench.domain.models import CandidateActionPack, InstalledActionPack


def validate_candidate_pack(candidate: CandidateActionPack) -> CandidateActionPack:
    try:
        return CandidateActionPack.model_validate(candidate.model_dump())
    except Exception as exc:
        raise ValidationFailure(f"Candidate pack validation failed: {exc}") from exc


def install_candidate_pack(
    candidate: CandidateActionPack,
    source: PackSource = PackSource.generated,
) -> InstalledActionPack:
    validated = validate_candidate_pack(candidate)
    try:
        return InstalledActionPack(
            schema_version=validated.schema_version,
            pack_id=validated.pack_id,
            name=validated.title,
            description=validated.summary,
            source=source,
            origin_goal=validated.goal,
            installed_at=datetime.now(timezone.utc).isoformat(),
            enabled=True,
            actions=validated.actions,
            recommended_preset_ids=[],
        )
    except Exception as exc:
        raise ValidationFailure(f"Installed pack conversion failed: {exc}") from exc
