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


def test_app_config_default_theme_is_light():
    """验证 AppConfig 默认主题为浅色。"""
    config = AppConfig()
    assert config.theme == "light"


def test_app_config_default_close_action_is_ask():
    """验证 AppConfig 默认关闭行为为询问。"""
    config = AppConfig()
    assert config.close_action == "ask"


def test_app_config_theme_round_trips_through_json():
    """验证 theme 字段的 JSON 序列化往返。"""
    config = AppConfig()
    config.theme = "dark"
    restored = AppConfig.from_dict(config.to_dict())
    assert restored.theme == "dark"


def test_app_config_close_action_round_trips_through_json():
    """验证 close_action 字段的 JSON 序列化往返。"""
    config = AppConfig()
    config.close_action = "quit"
    restored = AppConfig.from_dict(config.to_dict())
    assert restored.close_action == "quit"


def test_app_config_from_dict_handles_missing_new_fields():
    """旧配置文件没有 theme/closeAction 键时应使用默认值。"""
    old_data = {
        "projects": [],
        "globalCommands": [],
        "lastSelectedProjectId": None,
    }
    config = AppConfig.from_dict(old_data)
    assert config.theme == "light"
    assert config.close_action == "ask"


def test_app_config_auto_start_round_trips_through_json():
    """验证 autoStart 字段在 JSON 序列化/反序列化中正常保留。

    入参: 设置为 True 的配置
    出参: 反序列化后 auto_start 仍为 True，兼容缺失字段的旧配置默认 False
    """
    config = AppConfig(auto_start=True)
    data = config.to_dict()
    assert data["autoStart"] is True

    restored = AppConfig.from_dict(data)
    assert restored.auto_start is True

    # 旧配置缺少 autoStart 字段时默认为 False
    legacy = AppConfig.from_dict({"projects": [], "globalCommands": []})
    assert legacy.auto_start is False
