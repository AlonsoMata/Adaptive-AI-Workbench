from __future__ import annotations

import tkinter as tk
from threading import Thread
from typing import Any, Callable


def run_background(
    root: tk.Misc,
    task: Callable[[], Any],
    on_success: Callable[[Any], None],
    on_error: Callable[[Exception], None],
) -> None:
    def runner() -> None:
        try:
            result = task()
        except Exception as exc:
            root.after(0, lambda error=exc: on_error(error))
            return
        root.after(0, lambda: on_success(result))

    Thread(target=runner, daemon=True).start()
