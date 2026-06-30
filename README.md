# Project Launcher

Windows project launcher built with Python and PySide6.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m command_launcher.main
```

## Packaging

```bash
pyinstaller --onedir --name CommandLauncher src/command_launcher/main.py
```
