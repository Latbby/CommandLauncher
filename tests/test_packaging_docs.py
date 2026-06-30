from pathlib import Path
import struct


def _read_ico_entries(icon_path: Path) -> list[tuple[int, int, int]]:
    """读取 ICO 文件目录项。

    入参: icon_path 为待检查的 .ico 文件路径
    出参: 每个图层的宽度、高度和位深元组
    """
    data = icon_path.read_bytes()
    reserved, icon_type, image_count = struct.unpack_from("<HHH", data, 0)

    assert reserved == 0
    assert icon_type == 1

    entries: list[tuple[int, int, int]] = []
    for index in range(image_count):
        # ICO 目录宽高字节使用 0 表示 256 像素。
        width, height, _colors, _reserved, _planes, bit_count, _size, _offset = struct.unpack_from(
            "<BBBBHHII",
            data,
            6 + index * 16,
        )
        entries.append((256 if width == 0 else width, 256 if height == 0 else height, bit_count))

    return entries


def test_readme_uses_windowed_pyinstaller_build():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "CommandLauncher.spec" in readme
    assert "python -m PyInstaller --clean --noconfirm CommandLauncher.spec" in readme


def test_windows_build_script_packages_windowed_exe_from_repo_root():
    script = Path("build_windows.bat").read_text(encoding="utf-8")

    assert "chcp 65001" in script
    assert 'pushd "%~dp0"' in script
    assert "CommandLauncher.spec" in script
    assert "dist\\CommandLauncher\\CommandLauncher.exe" in script


def test_windows_build_script_packages_application_icon():
    """验证打包脚本同时设置 exe 图标并携带运行时窗口图标。

    入参: build_windows.bat
    出参: PyInstaller 使用受控 spec，spec 负责 exe 图标和运行时窗口图标
    """
    script = Path("build_windows.bat").read_text(encoding="utf-8")

    assert "%PYTHON_CMD% -m PyInstaller --clean --noconfirm CommandLauncher.spec" in script


def test_pyinstaller_spec_embeds_exe_and_runtime_icons():
    """验证 PyInstaller spec 同时写入 exe 图标和运行时窗口图标。

    入参: CommandLauncher.spec
    出参: EXE 配置包含 icon，Analysis 配置包含 assets/icon.ico 数据文件
    """
    spec = Path("CommandLauncher.spec").read_text(encoding="utf-8")

    assert "('assets/icon.ico', 'assets')" in spec
    assert "icon=['assets/icon.ico']" in spec


def test_pyinstaller_spec_uses_portable_entry_path():
    """验证 PyInstaller spec 使用跨平台入口路径。

    入参: CommandLauncher.spec
    出参: 入口脚本使用正斜杠路径，避免不同环境解析失败
    """
    spec = Path("CommandLauncher.spec").read_text(encoding="utf-8")

    assert "src/command_launcher/main.py" in spec
    assert "src\\command_launcher\\main.py" not in spec


def test_command_launcher_spec_is_tracked_by_gitignore_rules():
    """验证 CommandLauncher.spec 不会继续被通配规则忽略。

    入参: .gitignore
    出参: *.spec 仍默认忽略，但 CommandLauncher.spec 被显式放行
    """
    gitignore = Path(".gitignore").read_text(encoding="utf-8")

    assert "*.spec" in gitignore
    assert "!CommandLauncher.spec" in gitignore


def test_windows_build_script_updates_master_before_packaging():
    """验证 Windows 打包前固定切换并拉取 master 分支。

    入参: build_windows.bat
    出参: 脚本在安装依赖和打包前执行 git checkout master 与 git pull --ff-only origin master
    """
    script = Path("build_windows.bat").read_text(encoding="utf-8")

    checkout_index = script.index("git checkout master")
    pull_index = script.index("git pull --ff-only origin master")
    install_index = script.index('%PYTHON_CMD% -m pip install -e ".[dev]"')

    assert checkout_index < pull_index < install_index


def test_application_icon_contains_windows_shell_sizes():
    """验证 exe 图标包含资源管理器常用尺寸。

    入参: assets/icon.ico
    出参: icon.ico 至少包含 16/32/48/256 像素的 32 位图层
    """
    entries = _read_ico_entries(Path("assets/icon.ico"))
    sizes = {(width, height) for width, height, _bit_count in entries}

    assert {(16, 16), (32, 32), (48, 48), (256, 256)}.issubset(sizes)
    assert all(bit_count == 32 for _width, _height, bit_count in entries)


def test_windows_build_script_cleans_pyinstaller_cache_for_icon_updates():
    """验证打包时清理 PyInstaller 缓存以刷新 exe 图标资源。

    入参: build_windows.bat
    出参: PyInstaller 命令包含 --clean 参数
    """
    script = Path("build_windows.bat").read_text(encoding="utf-8")

    assert "--clean" in script


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
