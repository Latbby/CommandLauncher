from pathlib import Path


def test_readme_uses_windowed_pyinstaller_build():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "--windowed" in readme
    assert "--name CommandLauncher" in readme
