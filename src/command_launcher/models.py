"""Data models for projects, commands, and persisted application config."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PureWindowsPath
from uuid import uuid4


def _new_id() -> str:
    """Create a stable string id for persisted model objects."""
    return str(uuid4())


def normalize_path(path: str) -> str:
    """Normalize a project path for duplicate comparison and storage.

    Args:
        path: Project path selected by the user.

    Returns:
        A path string without trailing slash characters.
    """
    return path.strip().rstrip("\\/")


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
        """Return whether command values are valid for saving.

        Args:
            name: Display name entered by the user.
            command: Command text entered by the user.

        Returns:
            True when both values contain non-whitespace text.
        """
        return bool(name.strip()) and bool(command.strip())

    def to_dict(self) -> dict[str, str]:
        """Serialize the command to JSON-compatible data.

        Returns:
            Dictionary containing the persisted command fields.
        """
        return {"id": self.id, "name": self.name, "command": self.command}

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "LaunchCommand":
        """Create a command model from JSON-compatible data.

        Args:
            data: Persisted command dictionary.

        Returns:
            LaunchCommand instance restored from the dictionary.
        """
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
        """Create a project using the directory name as the display name.

        Args:
            path: Directory path selected by the user.

        Returns:
            Project instance with a generated id and default display name.
        """
        normalized_path = normalize_path(path)
        return cls(name=PureWindowsPath(normalized_path).name, path=normalized_path)

    def to_dict(self) -> dict[str, object]:
        """Serialize the project to JSON-compatible data.

        Returns:
            Dictionary containing project fields and command dictionaries.
        """
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "commands": [command.to_dict() for command in self.commands],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Project":
        """Create a project model from JSON-compatible data.

        Args:
            data: Persisted project dictionary.

        Returns:
            Project instance restored from the dictionary.
        """
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
    theme: str = "light"
    close_action: str = "ask"
    auto_start: bool = False

    def add_project(self, path: str) -> Project:
        """Add a project path or select the existing project for that path.

        Args:
            path: Directory path selected by the user.

        Returns:
            New or existing project for the path.
        """
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
        """Return the last selected project if it still exists.

        Returns:
            Selected project, first project fallback, or None.
        """
        for project in self.projects:
            if project.id == self.last_selected_project_id:
                return project
        return self.projects[0] if self.projects else None

    def to_dict(self) -> dict[str, object]:
        """Serialize the app config to JSON-compatible data.

        Returns:
            Dictionary matching the persisted config schema.
        """
        return {
            "projects": [project.to_dict() for project in self.projects],
            "globalCommands": [command.to_dict() for command in self.global_commands],
            "lastSelectedProjectId": self.last_selected_project_id,
            "theme": self.theme,
            "closeAction": self.close_action,
            "autoStart": self.auto_start,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "AppConfig":
        """Create app config from JSON-compatible data.

        Args:
            data: Persisted app config dictionary.

        Returns:
            AppConfig instance restored from persisted data.
        """
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
            theme=data.get("theme", "light"),
            close_action=data.get("closeAction", "ask"),
            auto_start=data.get("autoStart", False),
        )
