from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from adaptive_ai_workbench.settings import Settings
from adaptive_ai_workbench.ui.background_tasks import run_background
from adaptive_ai_workbench.ui.controller import AppController
from adaptive_ai_workbench.ui.state import AppState
from adaptive_ai_workbench.ui.widgets import (
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
        self.geometry("1200x760")
        self.minsize(960, 640)

        self._build_layout()
        self.controller.bootstrap()
        self._refresh_from_state()

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=0)

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

        goal_frame, self.goal_text = build_goal_panel(self)
        goal_frame.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=(0, 6))

        sidebar_frame, self.pack_list, self.action_list, self.preset_list = build_sidebar(self)
        sidebar_frame.grid(row=1, column=1, rowspan=3, sticky="nsew", padx=(6, 12), pady=(0, 6))

        editor_frame, self.input_text, self.output_text = build_editor_panel(self)
        editor_frame.grid(row=2, column=0, sticky="nsew", padx=(12, 6), pady=(0, 6))

        inspector_frame, self.inspector_text = build_inspector(self)
        inspector_frame.grid(row=3, column=0, sticky="nsew", padx=(12, 6), pady=(0, 6))

        status_frame, self.status_text = build_status_panel(self)
        status_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=12, pady=(0, 12))

        self.pack_list.bind("<<ListboxSelect>>", self._on_pack_selected)
        self.action_list.bind("<<ListboxSelect>>", self._on_action_selected)
        self.preset_list.bind("<<ListboxSelect>>", self._on_preset_selected)

    def _on_refresh(self) -> None:
        self.controller.handle_refresh_catalog()
        self._refresh_from_state()

    def _on_generate_workflow(self) -> None:
        task = self.controller.begin_generate_workflow(
            goal_text=self._read_text_widget(self.goal_text),
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
            goal_text=self._read_text_widget(self.goal_text),
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
            goal_text=self._read_text_widget(self.goal_text),
            input_text=self._read_text_widget(self.input_text),
        )
        self._refresh_from_state()

    def _on_preset_selected(self, _: tk.Event[tk.Listbox]) -> None:
        if self._syncing:
            return
        self.controller.handle_preset_selected(
            self._get_listbox_selection(self.preset_list),
            goal_text=self._read_text_widget(self.goal_text),
            input_text=self._read_text_widget(self.input_text),
        )
        self._refresh_from_state()

    def _refresh_from_state(self) -> None:
        self._syncing = True
        try:
            self._sync_output_widget(self.output_text, self.state.output_text)
            self._sync_readonly_widget(self.inspector_text, self.state.inspector_text)
            self._sync_listbox(self.pack_list, self.state.available_packs, self.state.selected_pack)
            self._sync_listbox(self.action_list, self.state.available_actions, self.state.selected_action)
            self._sync_listbox(self.preset_list, self.state.available_presets, self.state.selected_preset)
            self._sync_readonly_widget(self.status_text, "\n".join(self.state.status_lines))
            self._sync_busy_state()
        finally:
            self._syncing = False

    def _sync_busy_state(self) -> None:
        busy = self.state.busy
        self.refresh_button.configure(state="disabled" if busy else "normal")
        self.generate_button.configure(state="disabled" if busy else "normal")
        self.install_button.configure(state="disabled" if busy else "normal")
        self.run_button.configure(state="disabled" if busy else "normal")
        self.pack_list.configure(state="disabled" if busy else "normal")
        self.action_list.configure(state="disabled" if busy else "normal")
        self.preset_list.configure(state="disabled" if busy else "normal")
        self.title(f"{self.settings.app_name} {'(Working...)' if busy else ''}".rstrip())

    @staticmethod
    def _sync_output_widget(widget: tk.Text, content: str) -> None:
        widget.delete("1.0", "end")
        widget.insert("1.0", content)

    @staticmethod
    def _sync_readonly_widget(widget: tk.Text, content: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.configure(state="disabled")

    @staticmethod
    def _sync_listbox(widget: tk.Listbox, items: list[str], selected_item: str | None) -> None:
        widget.delete(0, "end")
        selected_index = None
        for index, item in enumerate(items):
            widget.insert("end", item)
            if item == selected_item:
                selected_index = index
        if selected_index is not None:
            widget.selection_set(selected_index)
            widget.activate(selected_index)

    @staticmethod
    def _read_text_widget(widget: tk.Text) -> str:
        return widget.get("1.0", "end").rstrip()

    @staticmethod
    def _get_listbox_selection(widget: tk.Listbox) -> str | None:
        selection = widget.curselection()
        if not selection:
            return None
        return str(widget.get(selection[0]))
