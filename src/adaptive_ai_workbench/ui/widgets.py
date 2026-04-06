from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk


@dataclass(slots=True)
class SidebarWidgets:
    pack_list: tk.Listbox
    pack_detail_label: ttk.Label
    action_list: tk.Listbox
    action_detail_label: ttk.Label
    preset_list: tk.Listbox
    preset_detail_label: ttk.Label


@dataclass(slots=True)
class CandidateEditorWidgets:
    title_entry: ttk.Entry
    summary_text: tk.Text
    reasoning_text: tk.Text
    recommended_presets_entry: ttk.Entry
    action_list: tk.Listbox
    action_detail_label: ttk.Label
    action_enabled_var: tk.BooleanVar
    action_enabled_check: ttk.Checkbutton
    action_name_entry: ttk.Entry
    action_description_text: tk.Text
    action_rationale_text: tk.Text
    action_default_preset_entry: ttk.Entry
    apply_button: ttk.Button
    remove_button: ttk.Button


GOAL_HELP_WRAP = 980
EXECUTION_HELP_WRAP = 460
SIDEBAR_DETAIL_WRAP = 255
CANDIDATE_ACTION_DETAIL_WRAP = 520
ENABLED_HELP_WRAP = 520


def build_goal_panel(parent: ttk.Frame) -> tuple[ttk.Frame, tk.Text]:
    frame = ttk.LabelFrame(parent, text="New Workflow Request")
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(2, weight=1)

    heading = ttk.Label(
        frame,
        text="Describe the workflow pack you want to generate",
        font=("Segoe UI", 11, "bold"),
        justify="left",
    )
    heading.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 2))

    helper = ttk.Label(
        frame,
        text=(
            "Examples: 'Help me draft and reply to professional emails' or "
            "'Create a pack to translate technical documentation from English to Spanish.' "
            "Then click Generate Workflow."
        ),
        wraplength=GOAL_HELP_WRAP,
        justify="left",
    )
    helper.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))

    text = tk.Text(frame, height=6, wrap="word")
    text.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
    return frame, text


def build_editor_panel(parent: ttk.Frame) -> tuple[ttk.Frame, tk.Text, tk.Text]:
    frame = ttk.LabelFrame(parent, text="Installed Action Execution")
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)
    frame.rowconfigure(2, weight=1)

    ttk.Label(frame, text="Input for Installed Action").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 0))
    ttk.Label(frame, text="Output").grid(row=0, column=1, sticky="w", padx=8, pady=(8, 0))

    input_help = ttk.Label(
        frame,
        text="Use this input only after selecting an installed workflow action to run.",
        wraplength=EXECUTION_HELP_WRAP,
        justify="left",
    )
    input_help.grid(row=1, column=0, sticky="w", padx=8, pady=(2, 0))

    output_help = ttk.Label(
        frame,
        text="Execution results from the selected installed action appear here.",
        wraplength=EXECUTION_HELP_WRAP,
        justify="left",
    )
    output_help.grid(row=1, column=1, sticky="w", padx=8, pady=(2, 0))

    input_text = tk.Text(frame, height=8, wrap="word")
    output_text = tk.Text(frame, height=8, wrap="word")
    input_text.grid(row=2, column=0, sticky="nsew", padx=(8, 4), pady=8)
    output_text.grid(row=2, column=1, sticky="nsew", padx=(4, 8), pady=8)
    return frame, input_text, output_text


def _build_selection_detail(parent: ttk.Frame, row: int) -> ttk.Label:
    label = ttk.Label(parent, text="Nothing selected", justify="left", wraplength=SIDEBAR_DETAIL_WRAP)
    label.grid(row=row, column=0, sticky="ew", padx=8, pady=(0, 8))
    return label


def build_sidebar(parent: ttk.Frame) -> tuple[ttk.Frame, SidebarWidgets]:
    frame = ttk.LabelFrame(parent, text="Installed Workflow Catalog")
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(1, weight=3)
    frame.rowconfigure(4, weight=3)
    frame.rowconfigure(7, weight=2)

    ttk.Label(frame, text="Packs").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 0))
    packs = tk.Listbox(frame, exportselection=False, height=7, width=28, activestyle="dotbox")
    packs.grid(row=1, column=0, sticky="nsew", padx=8, pady=(4, 2))
    pack_detail_label = _build_selection_detail(frame, 2)

    ttk.Label(frame, text="Actions").grid(row=3, column=0, sticky="w", padx=8, pady=(0, 0))
    actions = tk.Listbox(frame, exportselection=False, height=7, width=28, activestyle="dotbox")
    actions.grid(row=4, column=0, sticky="nsew", padx=8, pady=(4, 2))
    action_detail_label = _build_selection_detail(frame, 5)

    ttk.Label(frame, text="Presets").grid(row=6, column=0, sticky="w", padx=8, pady=(0, 0))
    presets = tk.Listbox(frame, exportselection=False, height=5, width=28, activestyle="dotbox")
    presets.grid(row=7, column=0, sticky="nsew", padx=8, pady=(4, 2))
    preset_detail_label = _build_selection_detail(frame, 8)

    widgets = SidebarWidgets(
        pack_list=packs,
        pack_detail_label=pack_detail_label,
        action_list=actions,
        action_detail_label=action_detail_label,
        preset_list=presets,
        preset_detail_label=preset_detail_label,
    )
    return frame, widgets


def build_inspector(parent: ttk.Frame) -> tuple[ttk.Frame, tk.Text]:
    frame = ttk.LabelFrame(parent, text="Inspector")
    text = tk.Text(frame, height=10, wrap="word")
    text.insert(
        "1.0",
        "Start in New Workflow Request, click Generate Workflow, review the candidate pack, install it, and then use Installed Action Execution to run the installed actions.",
    )
    text.configure(state="disabled")
    text.pack(fill="both", expand=True, padx=8, pady=8)
    return frame, text


def build_candidate_editor(parent: ttk.Frame) -> tuple[ttk.Frame, CandidateEditorWidgets]:
    frame = ttk.LabelFrame(parent, text="Candidate Review Editor")
    frame.columnconfigure(0, weight=5)
    frame.columnconfigure(1, weight=6)
    frame.rowconfigure(0, weight=1)
    frame.rowconfigure(1, weight=0)

    metadata_frame = ttk.Frame(frame)
    metadata_frame.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
    metadata_frame.columnconfigure(0, weight=0)
    metadata_frame.columnconfigure(1, weight=1)
    metadata_frame.rowconfigure(2, weight=2)
    metadata_frame.rowconfigure(3, weight=3)

    ttk.Label(metadata_frame, text="Title").grid(row=0, column=0, sticky="w")
    title_entry = ttk.Entry(metadata_frame)
    title_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=(0, 6))

    ttk.Label(metadata_frame, text="Recommended Presets").grid(row=1, column=0, sticky="w")
    recommended_presets_entry = ttk.Entry(metadata_frame)
    recommended_presets_entry.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(0, 6))

    ttk.Label(metadata_frame, text="Summary").grid(row=2, column=0, sticky="nw")
    summary_text = tk.Text(metadata_frame, height=6, wrap="word")
    summary_text.grid(row=2, column=1, sticky="nsew", padx=(8, 0), pady=(0, 6))

    ttk.Label(metadata_frame, text="Reasoning").grid(row=3, column=0, sticky="nw")
    reasoning_text = tk.Text(metadata_frame, height=8, wrap="word")
    reasoning_text.grid(row=3, column=1, sticky="nsew", padx=(8, 0), pady=(0, 6))

    action_frame = ttk.Frame(frame)
    action_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
    action_frame.columnconfigure(0, weight=0)
    action_frame.columnconfigure(1, weight=1)
    action_frame.rowconfigure(1, weight=2)
    action_frame.rowconfigure(7, weight=2)
    action_frame.rowconfigure(8, weight=3)

    ttk.Label(action_frame, text="Candidate Actions").grid(row=0, column=0, columnspan=2, sticky="w")
    action_list = tk.Listbox(action_frame, exportselection=False, height=10, width=34, activestyle="dotbox")
    action_list.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(4, 2))

    action_detail_label = ttk.Label(
        action_frame,
        text="No candidate action selected",
        justify="left",
        wraplength=CANDIDATE_ACTION_DETAIL_WRAP,
    )
    action_detail_label.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 8))

    action_enabled_var = tk.BooleanVar(value=True)
    action_enabled_check = ttk.Checkbutton(
        action_frame,
        text="Include in installed workflow",
        variable=action_enabled_var,
    )
    action_enabled_check.grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 2))

    enabled_help = ttk.Label(
        action_frame,
        text="Unchecked actions remain in the candidate review copy but install as disabled.",
        justify="left",
        wraplength=ENABLED_HELP_WRAP,
    )
    enabled_help.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 8))

    ttk.Label(action_frame, text="Action Name").grid(row=5, column=0, sticky="w")
    action_name_entry = ttk.Entry(action_frame)
    action_name_entry.grid(row=5, column=1, sticky="ew", padx=(8, 0), pady=(0, 6))

    ttk.Label(action_frame, text="Default Preset").grid(row=6, column=0, sticky="w")
    action_default_preset_entry = ttk.Entry(action_frame)
    action_default_preset_entry.grid(row=6, column=1, sticky="ew", padx=(8, 0), pady=(0, 6))

    ttk.Label(action_frame, text="Description").grid(row=7, column=0, sticky="nw")
    action_description_text = tk.Text(action_frame, height=6, wrap="word")
    action_description_text.grid(row=7, column=1, sticky="nsew", padx=(8, 0), pady=(0, 6))

    ttk.Label(action_frame, text="Rationale").grid(row=8, column=0, sticky="nw")
    action_rationale_text = tk.Text(action_frame, height=8, wrap="word")
    action_rationale_text.grid(row=8, column=1, sticky="nsew", padx=(8, 0), pady=(0, 6))

    button_row = ttk.Frame(frame)
    button_row.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
    apply_button = ttk.Button(button_row, text="Apply Candidate Edits")
    apply_button.pack(side="left")
    remove_button = ttk.Button(button_row, text="Remove Candidate Action")
    remove_button.pack(side="left", padx=(8, 0))

    widgets = CandidateEditorWidgets(
        title_entry=title_entry,
        summary_text=summary_text,
        reasoning_text=reasoning_text,
        recommended_presets_entry=recommended_presets_entry,
        action_list=action_list,
        action_detail_label=action_detail_label,
        action_enabled_var=action_enabled_var,
        action_enabled_check=action_enabled_check,
        action_name_entry=action_name_entry,
        action_description_text=action_description_text,
        action_rationale_text=action_rationale_text,
        action_default_preset_entry=action_default_preset_entry,
        apply_button=apply_button,
        remove_button=remove_button,
    )
    return frame, widgets


def build_status_panel(parent: ttk.Frame) -> tuple[ttk.Frame, tk.Text]:
    frame = ttk.LabelFrame(parent, text="Status")
    text = tk.Text(frame, height=4, wrap="word")
    text.configure(state="disabled")
    text.pack(fill="both", expand=True, padx=8, pady=8)
    return frame, text
