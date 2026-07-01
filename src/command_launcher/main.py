"""Application entry point."""

from __future__ import annotations

from PySide6.QtCore import QSharedMemory

from command_launcher.app import create_app
from command_launcher.ui.main_window import MainWindow

# 单实例检测的共享内存键名
_INSTANCE_KEY = "CommandLauncher_SingleInstance"


def main() -> int:
    """Start the desktop application and return the process exit code."""
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
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
