import json

from command_launcher.config_store import ConfigStore
from command_launcher.models import AppConfig, LaunchCommand


def test_load_missing_config_returns_empty_config(tmp_path):
    store = ConfigStore(tmp_path / "config.json")

    config = store.load()

    assert isinstance(config, AppConfig)
    assert config.projects == []


def test_save_and_load_round_trip(tmp_path):
    store = ConfigStore(tmp_path / "config.json")
    config = AppConfig()
    project = config.add_project(r"D:\work\command-launcher")
    project.commands.append(LaunchCommand(name="VS Code", command="code ."))
    config.global_commands.append(LaunchCommand(name="Git Bash", command="git-bash.exe"))
    store.save(config)

    loaded = store.load()

    assert loaded.projects[0].name == "command-launcher"
    assert loaded.projects[0].commands[0].command == "code ."
    assert loaded.global_commands[0].name == "Git Bash"


def test_malformed_config_is_backed_up_and_empty_config_is_returned(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text("{broken json", encoding="utf-8")
    store = ConfigStore(config_path)

    config = store.load()

    backups = list(tmp_path.glob("config.broken.*.json"))
    assert config.projects == []
    assert len(backups) == 1
    assert json.loads(config_path.read_text(encoding="utf-8"))["projects"] == []
