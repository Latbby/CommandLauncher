from command_launcher.models import AppConfig, LaunchCommand, Project


def test_project_uses_directory_name_as_default_name():
    project = Project.from_path(r"D:\work\command-launcher")

    assert project.name == "command-launcher"
    assert project.path == r"D:\work\command-launcher"
    assert project.commands == []


def test_config_selects_existing_project_for_duplicate_path():
    config = AppConfig()
    first = config.add_project(r"D:\work\command-launcher")
    second = config.add_project(r"D:\work\command-launcher\\")

    assert first.id == second.id
    assert len(config.projects) == 1
    assert config.last_selected_project_id == first.id


def test_launch_command_rejects_empty_values():
    assert LaunchCommand.is_valid("VS Code", "code .")
    assert not LaunchCommand.is_valid("", "code .")
    assert not LaunchCommand.is_valid("VS Code", "")
