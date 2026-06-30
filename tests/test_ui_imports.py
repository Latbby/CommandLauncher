"""主窗口 UI 测试。"""

from pathlib import Path


def test_ui_modules_import():
    from command_launcher.app import create_app
    from command_launcher.ui.main_window import MainWindow

    assert create_app is not None
    assert MainWindow is not None


def test_main_window_exposes_command_edit_actions(tmp_path, monkeypatch):
    """验证主窗口暴露基础按钮和命令页签。

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
    assert window.add_command_button.menu() is None
    assert window.command_tabs.tabText(0) == "全局命令"
    assert window.command_tabs.tabText(1) == "项目命令"

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
    """验证主窗口使用全局/项目命令页签。

    入参: 空配置 + 临时目录
    出参: 命令页签和两个命令列表存在
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication, QListWidget, QSplitter, QTabWidget

    from command_launcher.config_store import ConfigStore
    from command_launcher.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(store=ConfigStore(tmp_path / "config.json"))

    # 主布局使用可拖动分栏
    assert isinstance(window.main_splitter, QSplitter)
    # 命令使用全局/项目页签分别展示
    assert isinstance(window.command_tabs, QTabWidget)
    assert isinstance(window.global_command_list, QListWidget)
    assert isinstance(window.project_command_list, QListWidget)

    # 样式对象名
    assert window.project_name.objectName() == "projectTitle"
    assert window.project_path.objectName() == "projectPath"
    assert window.remove_project_button.property("variant") == "danger"
    assert window.add_command_button.property("variant") == "secondary"

    window.close()
    app.processEvents()


def test_main_window_status_bar_warns_when_project_path_missing(tmp_path, monkeypatch):
    """验证项目路径不存在时禁用启动按钮且不显示底部状态栏。

    入参: 路径不存在的项目
    出参: 启动按钮禁用，底部状态栏隐藏
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
    assert window.statusBar().isHidden() is True

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
    # 命令列表、页签 + 列表内按钮
    assert "QTabWidget#commandTabs" in LIGHT_STYLESHEET
    assert "QListWidget#commandList" in LIGHT_STYLESHEET
    assert "QPushButton#itemActionBtn" in LIGHT_STYLESHEET
    # 签名元素：等宽路径
    assert "QLabel#projectPath" in LIGHT_STYLESHEET
    assert "Consolas" in LIGHT_STYLESHEET
    # 新配色
    assert "#5b5fe3" in LIGHT_STYLESHEET
    assert "#eeede8" in LIGHT_STYLESHEET


def test_main_window_uses_compact_panel_spacing(tmp_path, monkeypatch):
    """验证左右分栏和命令区域使用紧凑间距。

    入参: 空配置 + 临时目录
    出参: 分栏拖拽柄更窄，右侧内容左边距更小
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication, QFrame

    from command_launcher.config_store import ConfigStore
    from command_launcher.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(store=ConfigStore(tmp_path / "config.json"))
    content_panel = window.findChild(QFrame, "contentPanel")
    content_margins = content_panel.layout().contentsMargins()
    command_margins = window.command_tabs.parentWidget().layout().contentsMargins()

    assert window.main_splitter.handleWidth() == 8
    assert content_margins.left() == 8
    assert content_margins.bottom() == 8
    assert command_margins.left() == 0
    assert command_margins.right() == 0

    window.close()
    app.processEvents()


def test_command_list_uses_tight_item_spacing_and_larger_rows():
    """验证命令列表自身和列表项不再叠加大内边距。

    入参: LIGHT_STYLESHEET
    出参: 命令列表内边距、命令项边距和命令文字尺寸符合紧凑放大后的设计
    """
    from command_launcher.ui.styles import LIGHT_STYLESHEET

    assert "QListWidget#commandList {\n  font-family" in LIGHT_STYLESHEET
    assert "padding: 1px;" in LIGHT_STYLESHEET
    assert "QListWidget#commandList::item {\n  padding: 0px;" in LIGHT_STYLESHEET
    assert "margin: 0px;" in LIGHT_STYLESHEET
    assert "QLabel#commandName {\n  color: #1c1c22;\n  font-size: 15px;" in LIGHT_STYLESHEET


def test_command_item_widget_uses_larger_tight_layout(monkeypatch):
    """验证命令项控件减少左侧空白并增大行高。

    入参: 命令项控件
    出参: 行控件内边距更小，最小高度更大
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.ui.main_window import _CommandItemWidget

    app = QApplication.instance() or QApplication([])
    item_widget = _CommandItemWidget("cmd-1", "构建项目")
    margins = item_widget.layout().contentsMargins()

    assert margins.left() == 11
    assert margins.top() == 6
    assert margins.right() == 6
    assert margins.bottom() == 6
    assert item_widget.minimumHeight() == 42

    item_widget.close()
    app.processEvents()


def test_command_item_name_aligns_with_command_tab_text(monkeypatch):
    """验证命令文字去掉前缀并与页签文字左边缘对齐。

    入参: 命令项控件 + LIGHT_STYLESHEET
    出参: 命令名称没有 > 前缀，命令行左边距与页签文字左边距一致
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication, QLabel

    from command_launcher.ui.main_window import _CommandItemWidget
    from command_launcher.ui.styles import LIGHT_STYLESHEET

    app = QApplication.instance() or QApplication([])
    item_widget = _CommandItemWidget("cmd-1", "构建项目")
    name_label = item_widget.findChild(QLabel, "commandName")

    assert name_label.text() == "构建项目"
    assert "padding: 7px 12px;" in LIGHT_STYLESHEET
    assert item_widget.layout().contentsMargins().left() + 1 == 12

    item_widget.close()
    app.processEvents()


def test_command_list_hover_is_controlled_by_item_widget():
    """验证命令列表禁用原生悬浮背景绘制。

    入参: LIGHT_STYLESHEET
    出参: commandList 显式覆盖通用 QListWidget::item:hover 为透明背景
    """
    from command_launcher.ui.styles import LIGHT_STYLESHEET

    assert "QListWidget#commandList::item:hover" in LIGHT_STYLESHEET
    assert "background: transparent;" in LIGHT_STYLESHEET


def test_command_list_disables_native_selection_background():
    """验证命令列表禁用原生选中背景绘制。

    入参: LIGHT_STYLESHEET
    出参: commandList 显式覆盖通用 QListWidget::item:selected 为透明背景
    """
    from command_launcher.ui.styles import LIGHT_STYLESHEET

    assert "QListWidget#commandList::item:selected" in LIGHT_STYLESHEET
    assert "QListWidget#commandList::item:selected:active" in LIGHT_STYLESHEET
    assert "QListWidget#commandList::item:selected:!active" in LIGHT_STYLESHEET


def test_command_tabs_render_global_and_project_commands_separately(tmp_path, monkeypatch):
    """验证全局命令和项目命令分别展示在对应页签。

    入参: 包含一个全局命令和一个项目命令的配置
    出参: 全局列表和项目列表各显示自己的命令
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.config_store import ConfigStore
    from command_launcher.models import AppConfig, LaunchCommand, Project
    from command_launcher.ui.main_window import MainWindow

    project_dir = tmp_path / "selected-project"
    project_dir.mkdir()
    project = Project(
        name="选中项目",
        path=str(project_dir),
        commands=[LaunchCommand(name="项目构建", command="npm run build")],
    )
    global_command = LaunchCommand(name="打开编辑器", command="code .")
    store = ConfigStore(tmp_path / "config.json")
    store.save(
        AppConfig(
            projects=[project],
            global_commands=[global_command],
            last_selected_project_id=project.id,
        )
    )

    app = QApplication.instance() or QApplication([])
    window = MainWindow(store=store)

    assert window.global_command_list.count() == 1
    assert window.project_command_list.count() == 1
    assert window.global_command_list.item(0).data(1) == global_command.id
    assert window.project_command_list.item(0).data(1) == project.commands[0].id

    window.close()
    app.processEvents()


def test_add_command_button_uses_current_command_tab(tmp_path, monkeypatch):
    """验证添加按钮根据当前页签决定命令类型。

    入参: 切换全局/项目页签并点击添加按钮
    出参: 分别触发添加全局命令和添加项目命令
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.config_store import ConfigStore
    from command_launcher.ui.main_window import MainWindow

    calls: list[bool] = []

    app = QApplication.instance() or QApplication([])
    window = MainWindow(store=ConfigStore(tmp_path / "config.json"))
    window._add_command = calls.append

    window.command_tabs.setCurrentIndex(0)
    window.add_command_button.click()
    window.command_tabs.setCurrentIndex(1)
    window.add_command_button.click()

    assert calls == [True, False]

    window.close()
    app.processEvents()


def test_command_item_hover_only_toggles_action_buttons(monkeypatch):
    """验证命令项悬浮时只显示操作按钮，不渲染悬浮背景色。

    入参: 命令项控件 + 鼠标进入/离开事件
    出参: 操作按钮显示状态切换，控件背景色保持不变
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QEnterEvent, QPalette
    from PySide6.QtWidgets import QApplication, QPushButton

    from command_launcher.ui.main_window import _CommandItemWidget

    app = QApplication.instance() or QApplication([])
    item_widget = _CommandItemWidget("cmd-1", "构建项目")
    action_buttons = item_widget.findChildren(QPushButton, "itemActionBtn")
    initial_color = item_widget.palette().color(QPalette.Window)

    item_widget.enterEvent(QEnterEvent(QPointF(), QPointF(), QPointF()))
    hovered_color = item_widget.palette().color(QPalette.Window)

    assert all(not button.isHidden() for button in action_buttons)
    assert hovered_color == initial_color

    item_widget.leaveEvent(None)
    left_color = item_widget.palette().color(QPalette.Window)

    assert all(button.isHidden() for button in action_buttons)
    assert left_color == initial_color

    item_widget.close()
    app.processEvents()


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

    # 获取全局命令列表中的 _CommandItemWidget
    item_widget = window.global_command_list.itemWidget(window.global_command_list.item(0))
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
