"""Application entry point."""

from __future__ import annotations

import os as _os
import sys as _sys

# ═══ PyInstaller 打包后必须在任何 Qt 导入之前设置插件路径 ═══
# styles.py 的 __getattr__ 会在首次访问 LIGHT_STYLESHEET 时创建
# QApplication，路径矫正必须在此之前完成。
if getattr(_sys, "frozen", False):
    for _candidate in (
        _os.path.join(_sys._MEIPASS, "PySide6", "plugins"),
        _os.path.join(_sys._MEIPASS, "qt6_plugins"),
        _os.path.join(_sys._MEIPASS, "PySide6", "qt-plugins"),
    ):
        if _os.path.isdir(_os.path.join(_candidate, "platforms")):
            _os.environ["QT_PLUGIN_PATH"] = _candidate
            break

from PySide6.QtCore import QSharedMemory

from command_launcher.app import create_app
from command_launcher.ui.main_window import MainWindow

# 单实例检测的共享内存键名
_INSTANCE_KEY = "CommandLauncher_SingleInstance"


def main() -> int:
    """Start the desktop application and return the process exit code.

    Supports --tray flag for auto-start — window stays hidden, tray icon only.
    """
    start_in_tray = "--tray" in _sys.argv

    # — 单实例检测 —
    shared_mem = QSharedMemory(_INSTANCE_KEY)
    if shared_mem.attach():
        # 已有实例在运行 — 通知其恢复窗口，然后退出
        shared_mem.lock()
        shared_mem.data()[0] = 1  # 设置"恢复"信号
        shared_mem.unlock()
        shared_mem.detach()
        return 0

    if not shared_mem.create(1):
        return 0

    # 清理共享内存初始数据
    shared_mem.lock()
    shared_mem.data()[0] = 0
    shared_mem.unlock()

    app = create_app()
    window = MainWindow(shared_mem=shared_mem)
    if not start_in_tray:
        window.show()
    # 托盘图标已在 MainWindow._setup_tray 中创建，开机自启时不弹窗也可见
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
