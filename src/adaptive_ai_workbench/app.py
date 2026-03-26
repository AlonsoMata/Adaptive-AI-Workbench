import tkinter as tk

from adaptive_ai_workbench.logging_config import configure_logging
from adaptive_ai_workbench.services.workbench_service import WorkbenchService
from adaptive_ai_workbench.settings import Settings
from adaptive_ai_workbench.ui.controller import AppController
from adaptive_ai_workbench.ui.root import WorkbenchRoot
from adaptive_ai_workbench.ui.state import AppState


def run() -> None:
    settings = Settings.from_env()
    configure_logging(settings.log_level)

    service = WorkbenchService(settings=settings)
    state = AppState()
    controller = AppController(service=service, state=state)
    try:
        root = WorkbenchRoot(settings=settings, controller=controller, state=state)
    except tk.TclError as exc:
        raise SystemExit(
            "Tkinter could not start. Use a Python installation with Tcl/Tk support to run the desktop UI."
        ) from exc
    root.mainloop()
