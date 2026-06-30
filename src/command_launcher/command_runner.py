"""External process launching for built-in and custom project commands."""

from __future__ import annotations

import subprocess
from pathlib import Path


class CommandRunner:
    """Build and launch external commands from a project directory."""

    def _new_console_flags(self) -> int:
        """Return Windows flags that force a new console window per launch.

        Returns:
            `CREATE_NEW_CONSOLE` on Windows, or 0 on platforms without that flag.
        """
        return getattr(subprocess, "CREATE_NEW_CONSOLE", 0)

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
        """构建打开项目目录的资源管理器命令。

        Args:
            project_path: 资源管理器需要打开的项目目录。

        Returns:
            subprocess 使用的可执行文件名和参数列表。
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
        return subprocess.Popen(
            [executable, *args],
            creationflags=self._new_console_flags(),
        )

    def run_powershell(self, project_path: str) -> subprocess.Popen:
        """Open PowerShell in the project directory and return the process handle.

        Args:
            project_path: Directory that PowerShell should open in.

        Returns:
            Process handle returned by subprocess.
        """
        executable, args = self.build_powershell(project_path)
        return subprocess.Popen(
            [executable, *args],
            creationflags=self._new_console_flags(),
        )

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
        """从项目目录启动用户自定义命令。

        Args:
            command: 用户填写的命令文本。
            project_path: 命令执行时使用的工作目录。

        Returns:
            subprocess 返回的进程句柄。

        Raises:
            ValueError: 命令文本为空时抛出。
        """
        if not command.strip():
            raise ValueError("Command text cannot be empty")

        # 使用 cmd /K 保留命令窗口，避免短命令执行后立刻关闭导致用户误以为无响应。
        return subprocess.Popen(
            ["cmd.exe", "/K", command],
            cwd=str(Path(project_path)),
            creationflags=self._new_console_flags(),
        )
