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


def test_windows_build_script_packages_application_icon():
    """验证打包脚本同时设置 exe 图标并携带运行时窗口图标。

    入参: build_windows.bat
    出参: PyInstaller 使用 assets/icon.ico 作为 exe 图标，并把图标文件复制进 dist
    """
    script = Path("build_windows.bat").read_text(encoding="utf-8")

    assert "--icon assets\\icon.ico" in script
    assert '--add-data "assets\\icon.ico;assets"' in script


def test_windows_build_script_uses_project_virtual_environment():
    """验证一键打包脚本优先使用项目内虚拟环境。"""
    script = Path("build_windows.bat").read_text(encoding="utf-8")

    assert 'set "VENV_PYTHON=.venv\\Scripts\\python.exe"' in script
    assert 'if exist "%VENV_PYTHON%" goto use_venv' in script
    assert '%BOOTSTRAP_PYTHON% -m venv .venv' in script
    assert 'set "PYTHON_CMD=%VENV_PYTHON%"' in script


def test_windows_build_script_uses_project_temp_directories():
    """验证一键打包脚本使用项目内临时目录。

    入参: build_windows.bat
    出参: pip 和构建过程使用项目内可写临时目录
    """
    script = Path("build_windows.bat").read_text(encoding="utf-8")

    assert 'set "BUILD_TMP=%~dp0.build_tmp"' in script
    assert 'set "TEMP=%BUILD_TMP%\\temp"' in script
    assert 'set "TMP=%BUILD_TMP%\\temp"' in script
    assert 'set "PIP_CACHE_DIR=%BUILD_TMP%\\pip-cache"' in script


def test_windows_build_script_resets_pyinstaller_runtime_environment():
    """验证打包脚本清理已打包程序继承的运行时环境变量。

    入参: build_windows.bat
    出参: PyInstaller 子进程不会继承旧 exe 注入的 _PYI 环境
    """
    script = Path("build_windows.bat").read_text(encoding="utf-8")

    assert 'set "_PYI_ARCHIVE_FILE="' in script
    assert 'set "_PYI_APPLICATION_HOME_DIR="' in script
    assert 'set "_PYI_PARENT_PROCESS_LEVEL="' in script
    assert 'set "PYINSTALLER_RESET_ENVIRONMENT=1"' in script


def test_windows_build_script_checks_running_packaged_app():
    """验证打包前检查旧版程序是否仍在运行。

    入参: build_windows.bat
    出参: 检测 CommandLauncher.exe 并提示用户先关闭
    """
    script = Path("build_windows.bat").read_text(encoding="utf-8")

    assert 'tasklist /FI "IMAGENAME eq CommandLauncher.exe"' in script
    assert '请先关闭正在运行的 CommandLauncher.exe' in script
    assert ":app_running" in script


def test_windows_build_script_uses_crlf_line_endings():
    """验证批处理脚本使用 cmd 稳定识别的 CRLF 换行。"""
    script_bytes = Path("build_windows.bat").read_bytes()

    assert b"\r\n" in script_bytes
    assert b"\n" not in script_bytes.replace(b"\r\n", b"")
