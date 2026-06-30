"""主窗口 UI 测试。"""

from pathlib import Path


def test_ui_modules_import():
    from command_launcher.app import create_app
    from command_launcher.ui.main_window import MainWindow

    assert create_app is not None
    assert MainWindow is not None


def test_main_window_exposes_command_edit_actions(tmp_path, monkeypatch):
    """验证主窗口暴露基础按钮和统一命令列表。

    入参: 空配置 + 临时目录
    出参: 按钮文案正确，添加按钮存在
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.config_store import ConfigStore
    from command_launcher.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(store=ConfigStore(tmp_path / "config.json"))

    assert window.cmd_button.text() == "打开命令提示符"
    assert window.powershell_button.text() == "打开 PowerShell"
    assert window.explorer_button.text() == "打开资源管理器"
    assert window.add_command_button.text() == "添加"

    window.close()
    app.processEvents()


def test_command_dialog_uses_chinese_button_text(monkeypatch):
    """验证命令对话框使用中文按钮文本。

    入参: 创建 CommandDialog
    出参: 确定/取消按钮文案正确
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication, QDialogButtonBox

    from command_launcher.ui.dialogs import CommandDialog

    app = QApplication.instance() or QApplication([])
    dialog = CommandDialog()
    buttons = dialog.findChild(QDialogButtonBox)

    assert buttons.button(QDialogButtonBox.Ok).text() == "确定"
    assert buttons.button(QDialogButtonBox.Cancel).text() == "取消"

    dialog.close()
    app.processEvents()


def test_main_window_uses_modern_layout_components(tmp_path, monkeypatch):
    """验证主窗口使用统一命令列表（无 Tab 分页）。

    入参: 空配置 + 临时目录
    出参: 只有统一 command_list，无旧版 command_tabs
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication, QListWidget, QSplitter

    from command_launcher.config_store import ConfigStore
    from command_launcher.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(store=ConfigStore(tmp_path / "config.json"))

    # 主布局使用可拖动分栏
    assert isinstance(window.main_splitter, QSplitter)
    # 统一命令列表
    assert isinstance(window.command_list, QListWidget)
    # 旧版 Tab 组件不应存在
    assert not hasattr(window, "command_tabs")

    # 样式对象名
    assert window.project_name.objectName() == "projectTitle"
    assert window.project_path.objectName() == "projectPath"
    assert window.remove_project_button.property("variant") == "danger"
    assert window.add_command_button.property("variant") == "secondary"

    window.close()
    app.processEvents()


def test_main_window_status_bar_warns_when_project_path_missing(tmp_path, monkeypatch):
    """验证项目路径不存在时状态栏显示轻量提示。

    入参: 路径不存在的项目
    出参: 启动按钮禁用，状态栏提示正确
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.config_store import ConfigStore
    from command_launcher.models import AppConfig, Project
    from command_launcher.ui.main_window import MainWindow

    missing_path = tmp_path / "missing-project"
    config_path = tmp_path / "config.json"
    store = ConfigStore(config_path)
    project = Project(name="缺失项目", path=str(missing_path))
    store.save(AppConfig(projects=[project], last_selected_project_id=project.id))

    app = QApplication.instance() or QApplication([])
    window = MainWindow(store=store)

    assert window.cmd_button.isEnabled() is False
    assert window.powershell_button.isEnabled() is False
    assert window.explorer_button.isEnabled() is False
    assert window.statusBar().currentMessage() == "项目路径不存在，启动操作已禁用。"

    window.close()
    app.processEvents()


def test_light_stylesheet_contains_modern_selectors():
    """验证现代化界面依赖的关键样式选择器存在。

    入参: 无
    出参: 面板、按钮变体、命令列表、等宽字体、配色选择器均存在
    """
    from command_launcher.ui.styles import LIGHT_STYLESHEET

    # 面板无边框
    assert "QFrame#sidebarPanel" in LIGHT_STYLESHEET
    assert "QFrame#contentPanel" in LIGHT_STYLESHEET
    assert "border: none;" in LIGHT_STYLESHEET
    # 按钮变体
    assert 'QPushButton[variant="primary"]' in LIGHT_STYLESHEET
    assert 'QPushButton[variant="secondary-fill"]' in LIGHT_STYLESHEET
    assert 'QPushButton[variant="secondary"]' in LIGHT_STYLESHEET
    assert 'QPushButton[variant="danger"]' in LIGHT_STYLESHEET
    # 命令列表 + 列表内按钮
    assert "QListWidget#commandList" in LIGHT_STYLESHEET
    assert "QPushButton#itemActionBtn" in LIGHT_STYLESHEET
    assert "QLabel#globalTag" in LIGHT_STYLESHEET
    # 签名元素：等宽路径
    assert "QLabel#projectPath" in LIGHT_STYLESHEET
    assert "Consolas" in LIGHT_STYLESHEET
    # 新配色
    assert "#5b5fe3" in LIGHT_STYLESHEET
    assert "#eeede8" in LIGHT_STYLESHEET


def test_double_click_global_command_runs_from_selected_project(tmp_path, monkeypatch):
    """验证命令通过 _CommandItemWidget 运行回调正确触发。

    入参: 包含全局命令和项目的配置
    出参: 全局命令从项目目录启动
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.config_store import ConfigStore
    from command_launcher.models import AppConfig, LaunchCommand, Project
    from command_launcher.ui.main_window import MainWindow

    class FakeRunner:
        """记录自定义命令调用参数的测试运行器。"""

        def __init__(self) -> None:
            self.custom_calls: list[tuple[str, str]] = []

        def run_custom(self, command: str, project_path: str) -> object:
            self.custom_calls.append((command, project_path))
            return object()

    project_dir = tmp_path / "selected-project"
    project_dir.mkdir()
    project = Project(name="选中项目", path=str(project_dir))
    command = LaunchCommand(name="打开编辑器", command="code .")
    store = ConfigStore(tmp_path / "config.json")
    store.save(
        AppConfig(
            projects=[project],
            global_commands=[command],
            last_selected_project_id=project.id,
        )
    )
    runner = FakeRunner()

    app = QApplication.instance() or QApplication([])
    window = MainWindow(store=store, runner=runner)

    # 获取命令列表中的 _CommandItemWidget
    item_widget = window.command_list.itemWidget(window.command_list.item(0))
    # 模拟双击运行
    item_widget.run_requested.emit(command.id)

    assert runner.custom_calls == [("code .", str(project_dir))]

    window.close()
    app.processEvents()


def test_explorer_button_opens_selected_project_path(tmp_path, monkeypatch):
    """验证资源管理器按钮使用当前选中项目目录。

    入参: 包含项目的配置
    出参: 点击资源管理器按钮调用 run_explorer 并传入正确路径
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.config_store import ConfigStore
    from command_launcher.models import AppConfig, Project
    from command_launcher.ui.main_window import MainWindow

    class FakeRunner:
        """记录资源管理器调用路径的测试运行器。"""

        def __init__(self) -> None:
            self.explorer_calls: list[str] = []

        def run_explorer(self, project_path: str) -> object:
            self.explorer_calls.append(project_path)
            return object()

    project_dir = tmp_path / "selected-project"
    project_dir.mkdir()
    project = Project(name="选中项目", path=str(project_dir))
    store = ConfigStore(tmp_path / "config.json")
    store.save(AppConfig(projects=[project], last_selected_project_id=project.id))
    runner = FakeRunner()

    app = QApplication.instance() or QApplication([])
    window = MainWindow(store=store, runner=runner)

    window.explorer_button.click()

    assert runner.explorer_calls == [str(project_dir)]

    window.close()
    app.processEvents()
