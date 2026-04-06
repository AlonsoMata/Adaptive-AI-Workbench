from __future__ import annotations

from dataclasses import dataclass, field

from adaptive_ai_workbench.domain.models import CandidateActionPack


@dataclass(slots=True)
class AppState:
    goal_text: str = ""
    input_text: str = ""
    output_text: str = ""
    inspector_text: str = ""
    status_lines: list[str] = field(default_factory=list)
    available_packs: list[str] = field(default_factory=list)
    available_actions: list[str] = field(default_factory=list)
    available_candidate_actions: list[str] = field(default_factory=list)
    available_presets: list[str] = field(default_factory=list)
    selected_pack: str | None = None
    selected_action: str | None = None
    selected_preset: str | None = None
    candidate_pack: CandidateActionPack | None = None
    selected_candidate_action: str | None = None
    busy: bool = False