from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from adaptive_ai_workbench.domain.models import ActionDefinition, CandidateActionPack
from adaptive_ai_workbench.settings import Settings
from adaptive_ai_workbench.ui.background_tasks import run_background
from adaptive_ai_workbench.ui.controller import AppController
from adaptive_ai_workbench.ui.state import AppState
from adaptive_ai_workbench.ui.widgets import (
    CandidateEditorWidgets,
    SidebarWidgets,
    build_candidate_editor,
    build_editor_panel,
    build_goal_panel,
    build_inspector,
    build_sidebar,
    build_status_panel,
)


class WorkbenchRoot(tk.Tk):
    def __init__(self, settings: Settings, controller: AppController, state: AppState) -> None:
        super().__init__()
        self.settings = settings
        self.controller = controller
        self.state = state
        self._syncing = False

        self.title(settings.app_name)
        self.geometry("1440x1020")
        self.minsize(1180, 860)

        self._build_layout()
        self.controller.bootstrap()
        self._refresh_from_state()

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=7)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=1, minsize=175)
        self.rowconfigure(2, weight=2, minsize=180)
        self.rowconfigure(3, weight=2, minsize=175)
        self.rowconfigure(4, weight=5, minsize=360)
        self.rowconfigure(5, weight=0)

        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 6))
        self.refresh_button = ttk.Button(toolbar, text="Refresh Catalog", command=self._on_refresh)
        self.refresh_button.pack(side="left")
        self.generate_button = ttk.Button(toolbar, text="Generate Workflow", command=self._on_generate_workflow)
        self.generate_button.pack(side="left", padx=(8, 0))
        self.install_button = ttk.Button(toolbar, text="Install Workflow", command=self._on_install_workflow)
        self.install_button.pack(side="left", padx=(8, 0))
        self.run_button = ttk.Button(toolbar, text="Run Action", command=self._on_run_action)
        self.run_button.pack(side="left", padx=(8, 0))
        self.clear_button = ttk.Button(toolbar, text="Clear Output", command=self._on_clear_output)
        self.clear_button.pack(side="left", padx=(8, 0))

        workflow_request_frame, self.workflow_request_text = build_goal_panel(self)
        workflow_request_frame.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=(0, 6))

        sidebar_frame, self.sidebar = build_sidebar(self)
        sidebar_frame.grid(row=1, column=1, rowspan=4, sticky="nsew", padx=(6, 12), pady=(0, 6))
        self.pack_list = self.sidebar.pack_list
        self.action_list = self.sidebar.action_list

        editor_frame, self.input_text, self.output_text = build_editor_panel(self)
        editor_frame.grid(row=2, column=0, sticky="nsew", padx=(12, 6), pady=(0, 6))

        inspector_frame, self.inspector_text = build_inspector(self)
        inspector_frame.grid(row=3, column=0, sticky="nsew", padx=(12, 6), pady=(0, 6))

        candidate_editor_frame, self.candidate_editor = build_candidate_editor(self)
        candidate_editor_frame.grid(row=4, column=0, sticky="nsew", padx=(12, 6), pady=(0, 6))

        status_frame, self.status_text = build_status_panel(self)
        status_frame.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=12, pady=(0, 12))

        self.pack_list.bind("<<ListboxSelect>>", self._on_pack_selected)
        self.action_list.bind("<<ListboxSelect>>", self._on_action_selected)
        self.candidate_editor.action_list.bind("<<ListboxSelect>>", self._on_candidate_action_selected)
        self.candidate_editor.apply_button.configure(command=self._on_apply_candidate_edits)
        self.candidate_editor.remove_button.configure(command=self._on_remove_candidate_action)

        for combo in (
            self.sidebar.tone_combo,
            self.sidebar.length_combo,
            self.sidebar.language_combo,
            self.sidebar.style_combo,
            self.sidebar.format_combo,
            self.sidebar.strictness_combo,
        ):
            combo.bind("<<ComboboxSelected>>", self._on_controls_changed)

    def _on_refresh(self) -> None:
        self.controller.handle_refresh_catalog()
        self._refresh_from_state()

    def _on_generate_workflow(self) -> None:
        task = self.controller.begin_generate_workflow(
            goal_text=self._read_text_widget(self.workflow_request_text),
        )
        self._refresh_from_state()
        if task is None:
            return

        run_background(
            root=self,
            task=task,
            on_success=self._on_generate_workflow_success,
            on_error=self._on_generate_workflow_error,
        )

    def _on_generate_workflow_success(self, candidate: object) -> None:
        self.controller.finish_generate_workflow(candidate)
        self._refresh_from_state()

    def _on_generate_workflow_error(self, error: Exception) -> None:
        self.controller.fail_generate_workflow(error)
        self._refresh_from_state()

    def _on_install_workflow(self) -> None:
        self.controller.handle_install_candidate()
        self._refresh_from_state()

    def _on_run_action(self) -> None:
        task = self.controller.begin_run_action(
            goal_text=self._read_text_widget(self.workflow_request_text),
            input_text=self._read_text_widget(self.input_text),
        )
        self._refresh_from_state()
        if task is None:
            return

        run_background(
            root=self,
            task=task,
            on_success=self._on_run_action_success,
            on_error=self._on_run_action_error,
        )

    def _on_run_action_success(self, result: object) -> None:
        self.controller.finish_run_action(result)
        self._refresh_from_state()

    def _on_run_action_error(self, error: Exception) -> None:
        self.controller.fail_run_action(error)
        self._refresh_from_state()

    def _on_clear_output(self) -> None:
        self.controller.handle_clear_output()
        self._refresh_from_state()

    def _on_pack_selected(self, _: tk.Event[tk.Listbox]) -> None:
        if self._syncing:
            return
        self.controller.handle_pack_selected(self._get_listbox_selection(self.pack_list))
        self._refresh_from_state()

    def _on_action_selected(self, _: tk.Event[tk.Listbox]) -> None:
        if self._syncing:
            return
        self.controller.handle_action_selected(
            self._get_listbox_selection(self.action_list),
            goal_text=self._read_text_widget(self.workflow_request_text),
            input_text=self._read_text_widget(self.input_text),
        )
        self._refresh_from_state()

    def _on_controls_changed(self, _: tk.Event[ttk.Combobox]) -> None:
        if self._syncing:
            return
        self.controller.handle_response_controls_changed(
            tone=self.sidebar.tone_combo.get(),
            length=self.sidebar.length_combo.get(),
            language=self.sidebar.language_combo.get(),
            output_style=self.sidebar.style_combo.get(),
            format=self.sidebar.format_combo.get(),
            strictness=self.sidebar.strictness_combo.get(),
            goal_text=self._read_text_widget(self.workflow_request_text),
            input_text=self._read_text_widget(self.input_text),
        )
        self._refresh_from_state()

    def _on_candidate_action_selected(self, _: tk.Event[tk.Listbox]) -> None:
        if self._syncing:
            return
        self.controller.handle_candidate_action_selected(
            self._get_listbox_selection(self.candidate_editor.action_list)
        )
        self._refresh_from_state()

    def _on_apply_candidate_edits(self) -> None:
        self.controller.handle_apply_candidate_edits(
            title=self.candidate_editor.title_entry.get(),
            summary=self._read_text_widget(self.candidate_editor.summary_text),
            reasoning=self._read_text_widget(self.candidate_editor.reasoning_text),
            recommended_preset_ids_text=self.candidate_editor.recommended_presets_entry.get(),
            action_name=self.candidate_editor.action_name_entry.get(),
            action_description=self._read_text_widget(self.candidate_editor.action_description_text),
            action_rationale=self._read_text_widget(self.candidate_editor.action_rationale_text),
            action_default_preset_id=self.candidate_editor.action_default_preset_entry.get(),
            action_enabled=self.candidate_editor.action_enabled_var.get(),
        )
        self._refresh_from_state()

    def _on_remove_candidate_action(self) -> None:
        self.controller.handle_remove_candidate_action()
        self._refresh_from_state()

    def _refresh_from_state(self) -> None:
        self._syncing = True
        try:
            self._sync_output_widget(self.output_text, self.state.output_text)
            self._sync_readonly_widget(self.inspector_text, self.state.inspector_text)
            self._sync_listbox(self.pack_list, self.state.available_packs, self.state.selected_pack)
            self._sync_listbox(self.action_list, self.state.available_actions, self.state.selected_action)
            self._sync_candidate_editor()
            self._sync_controls()
            self._sync_selection_details()
            self._sync_readonly_widget(self.status_text, "\n".join(self.state.status_lines))
            self._sync_busy_state()
        finally:
            self._syncing = False

    def _sync_candidate_editor(self) -> None:
        candidate = self.state.candidate_pack
        selected_action = self._get_selected_candidate_action(candidate)

        self._sync_entry_widget(self.candidate_editor.title_entry, candidate.title if candidate else "")
        self._sync_text_widget(self.candidate_editor.summary_text, candidate.summary if candidate else "")
        self._sync_text_widget(self.candidate_editor.reasoning_text, candidate.reasoning if candidate else "")
        self._sync_entry_widget(
            self.candidate_editor.recommended_presets_entry,
            ", ".join(candidate.recommended_preset_ids) if candidate else "",
        )
        self._sync_listbox(
            self.candidate_editor.action_list,
            self.state.available_candidate_actions,
            self.state.selected_candidate_action,
        )
        self.candidate_editor.action_enabled_var.set(selected_action.enabled if selected_action else False)
        self._sync_entry_widget(self.candidate_editor.action_name_entry, selected_action.name if selected_action else "")
        self._sync_text_widget(
            self.candidate_editor.action_description_text,
            selected_action.description if selected_action else "",
        )
        self._sync_text_widget(
            self.candidate_editor.action_rationale_text,
            selected_action.rationale if selected_action else "",
        )
        self._sync_entry_widget(
            self.candidate_editor.action_default_preset_entry,
            selected_action.default_preset_id or "" if selected_action else "",
        )

    def _sync_controls(self) -> None:
        self._sync_combobox(self.sidebar.tone_combo, self.state.available_tones, self.state.selected_tone)
        self._sync_combobox(self.sidebar.length_combo, self.state.available_lengths, self.state.selected_length)
        self._sync_combobox(self.sidebar.language_combo, self.state.available_languages, self.state.selected_language)
        self._sync_combobox(self.sidebar.style_combo, self.state.available_styles, self.state.selected_style)
        self._sync_combobox(self.sidebar.format_combo, self.state.available_formats, self.state.selected_format)
        self._sync_combobox(
            self.sidebar.strictness_combo,
            self.state.available_strictness_levels,
            self.state.selected_strictness,
        )

    def _sync_selection_details(self) -> None:
        self._sync_label(
            self.sidebar.pack_detail_label,
            self._format_selection_detail("Selected pack", self.state.selected_pack),
        )
        self._sync_label(
            self.sidebar.action_detail_label,
            self._format_selection_detail("Selected action", self.state.selected_action),
        )
        self._sync_label(
            self.sidebar.controls_detail_label,
            (
                "Current controls: "
                f"tone={self.state.selected_tone}, language={self.state.selected_language}, "
                f"style={self.state.selected_style}, length={self.state.selected_length}, "
                f"format={self.state.selected_format}, strictness={self.state.selected_strictness}"
            ),
        )

        candidate_action = self._get_selected_candidate_action(self.state.candidate_pack)
        if candidate_action is None:
            detail = "No candidate action selected"
        else:
            detail = f"Selected candidate action: {candidate_action.name} ({candidate_action.action_id})"
        self._sync_label(self.candidate_editor.action_detail_label, detail)

    def _sync_busy_state(self) -> None:
        busy = self.state.busy
        candidate_active = self.state.candidate_pack is not None and not busy
        candidate_action_active = candidate_active and self.state.selected_candidate_action is not None

        self.refresh_button.configure(state="disabled" if busy else "normal")
        self.generate_button.configure(state="disabled" if busy else "normal")
        self.install_button.configure(state="disabled" if busy or self.state.candidate_pack is None else "normal")
        self.run_button.configure(state="disabled" if busy else "normal")
        self.pack_list.configure(state="disabled" if busy else "normal")
        self.action_list.configure(state="disabled" if busy else "normal")

        for combo in (
            self.sidebar.tone_combo,
            self.sidebar.length_combo,
            self.sidebar.language_combo,
            self.sidebar.style_combo,
            self.sidebar.format_combo,
            self.sidebar.strictness_combo,
        ):
            combo.configure(state="disabled" if busy else "readonly")

        self.candidate_editor.title_entry.configure(state="normal" if candidate_active else "disabled")
        self.candidate_editor.recommended_presets_entry.configure(state="normal" if candidate_active else "disabled")
        self.candidate_editor.action_list.configure(state="normal" if candidate_active else "disabled")
        self.candidate_editor.action_enabled_check.configure(state="normal" if candidate_action_active else "disabled")
        self.candidate_editor.action_name_entry.configure(state="normal" if candidate_action_active else "disabled")
        self.candidate_editor.action_default_preset_entry.configure(state="normal" if candidate_action_active else "disabled")
        self.candidate_editor.apply_button.configure(state="normal" if candidate_action_active else "disabled")
        self.candidate_editor.remove_button.configure(state="normal" if candidate_action_active else "disabled")
        self._set_text_widget_state(self.candidate_editor.summary_text, candidate_active)
        self._set_text_widget_state(self.candidate_editor.reasoning_text, candidate_active)
        self._set_text_widget_state(self.candidate_editor.action_description_text, candidate_action_active)
        self._set_text_widget_state(self.candidate_editor.action_rationale_text, candidate_action_active)

        self.title(f"{self.settings.app_name} {'(Working...)' if busy else ''}".rstrip())

    def _get_selected_candidate_action(self, candidate: CandidateActionPack | None) -> ActionDefinition | None:
        if candidate is None or self.state.selected_candidate_action is None:
            return None
        for action in candidate.actions:
            if action.action_id == self.state.selected_candidate_action:
                return action
        return None

    @staticmethod
    def _sync_output_widget(widget: tk.Text, content: str) -> None:
        widget.delete("1.0", "end")
        widget.insert("1.0", content)

    @staticmethod
    def _sync_text_widget(widget: tk.Text, content: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)

    @staticmethod
    def _sync_readonly_widget(widget: tk.Text, content: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.configure(state="disabled")

    @staticmethod
    def _set_text_widget_state(widget: tk.Text, enabled: bool) -> None:
        widget.configure(state="normal" if enabled else "disabled")

    @staticmethod
    def _sync_entry_widget(widget: ttk.Entry, content: str) -> None:
        widget.configure(state="normal")
        widget.delete(0, "end")
        widget.insert(0, content)

    @staticmethod
    def _sync_label(widget: ttk.Label, content: str) -> None:
        widget.configure(text=content)

    @staticmethod
    def _sync_listbox(widget: tk.Listbox, items: list[str], selected_item: str | None) -> None:
        widget.delete(0, "end")
        widget.selection_clear(0, "end")
        selected_index = None
        for index, item in enumerate(items):
            widget.insert("end", item)
            if item == selected_item:
                selected_index = index
        if selected_index is not None:
            widget.selection_set(selected_index)
            widget.activate(selected_index)
            widget.see(selected_index)

    @staticmethod
    def _sync_combobox(widget: ttk.Combobox, values: list[str], selected_value: str) -> None:
        widget.configure(values=values)
        if selected_value in values:
            widget.set(selected_value)
        elif values:
            widget.set(values[0])
        else:
            widget.set("")

    @staticmethod
    def _format_selection_detail(label: str, value: str | None) -> str:
        return f"{label}: {value}" if value else f"{label}: nothing selected"

    @staticmethod
    def _read_text_widget(widget: tk.Text) -> str:
        return widget.get("1.0", "end").rstrip()

    @staticmethod
    def _get_listbox_selection(widget: tk.Listbox) -> str | None:
        selection = widget.curselection()
        if not selection:
            return None
        return str(widget.get(selection[0]))
