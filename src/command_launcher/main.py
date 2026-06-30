"""Application entry point."""

from __future__ import annotations

from command_launcher.app import create_app
from command_launcher.ui.main_window import MainWindow


def main() -> int:
    """Start the desktop application and return the process exit code."""
    app = create_app()
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
