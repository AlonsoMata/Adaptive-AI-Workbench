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
    available_tones: list[str] = field(default_factory=list)
    available_lengths: list[str] = field(default_factory=list)
    available_languages: list[str] = field(default_factory=list)
    available_styles: list[str] = field(default_factory=list)
    available_formats: list[str] = field(default_factory=list)
    available_strictness_levels: list[str] = field(default_factory=list)
    selected_pack: str | None = None
    selected_action: str | None = None
    selected_tone: str = "professional"
    selected_length: str = "medium"
    selected_language: str = "en"
    selected_style: str = "clear"
    selected_format: str = "paragraph"
    selected_strictness: str = "medium"
    candidate_pack: CandidateActionPack | None = None
    selected_candidate_action: str | None = None
    busy: bool = False
