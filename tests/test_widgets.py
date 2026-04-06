import tkinter as tk

import pytest

from adaptive_ai_workbench.ui.widgets import build_candidate_editor, build_sidebar


def test_candidate_editor_allocates_weight_to_visible_action_list_row() -> None:
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk is unavailable in this environment: {exc}")

    root.withdraw()
    try:
        frame, widgets = build_candidate_editor(root)
        frame.update_idletasks()

        assert int(frame.grid_rowconfigure(0)["weight"]) == 1
        assert int(frame.grid_rowconfigure(1)["weight"]) == 0
        assert int(frame.grid_columnconfigure(0)["weight"]) == 5
        assert int(frame.grid_columnconfigure(1)["weight"]) == 6

        action_frame = widgets.action_list.master
        assert int(action_frame.grid_rowconfigure(1)["weight"]) == 2
        assert int(action_frame.grid_rowconfigure(7)["weight"]) == 2
        assert int(action_frame.grid_rowconfigure(8)["weight"]) == 3
        assert int(action_frame.grid_columnconfigure(1)["weight"]) == 1
        assert widgets.action_enabled_check.cget("text") == "Include in installed workflow"
        assert widgets.action_list.cget("height") == 10
        assert widgets.action_description_text.cget("height") == 6
        assert widgets.action_rationale_text.cget("height") == 8
    finally:
        root.destroy()


def test_sidebar_exposes_detail_labels_for_long_selections() -> None:
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk is unavailable in this environment: {exc}")

    root.withdraw()
    try:
        frame, widgets = build_sidebar(root)
        frame.update_idletasks()

        assert widgets.pack_detail_label.cget("text") == "Nothing selected"
        assert widgets.action_detail_label.cget("text") == "Nothing selected"
        assert widgets.preset_detail_label.cget("text") == "Nothing selected"
        assert widgets.pack_list.cget("width") == 28
        assert widgets.action_list.cget("width") == 28
        assert widgets.preset_list.cget("width") == 28
    finally:
        root.destroy()
