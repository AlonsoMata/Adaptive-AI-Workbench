from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def build_goal_panel(parent: ttk.Frame) -> tuple[ttk.Frame, tk.Text]:
    frame = ttk.LabelFrame(parent, text="Goal")
    text = tk.Text(frame, height=4, wrap="word")
    text.pack(fill="both", expand=True, padx=8, pady=8)
    return frame, text


def build_editor_panel(parent: ttk.Frame) -> tuple[ttk.Frame, tk.Text, tk.Text]:
    frame = ttk.Frame(parent)
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)
    frame.rowconfigure(1, weight=1)

    ttk.Label(frame, text="Input").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 0))
    ttk.Label(frame, text="Output").grid(row=0, column=1, sticky="w", padx=8, pady=(8, 0))

    input_text = tk.Text(frame, wrap="word")
    output_text = tk.Text(frame, wrap="word")
    input_text.grid(row=1, column=0, sticky="nsew", padx=(8, 4), pady=8)
    output_text.grid(row=1, column=1, sticky="nsew", padx=(4, 8), pady=8)
    return frame, input_text, output_text


def build_sidebar(parent: ttk.Frame) -> tuple[ttk.Frame, tk.Listbox, tk.Listbox, tk.Listbox]:
    frame = ttk.LabelFrame(parent, text="Installed Workflow Catalog")
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(1, weight=1)
    frame.rowconfigure(3, weight=1)
    frame.rowconfigure(5, weight=1)

    ttk.Label(frame, text="Packs").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 0))
    packs = tk.Listbox(frame, exportselection=False, height=8)
    packs.grid(row=1, column=0, sticky="nsew", padx=8, pady=(4, 8))

    ttk.Label(frame, text="Actions").grid(row=2, column=0, sticky="w", padx=8, pady=(0, 0))
    actions = tk.Listbox(frame, exportselection=False, height=8)
    actions.grid(row=3, column=0, sticky="nsew", padx=8, pady=(4, 8))

    ttk.Label(frame, text="Presets").grid(row=4, column=0, sticky="w", padx=8, pady=(0, 0))
    presets = tk.Listbox(frame, exportselection=False, height=6)
    presets.grid(row=5, column=0, sticky="nsew", padx=8, pady=(4, 8))
    return frame, packs, actions, presets


def build_inspector(parent: ttk.Frame) -> tuple[ttk.Frame, tk.Text]:
    frame = ttk.LabelFrame(parent, text="Inspector")
    text = tk.Text(frame, height=8, wrap="word")
    text.insert(
        "1.0",
        "Describe a goal and click Generate Workflow to preview a candidate pack, or select an installed pack to inspect its actions.",
    )
    text.configure(state="disabled")
    text.pack(fill="both", expand=True, padx=8, pady=8)
    return frame, text


def build_status_panel(parent: ttk.Frame) -> tuple[ttk.Frame, tk.Text]:
    frame = ttk.LabelFrame(parent, text="Status")
    text = tk.Text(frame, height=6, wrap="word")
    text.configure(state="disabled")
    text.pack(fill="both", expand=True, padx=8, pady=8)
    return frame, text