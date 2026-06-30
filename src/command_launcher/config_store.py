"""JSON-backed configuration persistence."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from command_launcher.models import AppConfig


def default_config_path() -> Path:
    """Return the default per-user Windows config path.

    Returns:
        Path to `%APPDATA%\\CommandLauncher\\config.json`, with a home
        directory fallback for environments that do not expose APPDATA.
    """
    appdata = os.getenv("APPDATA")
    base_dir = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    return base_dir / "CommandLauncher" / "config.json"


class ConfigStore:
    """Load and save the application config as JSON."""

    def __init__(self, path: Path | None = None) -> None:
        """Create a config store for the provided path or the default path.

        Args:
            path: Optional config file path for tests or custom storage.
        """
        self.path = path or default_config_path()

    def load(self) -> AppConfig:
        """Load config, recovering to an empty config if the file is missing or broken.

        Returns:
            Loaded app config, or a new empty config when recovery is needed.
        """
        if not self.path.exists():
            return AppConfig()

        try:
            with self.path.open("r", encoding="utf-8") as config_file:
                return AppConfig.from_dict(json.load(config_file))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            self._backup_broken_config()
            config = AppConfig()
            self.save(config)
            return config

    def save(self, config: AppConfig) -> None:
        """Persist config to disk, creating the config directory when needed.

        Args:
            config: Application config to write as formatted JSON.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as config_file:
            json.dump(config.to_dict(), config_file, ensure_ascii=False, indent=2)

    def _backup_broken_config(self) -> None:
        """Move a malformed config aside before replacing it with a clean file."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = self.path.with_name(f"config.broken.{timestamp}.json")
        shutil.move(str(self.path), str(backup_path))
