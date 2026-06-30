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
