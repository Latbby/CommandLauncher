import subprocess

import pytest

from command_launcher.command_runner import CommandRunner


def test_build_cmd_command_uses_project_directory():
    runner = CommandRunner()

    executable, args = runner.build_cmd(r"D:\work\command-launcher")

    assert executable == "cmd.exe"
    assert args == ["/K", "cd", "/d", r"D:\work\command-launcher"]


def test_build_explorer_command_requests_new_window():
    """验证资源管理器直接打开项目目录。

    Returns:
        None。
    """
    runner = CommandRunner()

    executable, args = runner.build_explorer(r"D:\work\command-launcher")

    assert executable == "explorer.exe"
    assert args == [r"D:\work\command-launcher"]


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


def test_run_custom_opens_visible_cmd_window_in_project_directory(monkeypatch):
    """验证自定义命令在项目目录的新 cmd 窗口中保持可见。

    Args:
        monkeypatch: pytest 提供的替换依赖工具。
    """
    calls = []
    monkeypatch.setattr(subprocess, "CREATE_NEW_CONSOLE", 16, raising=False)

    def fake_popen(*args, **kwargs):
        calls.append((args, kwargs))
        return object()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    runner = CommandRunner()

    runner.run_custom("code .", r"D:\work\command-launcher")

    assert calls[0][0] == (["cmd.exe", "/K", "code ."],)
    assert calls[0][1]["cwd"] == r"D:\work\command-launcher"
    assert calls[0][1]["creationflags"] == 16


def test_run_cmd_requests_new_console_on_each_click(monkeypatch):
    calls = []
    monkeypatch.setattr(subprocess, "CREATE_NEW_CONSOLE", 16, raising=False)

    def fake_popen(*args, **kwargs):
        calls.append((args, kwargs))
        return object()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    runner = CommandRunner()

    runner.run_cmd(r"D:\work\command-launcher")

    assert calls[0][0] == (
        ["cmd.exe", "/K", "cd", "/d", r"D:\work\command-launcher"],
    )
    assert calls[0][1]["creationflags"] == 16
