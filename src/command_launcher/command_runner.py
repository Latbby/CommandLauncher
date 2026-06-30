"""External process launching for built-in and custom project commands."""

from __future__ import annotations

import subprocess
from pathlib import Path


class CommandRunner:
    """Build and launch external commands from a project directory."""

    def build_cmd(self, project_path: str) -> tuple[str, list[str]]:
        """Return executable and args for opening cmd in the project directory.

        Args:
            project_path: Directory that cmd should open in.

        Returns:
            Executable name and argument list for subprocess.
        """
        return "cmd.exe", ["/K", "cd", "/d", project_path]

    def build_powershell(self, project_path: str) -> tuple[str, list[str]]:
        """Return executable and args for opening PowerShell in the project directory.

        Args:
            project_path: Directory that PowerShell should open in.

        Returns:
            Executable name and argument list for subprocess.
        """
        escaped_path = project_path.replace("'", "''")
        return (
            "powershell.exe",
            ["-NoExit", "-Command", f"Set-Location -LiteralPath '{escaped_path}'"],
        )

    def build_explorer(self, project_path: str) -> tuple[str, list[str]]:
        """Return executable and args for opening File Explorer at the directory.

        Args:
            project_path: Directory that Explorer should display.

        Returns:
            Executable name and argument list for subprocess.
        """
        return "explorer.exe", [project_path]

    def run_cmd(self, project_path: str) -> subprocess.Popen:
        """Open cmd in the project directory and return the process handle.

        Args:
            project_path: Directory that cmd should open in.

        Returns:
            Process handle returned by subprocess.
        """
        executable, args = self.build_cmd(project_path)
        return subprocess.Popen([executable, *args])

    def run_powershell(self, project_path: str) -> subprocess.Popen:
        """Open PowerShell in the project directory and return the process handle.

        Args:
            project_path: Directory that PowerShell should open in.

        Returns:
            Process handle returned by subprocess.
        """
        executable, args = self.build_powershell(project_path)
        return subprocess.Popen([executable, *args])

    def run_explorer(self, project_path: str) -> subprocess.Popen:
        """Open File Explorer at the project directory and return the process handle.

        Args:
            project_path: Directory that Explorer should display.

        Returns:
            Process handle returned by subprocess.
        """
        executable, args = self.build_explorer(project_path)
        return subprocess.Popen([executable, *args])

    def run_custom(self, command: str, project_path: str) -> subprocess.Popen:
        """Launch a user command from the project directory.

        Args:
            command: User-entered command text.
            project_path: Working directory for command execution.

        Returns:
            Process handle returned by subprocess.

        Raises:
            ValueError: If command text is empty.
        """
        if not command.strip():
            raise ValueError("Command text cannot be empty")

        # Use shell=True so commands such as `code .` resolve like they do in cmd.
        return subprocess.Popen(command, cwd=str(Path(project_path)), shell=True)
