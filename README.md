# Project Launcher

Windows project launcher built with Python and PySide6.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
command-launcher
```

## Features

- Save project directories.
- Open `cmd`, PowerShell, and File Explorer from the selected project directory.
- Add global custom commands for every project.
- Add project-specific custom commands.
- Store configuration at `%APPDATA%\CommandLauncher\config.json`.

## Packaging

Build a debuggable one-directory Windows package:

```bash
pyinstaller --onedir --name CommandLauncher src/command_launcher/main.py
```

The `--onefile` package can be evaluated after the one-directory build is stable.
