# Project Launcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows-only Python + PySide6 project launcher that saves project directories and opens `cmd`, PowerShell, Explorer, plus global and project-specific custom commands.

**Architecture:** Core behavior lives in small testable modules: models, config persistence, and command launching. The PySide6 UI is a thin layer that calls those modules and persists changes through `ConfigStore`.

**Tech Stack:** Python 3.11+, PySide6, pytest, PyInstaller.

---

## File Structure

- Create `pyproject.toml`: package metadata, dependencies, pytest config, console script.
- Create `README.md`: setup, run, test, and package commands.
- Create `src/command_launcher/models.py`: dataclasses for commands, projects, and app config.
- Create `src/command_launcher/config_store.py`: JSON config loading, saving, duplicate path handling, broken config recovery.
- Create `src/command_launcher/command_runner.py`: command argument construction and external process launching.
- Create `src/command_launcher/app.py`: Qt application factory.
- Create `src/command_launcher/main.py`: executable entry point.
- Create `src/command_launcher/ui/main_window.py`: two-column main window and UI event wiring.
- Create `src/command_launcher/ui/dialogs.py`: command edit dialog.
- Create `src/command_launcher/ui/styles.py`: light modern stylesheet.
- Create `tests/test_models.py`: model behavior.
- Create `tests/test_config_store.py`: persistence behavior.
- Create `tests/test_command_runner.py`: command construction and launch behavior.

## Task 1: Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/command_launcher/__init__.py`
- Create: `src/command_launcher/main.py`
- Create: `tests/test_imports.py`

- [ ] **Step 1: Write failing import test**

Create `tests/test_imports.py`:

```python
def test_package_imports():
    import command_launcher

    assert command_launcher.__version__ == "0.1.0"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_imports.py -v
```

Expected: FAIL because `command_launcher` does not exist.

- [ ] **Step 3: Add minimal package skeleton**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "command-launcher"
version = "0.1.0"
description = "Windows project launcher desktop utility"
requires-python = ">=3.11"
dependencies = [
  "PySide6>=6.7",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "pyinstaller>=6.0",
]

[project.scripts]
command-launcher = "command_launcher.main:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

Create `src/command_launcher/__init__.py`:

```python
"""Project Launcher package."""

__version__ = "0.1.0"
```

Create `src/command_launcher/main.py`:

```python
"""Application entry point."""


def main() -> int:
    """Start the desktop application and return the process exit code."""
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Create `README.md`:

```markdown
# Project Launcher

Windows project launcher built with Python and PySide6.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m command_launcher.main
```

## Packaging

```bash
pyinstaller --onedir --name CommandLauncher src/command_launcher/main.py
```
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/test_imports.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml README.md src/command_launcher/__init__.py src/command_launcher/main.py tests/test_imports.py
git commit -m "chore: add python project skeleton"
```

## Task 2: Data Models

**Files:**
- Create: `src/command_launcher/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing model tests**

Create `tests/test_models.py`:

```python
from command_launcher.models import AppConfig, LaunchCommand, Project


def test_project_uses_directory_name_as_default_name():
    project = Project.from_path(r"D:\work\command-launcher")

    assert project.name == "command-launcher"
    assert project.path == r"D:\work\command-launcher"
    assert project.commands == []


def test_config_selects_existing_project_for_duplicate_path():
    config = AppConfig()
    first = config.add_project(r"D:\work\command-launcher")
    second = config.add_project(r"D:\work\command-launcher\\")

    assert first.id == second.id
    assert len(config.projects) == 1
    assert config.last_selected_project_id == first.id


def test_launch_command_rejects_empty_values():
    assert LaunchCommand.is_valid("VS Code", "code .")
    assert not LaunchCommand.is_valid("", "code .")
    assert not LaunchCommand.is_valid("VS Code", "")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_models.py -v
```

Expected: FAIL because `command_launcher.models` does not exist.

- [ ] **Step 3: Implement models**

Create `src/command_launcher/models.py`:

```python
"""Data models for projects, commands, and persisted application config."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4


def _new_id() -> str:
    """Create a stable string id for persisted model objects."""
    return str(uuid4())


def normalize_path(path: str) -> str:
    """Normalize a project path for duplicate comparison and storage."""
    return str(Path(path).expanduser()).rstrip("\\/")


@dataclass
class LaunchCommand:
    """User-defined launch command.

    Args:
        name: Display name shown in the command list.
        command: Command text executed from the selected project directory.
        id: Stable persisted command id.
    """

    name: str
    command: str
    id: str = field(default_factory=_new_id)

    @staticmethod
    def is_valid(name: str, command: str) -> bool:
        """Return whether command values are valid for saving."""
        return bool(name.strip()) and bool(command.strip())

    def to_dict(self) -> dict[str, str]:
        """Serialize the command to JSON-compatible data."""
        return {"id": self.id, "name": self.name, "command": self.command}

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "LaunchCommand":
        """Create a command model from JSON-compatible data."""
        return cls(id=data["id"], name=data["name"], command=data["command"])


@dataclass
class Project:
    """Saved project directory and its project-specific commands."""

    name: str
    path: str
    id: str = field(default_factory=_new_id)
    commands: list[LaunchCommand] = field(default_factory=list)

    @classmethod
    def from_path(cls, path: str) -> "Project":
        """Create a project using the directory name as the display name."""
        normalized_path = normalize_path(path)
        return cls(name=Path(normalized_path).name, path=normalized_path)

    def to_dict(self) -> dict[str, object]:
        """Serialize the project to JSON-compatible data."""
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "commands": [command.to_dict() for command in self.commands],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Project":
        """Create a project model from JSON-compatible data."""
        commands = [
            LaunchCommand.from_dict(command)
            for command in data.get("commands", [])
        ]
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            path=str(data["path"]),
            commands=commands,
        )


@dataclass
class AppConfig:
    """Persisted application configuration."""

    projects: list[Project] = field(default_factory=list)
    global_commands: list[LaunchCommand] = field(default_factory=list)
    last_selected_project_id: str | None = None

    def add_project(self, path: str) -> Project:
        """Add a project path or select the existing project for that path."""
        normalized_path = normalize_path(path)

        for project in self.projects:
            # Compare normalized paths so trailing slashes do not duplicate projects.
            if normalize_path(project.path).lower() == normalized_path.lower():
                self.last_selected_project_id = project.id
                return project

        project = Project.from_path(normalized_path)
        self.projects.append(project)
        self.last_selected_project_id = project.id
        return project

    def selected_project(self) -> Project | None:
        """Return the last selected project if it still exists."""
        for project in self.projects:
            if project.id == self.last_selected_project_id:
                return project
        return self.projects[0] if self.projects else None

    def to_dict(self) -> dict[str, object]:
        """Serialize the app config to JSON-compatible data."""
        return {
            "projects": [project.to_dict() for project in self.projects],
            "globalCommands": [command.to_dict() for command in self.global_commands],
            "lastSelectedProjectId": self.last_selected_project_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "AppConfig":
        """Create app config from JSON-compatible data."""
        return cls(
            projects=[
                Project.from_dict(project)
                for project in data.get("projects", [])
            ],
            global_commands=[
                LaunchCommand.from_dict(command)
                for command in data.get("globalCommands", [])
            ],
            last_selected_project_id=data.get("lastSelectedProjectId"),
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m pytest tests/test_models.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/command_launcher/models.py tests/test_models.py
git commit -m "feat: add launcher data models"
```

## Task 3: Config Store

**Files:**
- Create: `src/command_launcher/config_store.py`
- Create: `tests/test_config_store.py`

- [ ] **Step 1: Write failing config store tests**

Create `tests/test_config_store.py`:

```python
import json

from command_launcher.config_store import ConfigStore
from command_launcher.models import AppConfig, LaunchCommand


def test_load_missing_config_returns_empty_config(tmp_path):
    store = ConfigStore(tmp_path / "config.json")

    config = store.load()

    assert isinstance(config, AppConfig)
    assert config.projects == []


def test_save_and_load_round_trip(tmp_path):
    store = ConfigStore(tmp_path / "config.json")
    config = AppConfig()
    project = config.add_project(r"D:\work\command-launcher")
    project.commands.append(LaunchCommand(name="VS Code", command="code ."))
    config.global_commands.append(LaunchCommand(name="Git Bash", command="git-bash.exe"))
    store.save(config)

    loaded = store.load()

    assert loaded.projects[0].name == "command-launcher"
    assert loaded.projects[0].commands[0].command == "code ."
    assert loaded.global_commands[0].name == "Git Bash"


def test_malformed_config_is_backed_up_and_empty_config_is_returned(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text("{broken json", encoding="utf-8")
    store = ConfigStore(config_path)

    config = store.load()

    backups = list(tmp_path.glob("config.broken.*.json"))
    assert config.projects == []
    assert len(backups) == 1
    assert json.loads(config_path.read_text(encoding="utf-8"))["projects"] == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_config_store.py -v
```

Expected: FAIL because `command_launcher.config_store` does not exist.

- [ ] **Step 3: Implement config store**

Create `src/command_launcher/config_store.py`:

```python
"""JSON-backed configuration persistence."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from command_launcher.models import AppConfig


def default_config_path() -> Path:
    """Return the default per-user Windows config path."""
    appdata = os.getenv("APPDATA")
    base_dir = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    return base_dir / "CommandLauncher" / "config.json"


class ConfigStore:
    """Load and save the application config as JSON."""

    def __init__(self, path: Path | None = None) -> None:
        """Create a config store for the provided path or the default path."""
        self.path = path or default_config_path()

    def load(self) -> AppConfig:
        """Load config, recovering to an empty config if the file is missing or broken."""
        if not self.path.exists():
            return AppConfig()

        try:
            with self.path.open("r", encoding="utf-8") as config_file:
                return AppConfig.from_dict(json.load(config_file))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            self._backup_broken_config()
            config = AppConfig()
            self.save(config)
            return config

    def save(self, config: AppConfig) -> None:
        """Persist config to disk, creating the config directory when needed."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as config_file:
            json.dump(config.to_dict(), config_file, ensure_ascii=False, indent=2)

    def _backup_broken_config(self) -> None:
        """Move a malformed config aside before replacing it with a clean file."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = self.path.with_name(f"config.broken.{timestamp}.json")
        shutil.move(str(self.path), str(backup_path))
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m pytest tests/test_config_store.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/command_launcher/config_store.py tests/test_config_store.py
git commit -m "feat: add json config store"
```

## Task 4: Command Runner

**Files:**
- Create: `src/command_launcher/command_runner.py`
- Create: `tests/test_command_runner.py`

- [ ] **Step 1: Write failing command runner tests**

Create `tests/test_command_runner.py`:

```python
import subprocess

import pytest

from command_launcher.command_runner import CommandRunner


def test_build_cmd_command_uses_project_directory():
    runner = CommandRunner()

    executable, args = runner.build_cmd(r"D:\work\command-launcher")

    assert executable == "cmd.exe"
    assert args == ["/K", "cd", "/d", r"D:\work\command-launcher"]


def test_build_powershell_command_uses_literal_path():
    runner = CommandRunner()

    executable, args = runner.build_powershell(r"D:\work\command-launcher")

    assert executable == "powershell.exe"
    assert args == [
        "-NoExit",
        "-Command",
        "Set-Location -LiteralPath 'D:\\work\\command-launcher'",
    ]


def test_run_custom_rejects_empty_command():
    runner = CommandRunner()

    with pytest.raises(ValueError, match="Command text cannot be empty"):
        runner.run_custom(" ", r"D:\work\command-launcher")


def test_run_custom_uses_shell_and_project_cwd(monkeypatch):
    calls = []

    def fake_popen(*args, **kwargs):
        calls.append((args, kwargs))
        return object()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    runner = CommandRunner()

    runner.run_custom("code .", r"D:\work\command-launcher")

    assert calls[0][0] == ("code .",)
    assert calls[0][1]["cwd"] == r"D:\work\command-launcher"
    assert calls[0][1]["shell"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_command_runner.py -v
```

Expected: FAIL because `command_launcher.command_runner` does not exist.

- [ ] **Step 3: Implement command runner**

Create `src/command_launcher/command_runner.py`:

```python
"""External process launching for built-in and custom project commands."""

from __future__ import annotations

import subprocess
from pathlib import Path


class CommandRunner:
    """Build and launch external commands from a project directory."""

    def build_cmd(self, project_path: str) -> tuple[str, list[str]]:
        """Return executable and args for opening cmd in the project directory."""
        return "cmd.exe", ["/K", "cd", "/d", project_path]

    def build_powershell(self, project_path: str) -> tuple[str, list[str]]:
        """Return executable and args for opening PowerShell in the project directory."""
        escaped_path = project_path.replace("'", "''")
        return (
            "powershell.exe",
            ["-NoExit", "-Command", f"Set-Location -LiteralPath '{escaped_path}'"],
        )

    def build_explorer(self, project_path: str) -> tuple[str, list[str]]:
        """Return executable and args for opening File Explorer at the project directory."""
        return "explorer.exe", [project_path]

    def run_cmd(self, project_path: str) -> subprocess.Popen:
        """Open cmd in the project directory and return the process handle."""
        executable, args = self.build_cmd(project_path)
        return subprocess.Popen([executable, *args])

    def run_powershell(self, project_path: str) -> subprocess.Popen:
        """Open PowerShell in the project directory and return the process handle."""
        executable, args = self.build_powershell(project_path)
        return subprocess.Popen([executable, *args])

    def run_explorer(self, project_path: str) -> subprocess.Popen:
        """Open File Explorer at the project directory and return the process handle."""
        executable, args = self.build_explorer(project_path)
        return subprocess.Popen([executable, *args])

    def run_custom(self, command: str, project_path: str) -> subprocess.Popen:
        """Launch a user command from the project directory."""
        if not command.strip():
            raise ValueError("Command text cannot be empty")

        # Use shell=True so user commands such as `code .` resolve like they do in cmd.
        return subprocess.Popen(command, cwd=str(Path(project_path)), shell=True)
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m pytest tests/test_command_runner.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/command_launcher/command_runner.py tests/test_command_runner.py
git commit -m "feat: add external command runner"
```

## Task 5: PySide6 UI

**Files:**
- Create: `src/command_launcher/app.py`
- Create: `src/command_launcher/ui/__init__.py`
- Create: `src/command_launcher/ui/dialogs.py`
- Create: `src/command_launcher/ui/main_window.py`
- Create: `src/command_launcher/ui/styles.py`
- Modify: `src/command_launcher/main.py`

- [ ] **Step 1: Add UI smoke test**

Create `tests/test_ui_imports.py`:

```python
def test_ui_modules_import():
    from command_launcher.app import create_app
    from command_launcher.ui.main_window import MainWindow

    assert create_app is not None
    assert MainWindow is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_ui_imports.py -v
```

Expected: FAIL because `command_launcher.app` and UI modules do not exist.

- [ ] **Step 3: Implement UI files**

Create `src/command_launcher/app.py`:

```python
"""Qt application setup."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from command_launcher.ui.styles import LIGHT_STYLESHEET


def create_app(argv: list[str] | None = None) -> QApplication:
    """Create and configure the Qt application instance."""
    app = QApplication(argv or sys.argv)
    app.setApplicationName("Project Launcher")
    app.setStyleSheet(LIGHT_STYLESHEET)
    return app
```

Create `src/command_launcher/ui/__init__.py`:

```python
"""User interface package."""
```

Create `src/command_launcher/ui/styles.py`:

```python
"""Application stylesheet."""

LIGHT_STYLESHEET = """
QMainWindow {
  background: #f6f7f9;
}
QListWidget, QFrame, QGroupBox {
  background: #ffffff;
  border: 1px solid #d9dde4;
  border-radius: 8px;
}
QPushButton {
  background: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  padding: 8px 12px;
  font-weight: 600;
}
QPushButton:disabled {
  background: #cbd5e1;
  color: #64748b;
}
QPushButton:hover {
  background: #1d4ed8;
}
QLineEdit {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 8px;
}
QLabel {
  color: #111827;
}
"""
```

Create `src/command_launcher/ui/dialogs.py`:

```python
"""Dialogs for editing launcher commands."""

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QVBoxLayout

from command_launcher.models import LaunchCommand


class CommandDialog(QDialog):
    """Dialog for creating or editing a launch command."""

    def __init__(self, command: LaunchCommand | None = None, parent=None) -> None:
        """Initialize fields from an optional existing command."""
        super().__init__(parent)
        self.setWindowTitle("Command")
        self.name_input = QLineEdit(command.name if command else "")
        self.command_input = QLineEdit(command.command if command else "")

        form = QFormLayout()
        form.addRow("Name", self.name_input)
        form.addRow("Command", self.command_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def command_values(self) -> tuple[str, str]:
        """Return trimmed command name and command text."""
        return self.name_input.text().strip(), self.command_input.text().strip()
```

Create `src/command_launcher/ui/main_window.py` with a minimal functional main window that loads config, renders projects, opens built-in commands, and manages commands:

```python
"""Main Project Launcher window."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from command_launcher.command_runner import CommandRunner
from command_launcher.config_store import ConfigStore
from command_launcher.models import AppConfig, LaunchCommand, Project
from command_launcher.ui.dialogs import CommandDialog


class MainWindow(QMainWindow):
    """Main two-column project launcher window."""

    def __init__(
        self,
        store: ConfigStore | None = None,
        runner: CommandRunner | None = None,
    ) -> None:
        """Load configuration and initialize the main window widgets."""
        super().__init__()
        self.store = store or ConfigStore()
        self.runner = runner or CommandRunner()
        self.config: AppConfig = self.store.load()

        self.setWindowTitle("Project Launcher")
        self.resize(980, 620)
        self.project_list = QListWidget()
        self.project_name = QLabel("No project selected")
        self.project_path = QLabel("")
        self.cmd_button = QPushButton("cmd")
        self.powershell_button = QPushButton("PowerShell")
        self.explorer_button = QPushButton("Explorer")
        self.global_commands = QListWidget()
        self.project_commands = QListWidget()

        self._build_layout()
        self._connect_signals()
        self._refresh_projects()
        self._select_initial_project()

    def _build_layout(self) -> None:
        """Build the fixed two-column UI layout."""
        root = QHBoxLayout()
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        sidebar = QFrame()
        sidebar_layout = QVBoxLayout(sidebar)
        add_project = QPushButton("Add Project")
        remove_project = QPushButton("Remove Project")
        self.add_project_button = add_project
        self.remove_project_button = remove_project
        sidebar_layout.addWidget(QLabel("Projects"))
        sidebar_layout.addWidget(self.project_list, 1)
        sidebar_layout.addWidget(add_project)
        sidebar_layout.addWidget(remove_project)
        root.addWidget(sidebar, 1)

        content = QFrame()
        content_layout = QVBoxLayout(content)
        content_layout.addWidget(self.project_name)
        content_layout.addWidget(self.project_path)

        builtins = QHBoxLayout()
        builtins.addWidget(self.cmd_button)
        builtins.addWidget(self.powershell_button)
        builtins.addWidget(self.explorer_button)
        content_layout.addLayout(builtins)

        content_layout.addWidget(QLabel("Global Commands"))
        content_layout.addWidget(self.global_commands)
        add_global = QPushButton("Add Global Command")
        delete_global = QPushButton("Delete Global Command")
        self.add_global_button = add_global
        self.delete_global_button = delete_global
        content_layout.addWidget(add_global)
        content_layout.addWidget(delete_global)

        content_layout.addWidget(QLabel("Project Commands"))
        content_layout.addWidget(self.project_commands)
        add_project_command = QPushButton("Add Project Command")
        delete_project_command = QPushButton("Delete Project Command")
        self.add_project_command_button = add_project_command
        self.delete_project_command_button = delete_project_command
        content_layout.addWidget(add_project_command)
        content_layout.addWidget(delete_project_command)
        root.addWidget(content, 3)

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)

    def _connect_signals(self) -> None:
        """Connect UI events to application actions."""
        self.add_project_button.clicked.connect(self._add_project)
        self.remove_project_button.clicked.connect(self._remove_project)
        self.project_list.currentItemChanged.connect(self._project_changed)
        self.cmd_button.clicked.connect(lambda: self._run_builtin("cmd"))
        self.powershell_button.clicked.connect(lambda: self._run_builtin("powershell"))
        self.explorer_button.clicked.connect(lambda: self._run_builtin("explorer"))
        self.add_global_button.clicked.connect(lambda: self._add_command(global_command=True))
        self.add_project_command_button.clicked.connect(lambda: self._add_command(global_command=False))
        self.delete_global_button.clicked.connect(lambda: self._delete_command(global_command=True))
        self.delete_project_command_button.clicked.connect(lambda: self._delete_command(global_command=False))
        self.global_commands.itemDoubleClicked.connect(lambda item: self._run_command_item(item, True))
        self.project_commands.itemDoubleClicked.connect(lambda item: self._run_command_item(item, False))

    def _refresh_projects(self) -> None:
        """Render the saved project list."""
        self.project_list.clear()
        for project in self.config.projects:
            item = QListWidgetItem(project.name)
            item.setData(1, project.id)
            self.project_list.addItem(item)

    def _select_initial_project(self) -> None:
        """Select the last used project or the first available project."""
        selected = self.config.selected_project()
        if not selected:
            self._render_project(None)
            return
        for index in range(self.project_list.count()):
            item = self.project_list.item(index)
            if item.data(1) == selected.id:
                self.project_list.setCurrentItem(item)
                return

    def _selected_project(self) -> Project | None:
        """Return the project selected in the project list."""
        item = self.project_list.currentItem()
        if not item:
            return None
        project_id = item.data(1)
        return next((project for project in self.config.projects if project.id == project_id), None)

    def _project_changed(self) -> None:
        """Persist and render the newly selected project."""
        project = self._selected_project()
        self.config.last_selected_project_id = project.id if project else None
        self.store.save(self.config)
        self._render_project(project)

    def _render_project(self, project: Project | None) -> None:
        """Render project details and command lists."""
        enabled = bool(project and Path(project.path).exists())
        self.project_name.setText(project.name if project else "No project selected")
        self.project_path.setText(project.path if project else "")
        for button in (self.cmd_button, self.powershell_button, self.explorer_button):
            button.setEnabled(enabled)

        self.global_commands.clear()
        for command in self.config.global_commands:
            item = QListWidgetItem(command.name)
            item.setData(1, command.id)
            self.global_commands.addItem(item)

        self.project_commands.clear()
        if project:
            for command in project.commands:
                item = QListWidgetItem(command.name)
                item.setData(1, command.id)
                self.project_commands.addItem(item)

    def _add_project(self) -> None:
        """Prompt for a directory and save it as a project."""
        directory = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if not directory:
            return
        project = self.config.add_project(directory)
        self.store.save(self.config)
        self._refresh_projects()
        for index in range(self.project_list.count()):
            item = self.project_list.item(index)
            if item.data(1) == project.id:
                self.project_list.setCurrentItem(item)
                break

    def _remove_project(self) -> None:
        """Remove the selected project from local configuration only."""
        project = self._selected_project()
        if not project:
            return
        self.config.projects = [item for item in self.config.projects if item.id != project.id]
        self.config.last_selected_project_id = None
        self.store.save(self.config)
        self._refresh_projects()
        self._select_initial_project()

    def _add_command(self, global_command: bool) -> None:
        """Create a global or project-specific custom command."""
        project = self._selected_project()
        if not global_command and not project:
            return
        dialog = CommandDialog(parent=self)
        if dialog.exec() != CommandDialog.Accepted:
            return
        name, command_text = dialog.command_values()
        if not LaunchCommand.is_valid(name, command_text):
            QMessageBox.warning(self, "Invalid Command", "Name and command are required.")
            return
        command = LaunchCommand(name=name, command=command_text)
        if global_command:
            self.config.global_commands.append(command)
        else:
            project.commands.append(command)
        self.store.save(self.config)
        self._render_project(project)

    def _delete_command(self, global_command: bool) -> None:
        """Delete the selected custom command."""
        project = self._selected_project()
        command_list = self.global_commands if global_command else self.project_commands
        item = command_list.currentItem()
        if not item:
            return
        command_id = item.data(1)
        if global_command:
            self.config.global_commands = [
                command for command in self.config.global_commands if command.id != command_id
            ]
        elif project:
            project.commands = [command for command in project.commands if command.id != command_id]
        self.store.save(self.config)
        self._render_project(project)

    def _run_builtin(self, command_type: str) -> None:
        """Run one built-in command for the selected project."""
        project = self._selected_project()
        if not project:
            return
        try:
            if command_type == "cmd":
                self.runner.run_cmd(project.path)
            elif command_type == "powershell":
                self.runner.run_powershell(project.path)
            else:
                self.runner.run_explorer(project.path)
        except Exception as exc:
            QMessageBox.critical(self, "Launch Failed", str(exc))

    def _run_command_item(self, item: QListWidgetItem, global_command: bool) -> None:
        """Run a selected custom command from the current project directory."""
        project = self._selected_project()
        if not project:
            return
        commands = self.config.global_commands if global_command else project.commands
        command_id = item.data(1)
        command = next((entry for entry in commands if entry.id == command_id), None)
        if not command:
            return
        try:
            self.runner.run_custom(command.command, project.path)
        except Exception as exc:
            QMessageBox.critical(self, "Launch Failed", f"{command.command}\n\n{exc}")
```

Modify `src/command_launcher/main.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m pytest tests/test_ui_imports.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/command_launcher/app.py src/command_launcher/main.py src/command_launcher/ui tests/test_ui_imports.py
git commit -m "feat: add pyside main window"
```

## Task 6: Full Verification And Packaging Command

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Run all automated tests**

Run:

```bash
python -m pytest -v
```

Expected: all tests PASS.

- [ ] **Step 2: Add README usage details**

Modify `README.md`:

```markdown
# Project Launcher

Windows project launcher built with Python and PySide6.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
command-launcher
```

## Features

- Save project directories.
- Open `cmd`, PowerShell, and File Explorer from the selected project directory.
- Add global custom commands for every project.
- Add project-specific custom commands.
- Store configuration at `%APPDATA%\CommandLauncher\config.json`.

## Packaging

Build a debuggable one-directory Windows package:

```bash
pyinstaller --onedir --name CommandLauncher src/command_launcher/main.py
```

The `--onefile` package can be evaluated after the one-directory build is stable.
```

- [ ] **Step 3: Run all tests again**

Run:

```bash
python -m pytest -v
```

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add usage and packaging notes"
```

## Self-Review

- Spec coverage: project saving, duplicate path handling, built-in launch commands, global commands, project commands, config recovery, Windows packaging notes, and PySide6 UI are covered.
- Scope check: embedded terminal, process management, tray mode, grouping, shortcuts, search, and cross-platform support remain out of scope.
- Placeholder scan: no TBD/TODO placeholders are present.
- Type consistency: `LaunchCommand`, `Project`, `AppConfig`, `ConfigStore`, `CommandRunner`, and `MainWindow` names are used consistently across tasks.
