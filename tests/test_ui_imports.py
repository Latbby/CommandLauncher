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
