"""Qt application setup."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from command_launcher.ui.styles import LIGHT_STYLESHEET


def create_app(argv: list[str] | None = None) -> QApplication:
    """Create and configure the Qt application instance.

    Args:
        argv: Optional command line arguments for Qt.

    Returns:
        Configured QApplication instance.
    """
    app = QApplication(argv or sys.argv)
    app.setApplicationName("Project Launcher")
    app.setStyleSheet(LIGHT_STYLESHEET)
    return app
