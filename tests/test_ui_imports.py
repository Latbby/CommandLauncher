def test_ui_modules_import():
    from command_launcher.app import create_app
    from command_launcher.ui.main_window import MainWindow

    assert create_app is not None
    assert MainWindow is not None


def test_main_window_exposes_command_edit_actions(tmp_path, monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.config_store import ConfigStore
    from command_launcher.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(store=ConfigStore(tmp_path / "config.json"))

    assert window.cmd_button.text() == "打开命令提示符"
    assert window.powershell_button.text() == "打开 PowerShell"
    assert window.explorer_button.text() == "打开资源管理器"
    assert window.edit_global_button.text() == "编辑"
    assert window.edit_project_command_button.text() == "编辑"

    window.close()
    app.processEvents()


def test_command_dialog_uses_chinese_button_text(monkeypatch):
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
    """验证主窗口暴露现代化布局组件。

    Args:
        tmp_path: pytest 提供的临时目录。
        monkeypatch: pytest 提供的环境变量修改工具。
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication, QSplitter, QTabWidget

    from command_launcher.config_store import ConfigStore
    from command_launcher.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(store=ConfigStore(tmp_path / "config.json"))

    # 主布局使用可拖动分栏，命令区域使用 Tab 降低纵向堆叠。
    assert isinstance(window.main_splitter, QSplitter)
    assert isinstance(window.command_tabs, QTabWidget)
    assert window.command_tabs.count() == 2
    assert window.command_tabs.tabText(0) == "全局命令"
    assert window.command_tabs.tabText(1) == "项目命令"

    # 样式对象名用于 QSS 精准命中，避免影响对话框内部控件。
    assert window.project_name.objectName() == "projectTitle"
    assert window.project_path.objectName() == "projectPath"
    assert window.remove_project_button.property("variant") == "danger"
    assert window.add_global_button.property("variant") == "secondary"

    window.close()
    app.processEvents()


def test_main_window_status_bar_warns_when_project_path_missing(tmp_path, monkeypatch):
    """验证项目路径不存在时状态栏显示轻量提示。

    Args:
        tmp_path: pytest 提供的临时目录。
        monkeypatch: pytest 提供的环境变量修改工具。
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

    # 不存在的项目路径会禁用启动按钮，并通过状态栏提供轻量反馈。
    assert window.cmd_button.isEnabled() is False
    assert window.powershell_button.isEnabled() is False
    assert window.explorer_button.isEnabled() is False
    assert window.statusBar().currentMessage() == "项目路径不存在，启动操作已禁用。"

    window.close()
    app.processEvents()


def test_light_stylesheet_contains_modern_selectors():
    """验证现代化界面依赖的关键样式选择器存在。"""
    from command_launcher.ui.styles import LIGHT_STYLESHEET

    # 面板无边框
    assert "QFrame#sidebarPanel" in LIGHT_STYLESHEET
    assert "QFrame#contentPanel" in LIGHT_STYLESHEET
    assert "border: none;" in LIGHT_STYLESHEET
    # 按钮变体
    assert 'QPushButton[variant="primary"]' in LIGHT_STYLESHEET
    assert 'QPushButton[variant="secondary"]' in LIGHT_STYLESHEET
    assert 'QPushButton[variant="danger"]' in LIGHT_STYLESHEET
    # Tab 下划线指示器
    assert "QTabWidget::pane" in LIGHT_STYLESHEET
    assert "border-bottom: 2px solid transparent" in LIGHT_STYLESHEET
    assert "border-bottom: 2px solid #2563eb" in LIGHT_STYLESHEET
    # 终端面板样式
    assert "QFrame#terminalPanel" in LIGHT_STYLESHEET
    assert "QTabWidget#terminalTabs" in LIGHT_STYLESHEET
    assert "QPlainTextEdit#terminalOutput" in LIGHT_STYLESHEET
    assert "QSplitter#contentSplitter" in LIGHT_STYLESHEET


def test_double_click_global_command_runs_from_selected_project(tmp_path, monkeypatch):
    """验证双击全局命令会从当前选中项目目录启动。

    Args:
        tmp_path: pytest 提供的临时目录。
        monkeypatch: pytest 提供的环境变量修改工具。
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.config_store import ConfigStore
    from command_launcher.models import AppConfig, LaunchCommand, Project
    from command_launcher.ui.main_window import MainWindow

    class FakeRunner:
        """记录自定义命令调用参数的测试运行器。"""

        def __init__(self) -> None:
            """初始化调用记录。"""
            self.custom_calls: list[tuple[str, str]] = []

        def run_custom(self, command: str, project_path: str) -> object:
            """记录自定义命令和项目目录。

            Args:
                command: 待执行命令。
                project_path: 命令工作目录。

            Returns:
                测试占位对象。
            """
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
    item = window.global_commands.item(0)

    # 双击列表项时应调用运行器，而不是只选中列表项。
    window.global_commands.itemDoubleClicked.emit(item)

    assert runner.custom_calls == [("code .", str(project_dir))]

    window.close()
    app.processEvents()


def test_explorer_button_opens_selected_project_path(tmp_path, monkeypatch):
    """验证资源管理器按钮使用当前选中项目目录。

    Args:
        tmp_path: pytest 提供的临时目录。
        monkeypatch: pytest 提供的环境变量修改工具。
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.config_store import ConfigStore
    from command_launcher.models import AppConfig, Project
    from command_launcher.ui.main_window import MainWindow

    class FakeRunner:
        """记录资源管理器调用路径的测试运行器。"""

        def __init__(self) -> None:
            """初始化调用记录。"""
            self.explorer_calls: list[str] = []

        def run_explorer(self, project_path: str) -> object:
            """记录资源管理器打开路径。

            Args:
                project_path: 需要打开的项目目录。

            Returns:
                测试占位对象。
            """
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

    # 点击资源管理器按钮时必须使用配置里的项目目录。
    window.explorer_button.click()

    assert runner.explorer_calls == [str(project_dir)]

    window.close()
    app.processEvents()
