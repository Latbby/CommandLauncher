from pathlib import Path


def test_readme_uses_windowed_pyinstaller_build():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "--windowed" in readme
    assert "--name CommandLauncher" in readme


def test_windows_build_script_packages_windowed_exe_from_repo_root():
    script = Path("build_windows.bat").read_text(encoding="utf-8")

    assert "chcp 65001" in script
    assert 'pushd "%~dp0"' in script
    assert "--windowed --onedir --name CommandLauncher" in script
    assert "src\\command_launcher\\main.py" in script
    assert "dist\\CommandLauncher\\CommandLauncher.exe" in script


def test_windows_build_script_uses_project_virtual_environment():
    """验证一键打包脚本优先使用项目内虚拟环境。"""
    script = Path("build_windows.bat").read_text(encoding="utf-8")

    assert 'set "VENV_PYTHON=.venv\\Scripts\\python.exe"' in script
    assert 'if exist "%VENV_PYTHON%" goto use_venv' in script
    assert '%BOOTSTRAP_PYTHON% -m venv .venv' in script
    assert 'set "PYTHON_CMD=%VENV_PYTHON%"' in script


def test_windows_build_script_uses_crlf_line_endings():
    """验证批处理脚本使用 cmd 稳定识别的 CRLF 换行。"""
    script_bytes = Path("build_windows.bat").read_bytes()

    assert b"\r\n" in script_bytes
    assert b"\n" not in script_bytes.replace(b"\r\n", b"")
