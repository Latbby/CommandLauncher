"""Application resource path helpers."""

from __future__ import annotations

import sys
from pathlib import Path


def resource_root() -> Path:
    """Return the directory that contains bundled application resources.

    Returns:
        Resource root path for both source checkout and PyInstaller runtime.
    """
    # PyInstaller 解包运行时会把 --add-data 文件放在 _MEIPASS 目录下。
    pyinstaller_root = getattr(sys, "_MEIPASS", None)
    if pyinstaller_root:
        return Path(pyinstaller_root)

    return Path(__file__).resolve().parents[2]


def app_icon_path() -> Path:
    """Return the application icon path.

    Returns:
        Path to the ico file used by Qt windows and PyInstaller packaging.
    """
    return resource_root() / "assets" / "icon.ico"
