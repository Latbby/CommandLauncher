"""Qt application setup."""

from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from command_launcher.resources import app_icon_path
from command_launcher.ui.styles import LIGHT_STYLESHEET


def create_app(argv: list[str] | None = None) -> QApplication:
    """Create and configure the Qt application instance.

    Args:
        argv: Optional command line arguments for Qt.

    Returns:
        Configured QApplication instance.
    """
    app = QApplication(argv or sys.argv)
    app.setApplicationName("命令启动器")
    icon_path = app_icon_path()
    if icon_path.exists():
        # 设置应用级图标，供任务栏、窗口和系统对话框复用。
        app.setWindowIcon(QIcon(str(icon_path)))
    app.setStyleSheet(LIGHT_STYLESHEET)
    return app
