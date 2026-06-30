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
