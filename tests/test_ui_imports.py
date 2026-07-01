"""主窗口 UI 测试。"""

from pathlib import Path


def test_ui_modules_import():
    from command_launcher.app import create_app
    from command_launcher.ui.main_window import MainWindow

    assert create_app is not None
    assert MainWindow is not None


def test_app_icon_path_points_to_packaged_icon_asset():
    """验证应用图标路径解析到项目内的 ico 文件。

    入参: 当前项目目录
    出参: app_icon_path 返回存在的 assets/icon.ico
    """
    from command_launcher.resources import app_icon_path

    icon_path = app_icon_path()

    assert icon_path.name == "icon.ico"
    assert icon_path.parent.name == "assets"
    assert icon_path.exists()


def test_main_window_exposes_builtin_buttons_and_add_global_chip(tmp_path, monkeypatch):
    """验证主窗口暴露内置按钮，全局命令流式布局中存在添加芯片。

    入参: 空配置 + 临时目录
    出参: 内置按钮文案正确，添加全局命令芯片在流式布局末尾
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.config_store import ConfigStore
    from command_launcher.ui.main_window import _AddGlobalCommandChip, MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(store=ConfigStore(tmp_path / "config.json"))

    assert window.cmd_button.text() == "打开命令提示符"
    assert window.powershell_button.text() == "打开 PowerShell"
    assert window.explorer_button.text() == "打开资源管理器"
    # 添加全局命令芯片在流式布局末尾
    add_chips = window.global_commands_widget.findChildren(_AddGlobalCommandChip)
    assert len(add_chips) == 1
    assert add_chips[0].text() == "＋ 添加全局命令"

    window.close()
    app.processEvents()


def test_command_dialog_uses_command_editor_polish(monkeypatch):
    """验证命令对话框使用编辑器轻量美化。

    入参: 新增模式和编辑模式 CommandDialog
    出参: 标题、宽度、占位文案、等宽字体、按钮文案和按钮变体正确
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QDialogButtonBox, QPlainTextEdit

    from command_launcher.models import LaunchCommand
    from command_launcher.ui.dialogs import CommandDialog

    app = QApplication.instance() or QApplication([])
    dialog = CommandDialog()
    edit_dialog = CommandDialog(LaunchCommand(name="启动服务", command="npm run dev"))
    buttons = dialog.findChild(QDialogButtonBox)

    assert dialog.windowTitle() == "添加命令"
    assert edit_dialog.windowTitle() == "编辑命令"
    assert dialog.minimumWidth() == 760
    assert dialog.name_input.placeholderText() == "例如：启动前端"
    assert dialog.command_input.placeholderText() == "例如：npm run dev"
    assert dialog.command_input.minimumHeight() == 220
    assert dialog.command_input.lineWrapMode() == QPlainTextEdit.NoWrap
    assert dialog.command_input.horizontalScrollBarPolicy() == Qt.ScrollBarAsNeeded
    assert dialog.command_input.font().fixedPitch() is True
    # 编辑模式：命令文本正确回填
    assert edit_dialog.command_input.toPlainText() == "npm run dev"
    assert buttons.button(QDialogButtonBox.Ok).text() == "保存"
    assert buttons.button(QDialogButtonBox.Cancel).text() == "取消"
    assert buttons.button(QDialogButtonBox.Ok).property("variant") == "primary"
    assert buttons.button(QDialogButtonBox.Cancel).property("variant") == "secondary"

    dialog.close()
    edit_dialog.close()
    app.processEvents()


def test_command_dialog_preserves_multiline_command_text(monkeypatch):
    """验证命令编辑框保存时保留多行命令原文。

    入参: 多行命令文本
    出参: command_values 返回去除首尾空白但保留中间换行的命令文本
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.ui.dialogs import CommandDialog

    app = QApplication.instance() or QApplication([])
    dialog = CommandDialog()

    dialog.name_input.setText("启动服务")
    dialog.command_input.setPlainText("  npm run build\nnpm run dev  ")

    assert dialog.command_values() == ("启动服务", "npm run build\nnpm run dev")

    dialog.close()
    app.processEvents()


def test_main_window_corner_tools_open_github_repository(tmp_path, monkeypatch):
    """验证右下角工具区 GitHub 按钮打开仓库地址。

    入参: 点击 GitHub 按钮
    出参: 调用系统浏览器打开项目仓库 URL
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import QApplication

    from command_launcher.config_store import ConfigStore
    from command_launcher.ui.main_window import MainWindow

    opened_urls: list[str] = []
    monkeypatch.setattr(
        QDesktopServices,
        "openUrl",
        lambda url: opened_urls.append(url.toString()) or True,
    )

    app = QApplication.instance() or QApplication([])
    window = MainWindow(store=ConfigStore(tmp_path / "config.json"))

    assert window.github_button.text() == ""
    assert window.github_button.icon().isNull() is False
    assert window.github_button.property("variant") is None
    assert window.github_button.toolTip() == "打开 GitHub 仓库"

    window.github_button.click()

    assert opened_urls == ["https://github.com/Latbby/CommandLauncher.git"]

    window.close()
    app.processEvents()


def test_settings_dialog_uses_control_panel_cards(monkeypatch):
    """验证设置对话框使用符合主界面风格的控制面板卡片。

    入参: SettingsDialog
    出参: 弹窗标题、副标题、设置卡片和关闭行为行存在
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication, QFrame, QLabel

    from command_launcher.ui.dialogs import SettingsDialog

    app = QApplication.instance() or QApplication([])
    dialog = SettingsDialog()

    labels = dialog.findChildren(QLabel)
    obj_names = {l.objectName() for l in labels}
    cards = dialog.findChildren(QFrame, "settingsCard")

    assert dialog.minimumWidth() == 480
    assert dialog.maximumWidth() == 480
    assert dialog.objectName() == "settingsDialog"
    assert "settingsTitle" in obj_names
    assert "settingsSubtitle" in obj_names
    assert "settingsCardTitle" in obj_names
    assert "settingsCardHint" in obj_names
    assert len(cards) == 2
    assert dialog.findChild(QFrame, "settingsCloseActionRow") is not None

    dialog.close()
    app.processEvents()


def test_settings_dialog_controls_auto_start_and_close_action(monkeypatch):
    """验证设置对话框控件的默认值和交互。

    入参: SettingsDialog(auto_start=True, close_action="minimize")
    出参: 复选框已勾选，下拉框选中对应项，可读取用户选择
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.ui.dialogs import SettingsDialog

    app = QApplication.instance() or QApplication([])
    dialog = SettingsDialog(auto_start=True, close_action="minimize")

    assert dialog.windowTitle() == "设置"
    assert dialog.auto_start() is True
    assert dialog.close_action() == "minimize"
    # 确认下拉框有 3 个选项
    assert dialog.close_combo.count() == 3
    # 确认当前选中项文本正确
    assert dialog.close_combo.currentText() == "最小化到系统托盘"

    dialog.close()
    app.processEvents()


def test_settings_dialog_close_combo_uses_clean_flat_border(monkeypatch):
    """验证设置弹窗关闭行为下拉框使用干净的单层边框。

    入参: SettingsDialog 和 LIGHT_STYLESHEET
    出参: 下拉框具备专用对象名，样式覆盖原生下拉边框
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.ui.dialogs import SettingsDialog
    from command_launcher.ui.styles import LIGHT_STYLESHEET

    app = QApplication.instance() or QApplication([])
    dialog = SettingsDialog()

    assert dialog.close_combo.objectName() == "settingsCloseCombo"
    assert "QComboBox#settingsCloseCombo" in LIGHT_STYLESHEET
    assert "QComboBox#settingsCloseCombo::drop-down" in LIGHT_STYLESHEET
    assert "border: none;" in LIGHT_STYLESHEET

    dialog.close()
    app.processEvents()


def test_github_button_renders_as_borderless_logo():
    """验证 GitHub 入口只展示无边框 logo。

    入参: LIGHT_STYLESHEET
    出参: GitHub 按钮使用透明背景和无边框样式
    """
    from command_launcher.ui.styles import LIGHT_STYLESHEET

    assert "QPushButton#githubButton" in LIGHT_STYLESHEET
    assert "background: transparent;" in LIGHT_STYLESHEET
    assert "border: none;" in LIGHT_STYLESHEET


def test_main_window_theme_switch_toggles_light_and_dark_styles(tmp_path, monkeypatch):
    """验证主窗口主题开关可在浅色和深色间运行时切换。

    入参: 拖动主题开关到深色再回到浅色
    出参: 应用样式表分别切换为深色和浅色样式
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QSlider

    from command_launcher.config_store import ConfigStore
    from command_launcher.ui.main_window import MainWindow
    from command_launcher.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET

    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(LIGHT_STYLESHEET)
    window = MainWindow(store=ConfigStore(tmp_path / "config.json"))

    assert isinstance(window.theme_switch, QSlider)
    assert window.theme_switch.orientation() == Qt.Horizontal
    assert window.theme_switch.minimum() == 0
    assert window.theme_switch.maximum() == 1
    assert window.theme_switch.value() == 0

    window.theme_switch.setValue(1)
    assert app.styleSheet() == DARK_STYLESHEET

    window.theme_switch.setValue(0)
    assert app.styleSheet() == LIGHT_STYLESHEET

    window.close()
    app.processEvents()


def test_theme_switch_click_toggles_to_other_theme(tmp_path, monkeypatch):
    """验证点击主题开关任意位置会切换到另一种主题。

    入参: 主题开关鼠标左键点击事件
    出参: 浅色切深色，再次点击切回浅色
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtWidgets import QApplication

    from command_launcher.config_store import ConfigStore
    from command_launcher.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(store=ConfigStore(tmp_path / "config.json"))
    click_event = QMouseEvent(
        QEvent.MouseButtonPress,
        QPointF(2, 2),
        QPointF(2, 2),
        QPointF(2, 2),
        Qt.LeftButton,
        Qt.LeftButton,
        Qt.NoModifier,
    )

    window.theme_switch.mousePressEvent(click_event)
    assert window.theme_switch.value() == 1

    window.theme_switch.mousePressEvent(click_event)
    assert window.theme_switch.value() == 0

    window.close()
    app.processEvents()


def test_dark_stylesheet_contains_expected_palette():
    """验证深色样式包含约定的关键调色板。

    入参: DARK_STYLESHEET
    出参: 背景、面板、输入、主文字、次级文字和主色均存在
    """
    from command_launcher.ui.styles import DARK_STYLESHEET

    assert "#15161a" in DARK_STYLESHEET
    assert "#202127" in DARK_STYLESHEET
    assert "#262832" in DARK_STYLESHEET
    assert "#f3f4f8" in DARK_STYLESHEET
    assert "#a5a7b3" in DARK_STYLESHEET
    assert "#7c83ff" in DARK_STYLESHEET


def test_dark_stylesheet_uses_card_and_chip_selectors():
    """验证深色主题使用卡片和芯片样式替代旧的命令列表样式。

    入参: DARK_STYLESHEET
    出参: 深色主题包含 projectCard、cardTitle、addGlobalChip 等新选择器
    """
    from command_launcher.ui.styles import DARK_STYLESHEET

    assert "QFrame#projectCard" in DARK_STYLESHEET
    assert "QLabel#cardTitle" in DARK_STYLESHEET
    assert "QLabel#cardCommand" in DARK_STYLESHEET
    assert "QPushButton#addGlobalChip" in DARK_STYLESHEET
    assert "QPushButton#cardActionBtn" in DARK_STYLESHEET
    # 旧选择器已移除
    assert "QTabWidget#commandTabs" not in DARK_STYLESHEET
    assert "QListWidget#commandList" not in DARK_STYLESHEET


def test_light_stylesheet_styles_theme_switch():
    """验证默认浅色主题下主题开关有可辨识的滑块样式。

    入参: LIGHT_STYLESHEET
    出参: 浅色主题包含 themeSwitch 轨道和手柄样式，并使用明确区分的轨道与手柄颜色
    """
    from command_launcher.ui.styles import LIGHT_STYLESHEET

    assert "QSlider#themeSwitch::groove:horizontal" in LIGHT_STYLESHEET
    assert "QSlider#themeSwitch::handle:horizontal" in LIGHT_STYLESHEET
    assert "background: #eceafe;" in LIGHT_STYLESHEET
    assert "background: #5b5fe3;" in LIGHT_STYLESHEET


def test_main_window_uses_flow_layout_for_commands(tmp_path, monkeypatch):
    """验证主窗口使用流式布局和卡片替代旧的页签列表。

    入参: 空配置 + 临时目录
    出参: 全局命令流式容器、项目命令卡片滚动区域和添加按钮存在
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication, QScrollArea, QSplitter

    from command_launcher.config_store import ConfigStore
    from command_launcher.ui.main_window import (
        FlowLayout,
        MainWindow,
        _AddGlobalCommandChip,
    )

    app = QApplication.instance() or QApplication([])
    window = MainWindow(store=ConfigStore(tmp_path / "config.json"))

    # 主布局使用可拖动分栏
    assert isinstance(window.main_splitter, QSplitter)
    # 全局命令使用流式布局
    assert isinstance(window.global_commands_flow, FlowLayout)
    # 添加全局命令芯片存在
    add_chips = window.global_commands_widget.findChildren(_AddGlobalCommandChip)
    assert len(add_chips) == 1
    assert add_chips[0].text() == "＋ 添加全局命令"
    # 项目命令使用卡片滚动区域（垂直布局）
    assert isinstance(window.project_cards_scroll, QScrollArea)
    assert isinstance(window.project_cards_flow, FlowLayout)
    # 添加项目命令按钮存在
    assert window.add_project_command_button.text() == "添加项目命令"

    # 样式对象名
    assert window.project_name.objectName() == "projectTitle"
    assert window.project_path.objectName() == "projectPath"
    assert window.remove_project_button.property("variant") == "danger"
    assert window.add_project_command_button.property("variant") == "secondary"

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


def test_light_stylesheet_contains_card_and_chip_selectors():
    """验证现代化界面依赖的卡片和芯片样式选择器存在。

    入参: 无
    出参: 面板、按钮变体、卡片、芯片、等宽字体、配色选择器均存在
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
    # 新卡片和芯片选择器
    assert "QFrame#projectCard" in LIGHT_STYLESHEET
    assert "QLabel#cardTitle" in LIGHT_STYLESHEET
    assert "QLabel#cardCommand" in LIGHT_STYLESHEET
    assert "QPushButton#addGlobalChip" in LIGHT_STYLESHEET
    assert "QPushButton#cardActionBtn" in LIGHT_STYLESHEET
    # 旧页签/命令列表选择器已移除
    assert "QTabWidget#commandTabs" not in LIGHT_STYLESHEET
    assert "QListWidget#commandList" not in LIGHT_STYLESHEET
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
    # 全局命令流式容器直接挂在命令区域下
    global_margins = window.global_commands_widget.layout().contentsMargins()

    assert window.main_splitter.handleWidth() == 8
    assert content_margins.left() == 8
    assert content_margins.bottom() == 8
    # 全局命令流式布局无边距
    assert global_margins.left() == 0
    assert global_margins.right() == 0

    window.close()
    app.processEvents()


# ── 全局命令芯片测试 ────────────────────────────────────────────

def test_global_command_chip_click_emits_run(monkeypatch):
    """验证点击全局命令芯片发出运行信号。

    入参: 全局命令芯片 + 鼠标左键点击
    出参: 发出 run_requested 信号并携带命令 ID
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.ui.main_window import _GlobalCommandChip

    app = QApplication.instance() or QApplication([])
    chip = _GlobalCommandChip("global-1", "测试命令")
    run_requests: list[str] = []
    chip.run_requested.connect(run_requests.append)

    chip.click()

    assert run_requests == ["global-1"]

    chip.close()
    app.processEvents()


def test_global_command_chip_uses_secondary_fill_variant(monkeypatch):
    """验证全局命令芯片使用 secondary-fill 变体样式。

    入参: 全局命令芯片
    出参: variant 属性为 secondary-fill
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.ui.main_window import _GlobalCommandChip

    app = QApplication.instance() or QApplication([])
    chip = _GlobalCommandChip("cmd-1", "构建项目")

    assert chip.property("variant") == "secondary-fill"
    assert chip.text() == "构建项目"

    chip.close()
    app.processEvents()


def test_add_global_command_chip_emits_add_requested(monkeypatch):
    """验证添加全局命令芯片点击发出添加请求。

    入参: 添加全局命令芯片 + 鼠标左键点击
    出参: 发出 add_requested 信号
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.ui.main_window import _AddGlobalCommandChip

    app = QApplication.instance() or QApplication([])
    chip = _AddGlobalCommandChip()
    add_requests: list[bool] = []
    chip.add_requested.connect(lambda: add_requests.append(True))

    chip.click()

    assert add_requests == [True]
    assert chip.text() == "＋ 添加全局命令"

    chip.close()
    app.processEvents()


def test_add_global_chip_uses_dashed_border_object_name(monkeypatch):
    """验证添加全局命令芯片使用专用的虚线边框样式对象名。

    入参: 添加全局命令芯片
    出参: objectName 为 addGlobalChip，用于虚线边框样式
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.ui.main_window import _AddGlobalCommandChip

    app = QApplication.instance() or QApplication([])
    chip = _AddGlobalCommandChip()

    assert chip.objectName() == "addGlobalChip"

    chip.close()
    app.processEvents()


# ── 项目命令卡片测试 ────────────────────────────────────────────

def test_project_command_card_displays_name_and_command(monkeypatch):
    """验证项目命令卡片展示命令名称和命令文本。

    入参: 项目命令卡片
    出参: 卡片内包含名称标签和命令文本标签
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication, QLabel

    from command_launcher.ui.main_window import _ProjectCommandCard

    app = QApplication.instance() or QApplication([])
    card = _ProjectCommandCard("card-1", "启动服务", "npm run dev")
    labels = card.findChildren(QLabel)

    title_texts = [l.text() for l in labels if l.objectName() == "cardTitle"]
    cmd_texts = [l.text() for l in labels if l.objectName() == "cardCommand"]

    assert "启动服务" in title_texts
    assert "npm run dev" in cmd_texts
    assert card.objectName() == "projectCard"
    assert card.width() == 278   # 固定卡片宽度
    assert card.height() == 122  # 固定卡片高度

    card.close()
    app.processEvents()


def test_project_command_card_click_emits_run(monkeypatch):
    """验证点击项目命令卡片发出运行信号。

    入参: 项目命令卡片 + 鼠标左键点击
    出参: 发出 run_requested 信号并携带命令 ID
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtWidgets import QApplication

    from command_launcher.ui.main_window import _ProjectCommandCard

    app = QApplication.instance() or QApplication([])
    card = _ProjectCommandCard("card-1", "启动服务", "npm run dev")
    run_requests: list[str] = []
    card.run_requested.connect(run_requests.append)

    event = QMouseEvent(
        QEvent.MouseButtonPress,
        QPointF(10, 10),
        QPointF(10, 10),
        QPointF(10, 10),
        Qt.LeftButton,
        Qt.LeftButton,
        Qt.NoModifier,
    )
    card.mousePressEvent(event)

    assert run_requests == ["card-1"]

    card.close()
    app.processEvents()


def test_project_command_card_hover_toggles_action_buttons(monkeypatch):
    """验证项目命令卡片悬浮时原地替换为操作按钮。

    入参: 项目命令卡片 + 鼠标进入/离开事件
    出参: 堆叠控件在悬浮时切换到按钮面板，离开后切回代码块
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QEnterEvent
    from PySide6.QtWidgets import QApplication

    from command_launcher.ui.main_window import _ProjectCommandCard

    app = QApplication.instance() or QApplication([])
    card = _ProjectCommandCard("card-1", "构建项目", "npm run build")

    # 初始状态：显示命令代码块（第 0 层）
    assert card._stack.currentIndex() == 0

    # 鼠标进入：原地替换为操作按钮面板（第 1 层）
    card.enterEvent(QEnterEvent(QPointF(), QPointF(), QPointF()))
    assert card._stack.currentIndex() == 1

    # 鼠标离开：恢复显示命令代码块
    card.leaveEvent(None)
    assert card._stack.currentIndex() == 0

    card.close()
    app.processEvents()


def test_project_command_card_edit_button_emits_signal(monkeypatch):
    """验证项目命令卡片编辑按钮发出编辑信号。

    入参: 项目命令卡片 + 悬浮后点击编辑按钮
    出参: 发出 edit_requested 信号并携带命令 ID
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QEnterEvent
    from PySide6.QtWidgets import QApplication, QPushButton

    from command_launcher.ui.main_window import _ProjectCommandCard

    app = QApplication.instance() or QApplication([])
    card = _ProjectCommandCard("card-1", "启动服务", "npm run dev")
    edit_requests: list[str] = []
    card.edit_requested.connect(edit_requests.append)

    # 先悬浮以切换到按钮面板
    card.enterEvent(QEnterEvent(QPointF(), QPointF(), QPointF()))
    # 找到按钮面板中的编辑按钮并点击
    edit_btn = card.findChildren(QPushButton, "cardActionBtn")[0]
    edit_btn.click()

    assert edit_requests == ["card-1"]

    card.close()
    app.processEvents()


# ── 全局命令和项目命令数据分离测试 ──────────────────────────────

def test_global_and_project_commands_rendered_in_respective_containers(tmp_path, monkeypatch):
    """验证全局命令以芯片展示，项目命令以卡片展示。

    入参: 包含一个全局命令和一个项目命令的配置
    出参: 全局命令在流式布局中，项目命令在卡片区域中
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.config_store import ConfigStore
    from command_launcher.models import AppConfig, LaunchCommand, Project
    from command_launcher.ui.main_window import _GlobalCommandChip, _ProjectCommandCard, MainWindow

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

    # 全局命令以芯片展示（+1 是添加按钮）
    global_chips = window.global_commands_widget.findChildren(_GlobalCommandChip)
    assert len(global_chips) == 1
    assert global_chips[0].text() == "打开编辑器"

    # 项目命令以卡片展示
    project_cards = window.project_cards_widget.findChildren(_ProjectCommandCard)
    assert len(project_cards) == 1

    window.close()
    app.processEvents()


def test_add_global_chip_triggers_global_command_dialog(tmp_path, monkeypatch):
    """验证添加全局命令芯片触发添加全局命令。

    入参: 点击添加全局命令芯片
    出参: _add_command 被调用并传入 global_command=True
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.config_store import ConfigStore
    from command_launcher.ui.main_window import _AddGlobalCommandChip, MainWindow

    calls: list[bool] = []

    app = QApplication.instance() or QApplication([])
    window = MainWindow(store=ConfigStore(tmp_path / "config.json"))
    window._add_command = calls.append

    # 获取流式布局中的添加全局命令芯片并点击
    add_chips = window.global_commands_widget.findChildren(_AddGlobalCommandChip)
    add_chips[0].click()

    assert calls == [True]

    window.close()
    app.processEvents()


def test_add_project_command_button_triggers_project_command_dialog(tmp_path, monkeypatch):
    """验证添加项目命令按钮触发添加项目命令。

    入参: 点击添加项目命令按钮
    出参: _add_command 被调用并传入 global_command=False
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.config_store import ConfigStore
    from command_launcher.ui.main_window import MainWindow

    calls: list[bool] = []

    app = QApplication.instance() or QApplication([])
    window = MainWindow(store=ConfigStore(tmp_path / "config.json"))
    window._add_command = calls.append

    window.add_project_command_button.click()

    assert calls == [False]

    window.close()
    app.processEvents()


def test_click_global_command_runs_from_selected_project(tmp_path, monkeypatch):
    """验证全局命令芯片点击后从选中项目目录运行。

    入参: 包含全局命令和项目的配置
    出参: 全局命令从项目目录启动
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.config_store import ConfigStore
    from command_launcher.models import AppConfig, LaunchCommand, Project
    from command_launcher.ui.main_window import _GlobalCommandChip, MainWindow

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

    # 获取全局命令芯片并点击
    chip = window.global_commands_widget.findChildren(_GlobalCommandChip)[0]
    chip.click()

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


def test_project_commands_hidden_when_no_project_selected(tmp_path, monkeypatch):
    """验证无项目选中时隐藏项目命令区域。

    入参: 无项目配置
    出参: 项目命令标题、卡片区域和添加按钮隐藏
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from command_launcher.config_store import ConfigStore
    from command_launcher.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow(store=ConfigStore(tmp_path / "config.json"))

    assert window.project_commands_title.isHidden() or not window.project_commands_title.isVisible()
    assert window.project_cards_scroll.isHidden() or not window.project_cards_scroll.isVisible()
    assert window.add_project_command_button.isHidden() or not window.add_project_command_button.isVisible()

    window.close()
    app.processEvents()


def test_add_global_chip_styled_with_dashed_border():
    """验证添加全局命令芯片样式使用虚线边框。

    入参: LIGHT_STYLESHEET
    出参: addGlobalChip 选择器包含 dashed 边框样式
    """
    from command_launcher.ui.styles import LIGHT_STYLESHEET

    assert "QPushButton#addGlobalChip" in LIGHT_STYLESHEET
    assert "dashed" in LIGHT_STYLESHEET


def test_project_card_styled_with_rounded_corners():
    """验证项目命令卡片使用圆角、边框、强调条和代码块样式。

    入参: LIGHT_STYLESHEET
    出参: projectCard、cardStripe、cardCodeBlock 选择器存在
    """
    from command_launcher.ui.styles import LIGHT_STYLESHEET

    assert "QFrame#projectCard" in LIGHT_STYLESHEET
    assert "border-radius: 8px;" in LIGHT_STYLESHEET
    assert "border: 1px solid" in LIGHT_STYLESHEET
    # 签名元素：左侧强调条
    assert "QFrame#cardStripe" in LIGHT_STYLESHEET
    assert "background: #5b5fe3;" in LIGHT_STYLESHEET
    # 命令代码块
    assert "QFrame#cardCodeBlock" in LIGHT_STYLESHEET
    # 设置对话框样式
    assert "QLabel#settingsTitle" in LIGHT_STYLESHEET
    assert "QLabel#settingsSubtitle" in LIGHT_STYLESHEET
    assert "QFrame#settingsCard" in LIGHT_STYLESHEET
    assert "QFrame#settingsCloseActionRow" in LIGHT_STYLESHEET
    assert "QLabel#settingsCardHint" in LIGHT_STYLESHEET
    assert "QCheckBox" in LIGHT_STYLESHEET
    assert "QComboBox" in LIGHT_STYLESHEET


def test_flow_layout_wraps_items_to_next_row(monkeypatch):
    """验证 FlowLayout 在空间不足时自动换行。

    入参: FlowLayout + 两个按钮
    出参: 布局的 heightForWidth 在宽度足够时低，在宽度不够时高（换行）
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication, QPushButton

    from command_launcher.ui.main_window import FlowLayout

    app = QApplication.instance() or QApplication([])
    container = QPushButton()  # 用作父控件
    flow = FlowLayout(container)
    btn1 = QPushButton("命令 A")
    btn2 = QPushButton("命令 B")
    flow.addWidget(btn1)
    flow.addWidget(btn2)

    # 宽度足够时单行高度
    single_row_height = flow.heightForWidth(500)
    # 宽度很小时强制换行，高度应大于单行
    wrapped_height = flow.heightForWidth(50)

    assert wrapped_height > single_row_height

    flow.removeWidget(btn1)
    flow.removeWidget(btn2)
    btn1.close()
    btn2.close()
    container.close()
    app.processEvents()
