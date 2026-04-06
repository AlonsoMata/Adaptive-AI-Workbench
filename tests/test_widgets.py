import tkinter as tk

import pytest

from adaptive_ai_workbench.ui.widgets import build_candidate_editor


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

        action_frame = widgets.action_list.master
        assert int(action_frame.grid_rowconfigure(1)["weight"]) == 1
        assert int(action_frame.grid_columnconfigure(1)["weight"]) == 1
    finally:
        root.destroy()