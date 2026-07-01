"""Main Project Launcher window."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QByteArray, QPoint, QRect, QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLayoutItem,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSplitter,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from command_launcher.command_runner import CommandRunner
from command_launcher.config_store import ConfigStore
from command_launcher.models import AppConfig, LaunchCommand, Project
from command_launcher.resources import app_icon_path
from command_launcher.ui.dialogs import CloseConfirmDialog, CommandDialog
from command_launcher.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


def _github_mark_icon(dark_mode: bool = False) -> QIcon:
    """根据 GitHub 官方 mark 轮廓绘制仓库入口图标。

    Args:
        dark_mode: True 时使用适合深色主题的浅色图标。

    Returns:
        可直接设置到按钮上的 GitHub 标识图标。
    """
    icon_color = "#f3f4f8" if dark_mode else "#24292f"
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)

    svg = f"""
    <svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
      <path fill="{icon_color}" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82A7.65 7.65 0 0 1 8 3.86c.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8Z"/>
    </svg>
    """
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


def _gear_icon(dark_mode: bool = False) -> QIcon:
    """绘制设置齿轮图标。

    Args:
        dark_mode: True 时使用适合深色主题的浅色图标。

    Returns:
        可直接设置到按钮上的齿轮图标。
    """
    icon_color = "#f3f4f8" if dark_mode else "#5c5a6e"
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)

    svg = f"""
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path fill="{icon_color}" d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58a.49.49 0 0 0 .12-.61l-1.92-3.32a.49.49 0 0 0-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.484.484 0 0 0-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.07.62-.07.94s.02.64.07.94l-2.03 1.58a.49.49 0 0 0-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6A3.6 3.6 0 1 1 12 8.4a3.6 3.6 0 0 1 0 7.2z"/>
    </svg>
    """
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


# ── 流式布局：根据容器宽度自动换行 ──────────────────────────────────

class FlowLayout(QLayout):
    """自适应流式布局，根据容器宽度自动换行。

    子控件从左到右排列，空间不足时自动折行。
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """初始化流式布局。

        Args:
            parent: 可选的 Qt 父控件。
        """
        super().__init__(parent)
        self._items: list[QLayoutItem] = []
        self._h_spacing = 8
        self._v_spacing = 8

    def __del__(self) -> None:
        """析构时清理所有布局项。"""
        while self.count():
            self.takeAt(0)

    def addItem(self, item: QLayoutItem) -> None:
        """向布局末尾添加一个布局项。

        Args:
            item: Qt 布局项。
        """
        self._items.append(item)

    def count(self) -> int:
        """返回布局中的项目数量。"""
        return len(self._items)

    def itemAt(self, index: int) -> QLayoutItem | None:
        """返回指定索引的布局项。

        Args:
            index: 项索引。

        Returns:
            布局项或 None。
        """
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int) -> QLayoutItem | None:
        """移除并返回指定索引的布局项。

        Args:
            index: 项索引。

        Returns:
            被移除的布局项或 None。
        """
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self) -> Qt.Orientations:
        """流式布局不向任何方向扩展。"""
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        """高度依赖于可用宽度。"""
        return True

    def heightForWidth(self, width: int) -> int:
        """计算给定宽度下的所需高度。

        Args:
            width: 可用宽度（像素）。

        Returns:
            所需高度（像素）。
        """
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def sizeHint(self) -> QSize:
        """返回布局的建议尺寸。"""
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        """返回布局的最小尺寸。"""
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def setGeometry(self, rect: QRect) -> None:
        """设置布局几何并执行流式排列。

        Args:
            rect: 布局的矩形区域。
        """
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        """执行流式布局计算，返回所需总高度。

        Args:
            rect: 布局矩形区域。
            test_only: True 时仅计算高度不移动控件。

        Returns:
            布局所需的总高度（像素）。
        """
        margins = self.contentsMargins()
        effective = rect.adjusted(
            margins.left(), margins.top(), -margins.right(), -margins.bottom()
        )
        x = effective.x()
        y = effective.y()
        line_height = 0

        for item in self._items:
            item_size = item.sizeHint()
            # 当前行放不下且已有内容时换行
            if x + item_size.width() > effective.right() and line_height > 0:
                x = effective.x()
                y += line_height + self._v_spacing
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item_size))

            x += item_size.width() + self._h_spacing
            line_height = max(line_height, item_size.height())

        return y + line_height - rect.y() + margins.bottom()


# ── 全局命令芯片：点击运行，右键编辑/删除 ──────────────────────────

class _GlobalCommandChip(QPushButton):
    """全局命令芯片控件，点击运行命令，右键弹出编辑/删除菜单。

    信号:
        edit_requested(str): 用户选择编辑，携带命令 ID。
        delete_requested(str): 用户选择删除，携带命令 ID。
        run_requested(str): 用户点击芯片，携带命令 ID。
    """

    edit_requested = Signal(str)
    delete_requested = Signal(str)
    run_requested = Signal(str)

    def __init__(
        self,
        command_id: str,
        command_name: str,
        parent: QWidget | None = None,
    ) -> None:
        """初始化全局命令芯片。

        Args:
            command_id: 命令唯一标识。
            command_name: 命令显示名称。
            parent: 可选的 Qt 父控件。
        """
        super().__init__(command_name, parent)
        self._command_id = command_id
        self.setProperty("variant", "secondary-fill")
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(lambda: self.run_requested.emit(self._command_id))
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos: QPoint) -> None:
        """弹出右键上下文菜单（编辑/删除）。

        Args:
            pos: 鼠标点击位置。
        """
        menu = QMenu(self)
        edit_action = menu.addAction("编辑")
        delete_action = menu.addAction("删除")
        action = menu.exec(self.mapToGlobal(pos))
        if action == edit_action:
            self.edit_requested.emit(self._command_id)
        elif action == delete_action:
            self.delete_requested.emit(self._command_id)


# ── 添加全局命令按钮：位于全局命令芯片末尾 ────────────────────────

class _AddGlobalCommandChip(QPushButton):
    """添加全局命令按钮，使用虚线边框和加号图标区分于普通命令芯片。"""

    add_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """初始化添加全局命令按钮。"""
        super().__init__("＋ 添加全局命令", parent)
        self.setObjectName("addGlobalChip")
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self.add_requested.emit)


# ── 项目命令卡片 ──────────────────────────────────────────────────

class _ProjectCommandCard(QFrame):
    """项目命令卡片控件，展示命令名称、命令文本和操作按钮。

    卡片左侧有靛蓝色强调条。鼠标悬浮时，命令代码块原地替换为操作按钮，
    卡片高度保持不变。

    信号:
        edit_requested(str): 用户点击编辑按钮，携带命令 ID。
        delete_requested(str): 用户点击删除按钮，携带命令 ID。
        run_requested(str): 用户点击卡片，携带命令 ID。
    """

    edit_requested = Signal(str)
    delete_requested = Signal(str)
    run_requested = Signal(str)

    # 卡片尺寸 — 宽高固定，保证网格整齐、高度恒定
    CARD_WIDTH = 278
    CARD_HEIGHT = 122
    # 代码块/按钮面板的固定高度 — 容纳约 2 行等宽文字
    CODE_AREA_HEIGHT = 52

    def __init__(
        self,
        command_id: str,
        command_name: str,
        command_text: str,
        parent: QWidget | None = None,
    ) -> None:
        """初始化项目命令卡片。

        Args:
            command_id: 命令唯一标识。
            command_name: 命令显示名称。
            command_text: 实际命令文本。
            parent: 可选的 Qt 父控件。
        """
        super().__init__(parent)
        self._command_id = command_id
        self.setObjectName("projectCard")
        self.setFixedWidth(self.CARD_WIDTH)
        self.setFixedHeight(self.CARD_HEIGHT)
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)

        # ── 卡片主体水平布局：左侧强调条 + 右侧内容区 ──
        card_layout = QHBoxLayout(self)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # 左侧强调条 — 3px 靛蓝竖线，致敬代码编辑器变更标记
        stripe = QFrame()
        stripe.setObjectName("cardStripe")
        stripe.setFixedWidth(3)
        card_layout.addWidget(stripe)

        # 右侧内容区
        content = QWidget()
        content.setMouseTracking(True)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(14, 12, 14, 10)
        content_layout.setSpacing(8)

        # 命令名称 — 上限 2 行，超出省略
        name_label = QLabel(command_name)
        name_label.setObjectName("cardTitle")
        name_label.setWordWrap(True)
        name_label.setMaximumHeight(38)  # 上限约 2 行 (14px × 2 + 行距)
        content_layout.addWidget(name_label)

        # ── 可切换区域：命令代码块 ↔ 操作按钮 ──
        self._stack = QStackedWidget()
        self._stack.setObjectName("cardStack")
        self._stack.setFixedHeight(self.CODE_AREA_HEIGHT)

        # 第 0 层：命令代码块
        code_block = QFrame()
        code_block.setObjectName("cardCodeBlock")
        code_block_layout = QVBoxLayout(code_block)
        code_block_layout.setContentsMargins(10, 6, 10, 6)

        cmd_label = QLabel(command_text)
        cmd_label.setObjectName("cardCommand")
        cmd_label.setWordWrap(True)
        cmd_label.setTextFormat(Qt.PlainText)  # 显式渲染 \n 换行
        cmd_label.setToolTip(command_text)  # 长命令悬浮看全文
        code_block_layout.addWidget(cmd_label)

        self._stack.addWidget(code_block)  # index 0

        # 第 1 层：操作按钮面板（与代码块等高等宽，原地替换）
        btn_panel = QFrame()
        btn_panel.setObjectName("cardCodeBlock")  # 复用同一背景样式
        btn_panel_layout = QVBoxLayout(btn_panel)
        btn_panel_layout.setContentsMargins(10, 0, 10, 0)
        btn_panel_layout.setAlignment(Qt.AlignCenter)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.setAlignment(Qt.AlignCenter)

        edit_btn = QPushButton("编辑")
        edit_btn.setObjectName("cardActionBtn")
        edit_btn.setProperty("variant", "secondary")
        edit_btn.setFixedHeight(26)
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self._command_id))

        delete_btn = QPushButton("删除")
        delete_btn.setObjectName("cardActionBtn")
        delete_btn.setProperty("variant", "danger")
        delete_btn.setFixedHeight(26)
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self._command_id))

        btn_row.addWidget(edit_btn)
        btn_row.addWidget(delete_btn)
        btn_panel_layout.addLayout(btn_row)

        self._stack.addWidget(btn_panel)  # index 1
        content_layout.addWidget(self._stack)

        card_layout.addWidget(content, 1)

        self._stripe = stripe
        self._code_block = code_block
        self._edit_btn = edit_btn
        self._delete_btn = delete_btn

    def enterEvent(self, event) -> None:
        """鼠标进入时，命令代码块原地替换为操作按钮。"""
        self._stack.setCurrentIndex(1)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """鼠标离开时，恢复显示命令代码块。"""
        self._stack.setCurrentIndex(0)
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        """鼠标左键单击时发出运行请求。

        Args:
            event: Qt 鼠标按下事件。
        """
        if event.button() == Qt.LeftButton:
            self.run_requested.emit(self._command_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        """双击时不重复发出运行请求，避免命令执行两次。"""
        super().mouseDoubleClickEvent(event)


# ── 主题开关：点击切换 ────────────────────────────────────────────

class _ThemeSwitch(QSlider):
    """点击即切换浅色/深色的主题开关。"""

    def mousePressEvent(self, event) -> None:
        """鼠标左键点击时切换到另一种主题。

        Args:
            event: Qt 鼠标按下事件。

        Returns:
            无返回值。
        """
        if event.button() == Qt.LeftButton:
            # 作为二态开关使用，点击任意位置都在 0 和 1 之间切换。
            self.setValue(0 if self.value() == 1 else 1)
            event.accept()
            return
        super().mousePressEvent(event)


# ── 主窗口 ────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    """Main two-column project launcher window."""

    def __init__(
        self,
        store: ConfigStore | None = None,
        runner: CommandRunner | None = None,
        shared_mem: object | None = None,
    ) -> None:
        """加载配置并初始化主窗口控件。

        Args:
            store: 可选配置存储，主要用于测试。
            runner: 可选命令运行器，主要用于测试。
            shared_mem: 单实例检测的共享内存，用于接收恢复信号。
        """
        super().__init__()
        self.store = store or ConfigStore()
        self.runner = runner or CommandRunner()
        self._shared_mem = shared_mem
        self.config: AppConfig = self.store.load()

        self.setWindowTitle("命令启动器")
        icon_path = app_icon_path()
        if icon_path.exists():
            # 设置主窗口标题栏图标，Windows 左上角和任务栏会读取该图标。
            self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(980, 620)
        self.project_list = QListWidget()
        self.project_name = QLabel("未选择项目")
        self.project_path = QLabel("")
        # 项目路径使用等宽字体 — 签名元素
        path_font = self.project_path.font()
        path_font.setFamily("Consolas")
        path_font.setPointSize(10)
        self.project_path.setFont(path_font)
        self.cmd_button = QPushButton("打开命令提示符")
        self.powershell_button = QPushButton("打开 PowerShell")
        self.explorer_button = QPushButton("打开资源管理器")

        # 全局命令流式布局（添加按钮在 _refresh_command_list 中动态创建）
        self.global_commands_widget = QWidget()
        self.global_commands_flow = FlowLayout(self.global_commands_widget)
        self.global_commands_flow.setContentsMargins(0, 0, 0, 0)

        # 项目命令标题和卡片区域（卡片使用流式布局，自适应网格排列）
        self.project_commands_title = QLabel("项目命令")
        self.project_cards_widget = QWidget()
        self.project_cards_flow = FlowLayout(self.project_cards_widget)
        self.project_cards_flow.setContentsMargins(0, 0, 0, 0)
        self.project_cards_flow.setSpacing(12)
        self.project_cards_scroll = QScrollArea()
        self.add_project_command_button = QPushButton("添加项目命令")

        self.main_splitter = QSplitter()
        self.github_button = QPushButton("")
        self.settings_button = QPushButton("")
        self.theme_switch = _ThemeSwitch(Qt.Horizontal)

        self._build_layout()
        self._connect_signals()
        # 从配置恢复保存的主题，默认为浅色
        theme_value = 1 if self.config.theme == "dark" else 0
        self.theme_switch.blockSignals(True)
        self.theme_switch.setValue(theme_value)
        self.theme_switch.blockSignals(False)
        self._apply_theme(theme_value)
        self._refresh_projects()
        self._select_initial_project()
        self._setup_tray()

    # ── 布局构建 ──────────────────────────────────────────────────

    def _build_layout(self) -> None:
        """构建左右分栏的现代化主界面布局。"""
        root = QHBoxLayout()
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(0)

        self.main_splitter.setObjectName("mainSplitter")
        self.main_splitter.setChildrenCollapsible(False)
        # 分栏拖拽柄保持可用，同时减少左右面板之间的视觉空隙。
        self.main_splitter.setHandleWidth(8)

        sidebar = self._build_sidebar()
        content = self._build_content_panel()
        self.main_splitter.addWidget(sidebar)
        self.main_splitter.addWidget(content)
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 3)
        self.main_splitter.setSizes([230, 750])

        root.addWidget(self.main_splitter)

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)
        self.statusBar().setObjectName("statusBar")
        self.statusBar().hide()

    def _build_sidebar(self) -> QFrame:
        """构建左侧项目列表面板。

        Returns:
            已配置布局和样式标记的项目面板。
        """
        sidebar = QFrame()
        sidebar.setObjectName("sidebarPanel")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(14, 14, 14, 14)
        sidebar_layout.setSpacing(10)

        title = QLabel("项目")
        title.setObjectName("sectionTitle")
        self.project_list.setObjectName("projectList")
        self.project_list.setFrameShape(QFrame.NoFrame)

        self.add_project_button = QPushButton("添加")
        self.remove_project_button = QPushButton("移除")
        self.add_project_button.setProperty("variant", "secondary")
        self.remove_project_button.setProperty("variant", "danger")

        project_actions = QHBoxLayout()
        project_actions.setSpacing(8)
        project_actions.addWidget(self.add_project_button)
        project_actions.addWidget(self.remove_project_button)

        sidebar_layout.addWidget(title)
        sidebar_layout.addWidget(self.project_list, 1)
        sidebar_layout.addLayout(project_actions)
        return sidebar

    def _build_content_panel(self) -> QFrame:
        """构建右侧项目详情和命令面板。

        Returns:
            已配置布局和样式标记的内容面板。
        """
        content = QFrame()
        content.setObjectName("contentPanel")
        content_layout = QVBoxLayout(content)
        # 底部不再保留状态栏提示，内容区底部边距与左侧保持一致。
        content_layout.setContentsMargins(8, 18, 18, 8)
        content_layout.setSpacing(8)

        self.project_name.setObjectName("projectTitle")
        self.project_path.setObjectName("projectPath")
        self.project_path.setWordWrap(True)

        content_layout.addWidget(self.project_name)
        content_layout.addWidget(self.project_path)
        content_layout.addLayout(self._build_builtin_actions())
        content_layout.addWidget(self._build_command_area(), 1)
        content_layout.addLayout(self._build_corner_tools())
        return content

    def _build_builtin_actions(self) -> QHBoxLayout:
        """构建内置启动操作按钮组。

        CMD 为主操作，PowerShell 和资源管理器为次要操作。

        Returns:
            包含 CMD、PowerShell 和资源管理器按钮的横向布局。
        """
        self.cmd_button.setProperty("variant", "primary")
        self.powershell_button.setProperty("variant", "secondary-fill")
        self.explorer_button.setProperty("variant", "secondary")

        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addWidget(self.cmd_button)
        actions.addWidget(self.powershell_button)
        actions.addWidget(self.explorer_button)
        actions.addStretch(1)
        return actions

    def _build_command_area(self) -> QWidget:
        """构建命令区域：全局命令流式布局 + 项目命令卡片区域。

        全局命令以芯片形式排列在 3 个固定按钮下方，自适应换行，
        末尾为"添加全局命令"按钮。项目命令以卡片形式展示在下方滚动区域。

        Returns:
            包含全局命令芯片和项目命令卡片的控件。
        """
        area = QWidget()
        layout = QVBoxLayout(area)
        layout.setContentsMargins(0, 2, 0, 0)
        layout.setSpacing(12)

        # ── 全局命令流式布局 ──
        self.global_commands_widget.setObjectName("globalCommandsWidget")
        layout.addWidget(self.global_commands_widget)

        # ── 项目命令区域标题 ──
        self.project_commands_title.setObjectName("sectionTitle")
        layout.addWidget(self.project_commands_title)

        # ── 项目命令卡片滚动区域 ──
        self.project_cards_scroll.setObjectName("projectCardsScroll")
        self.project_cards_scroll.setFrameShape(QFrame.NoFrame)
        self.project_cards_scroll.setWidgetResizable(True)
        self.project_cards_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.project_cards_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.project_cards_widget.setObjectName("projectCardsContainer")
        self.project_cards_scroll.setWidget(self.project_cards_widget)
        layout.addWidget(self.project_cards_scroll, 1)

        # ── 添加项目命令按钮 ──
        self.add_project_command_button.setProperty("variant", "secondary")
        self.add_project_command_button.clicked.connect(
            lambda: self._add_command(global_command=False)
        )
        layout.addWidget(self.add_project_command_button)

        return area

    def _build_corner_tools(self) -> QHBoxLayout:
        """构建右下角工具区：主题开关 → 设置 → GitHub。"""
        tools = QHBoxLayout()
        tools.setObjectName("cornerTools")
        tools.setSpacing(8)
        tools.addStretch(1)

        # 主题开关 — 左侧为浅色，右侧为深色
        self.theme_switch.setObjectName("themeSwitch")
        self.theme_switch.setRange(0, 1)
        self.theme_switch.setSingleStep(1)
        self.theme_switch.setPageStep(1)
        self.theme_switch.setFixedWidth(46)
        self.theme_switch.setToolTip("切换浅色 / 深色模式")
        self.theme_switch.valueChanged.connect(self._apply_theme)

        # 设置齿轮按钮
        self.settings_button.setObjectName("settingsButton")
        self.settings_button.setFixedSize(30, 30)
        self.settings_button.setIconSize(self.settings_button.size() * 0.58)
        self.settings_button.setToolTip("设置")
        self.settings_button.clicked.connect(self._open_settings)

        # GitHub 按钮
        self.github_button.setObjectName("githubButton")
        self.github_button.setFixedSize(34, 30)
        self.github_button.setIconSize(self.github_button.size() * 0.62)
        self.github_button.setToolTip("打开 GitHub 仓库")
        self.github_button.clicked.connect(self._open_github_repository)

        tools.addWidget(self.theme_switch)
        tools.addWidget(self.settings_button)
        tools.addWidget(self.github_button)
        return tools

    # ── 信号连接 ──────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        """Connect UI events to application actions."""
        self.add_project_button.clicked.connect(self._add_project)
        self.remove_project_button.clicked.connect(self._remove_project)
        self.project_list.currentItemChanged.connect(self._project_changed)
        self.cmd_button.clicked.connect(lambda: self._run_builtin("cmd"))
        self.powershell_button.clicked.connect(lambda: self._run_builtin("powershell"))
        self.explorer_button.clicked.connect(lambda: self._run_builtin("explorer"))

    def closeEvent(self, event) -> None:
        """处理窗口关闭事件 — 根据配置分流：最小化、退出或询问。

        Args:
            event: Qt 关闭事件。
        """
        if self.config.close_action == "minimize":
            event.ignore()
            self.hide()
            return

        if self.config.close_action == "quit":
            self._do_quit()
            return

        # close_action == "ask" — 弹出确认对话框
        dialog = CloseConfirmDialog(parent=self)
        dialog.exec()

        if dialog.should_minimize():
            event.ignore()
            self.hide()
        else:
            self._do_quit()

        if dialog.remember_choice():
            self.config.close_action = (
                "minimize" if dialog.should_minimize() else "quit"
            )
            self.store.save(self.config)

    def _do_quit(self) -> None:
        """彻底退出应用：隐藏托盘图标并退出事件循环。"""
        self.tray_icon.hide()
        QApplication.instance().quit()

    # ── 系统托盘 ──────────────────────────────────────────────────

    def _setup_tray(self) -> None:
        """创建系统托盘图标。左键弹出命令菜单，右键弹出操作菜单。"""
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = app_icon_path()
        if icon_path.exists():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        else:
            self.tray_icon.setIcon(QApplication.style().standardIcon(
                QApplication.style().SP_ComputerIcon
            ))
        self.tray_icon.setToolTip("命令启动器")

        # 左键点击弹出命令菜单
        self.tray_icon.activated.connect(self._on_tray_activated)

        # 首次构建菜单
        self._rebuild_tray_menu()
        self.tray_icon.show()

        # 定时检查来自第二个实例的「恢复窗口」信号
        self._restore_timer = QTimer(self)
        self._restore_timer.timeout.connect(self._check_restore_signal)
        self._restore_timer.start(300)  # 每 300ms 检查一次

    def _check_restore_signal(self) -> None:
        """检查共享内存中的恢复信号，由第二个实例写入。"""
        if self._shared_mem is None:
            return
        if self._shared_mem.lock():
            try:
                if self._shared_mem.data()[0] == 1:
                    self._shared_mem.data()[0] = 0
                    self._shared_mem.unlock()
                    self._show_from_tray()
                    return
            except Exception:
                pass
            self._shared_mem.unlock()

    def _rebuild_tray_menu(self) -> None:
        """根据当前配置重建托盘菜单（项目 → 命令 层级结构）。"""
        menu = QMenu()

        # — 项目层级 —
        for project in self.config.projects:
            project_menu = menu.addMenu(project.name)

            # 全局命令（每个项目都显示）
            for cmd in self.config.global_commands:
                action = project_menu.addAction(f"📋 {cmd.name}")
                action.triggered.connect(
                    lambda checked=False, p=project, c=cmd: self._run_from_tray(p, c)
                )

            # 项目命令
            if self.config.global_commands and project.commands:
                project_menu.addSeparator()
            for cmd in project.commands:
                action = project_menu.addAction(cmd.name)
                action.triggered.connect(
                    lambda checked=False, p=project, c=cmd: self._run_from_tray(p, c)
                )

            # 如果项目下没有命令，显示提示
            if not self.config.global_commands and not project.commands:
                empty = project_menu.addAction("（无命令）")
                empty.setEnabled(False)

        # 如果没有项目，显示提示
        if not self.config.projects:
            empty = menu.addAction("（无项目，请先添加项目目录）")
            empty.setEnabled(False)

        menu.addSeparator()

        # — 操作项 —
        show_action = menu.addAction("显示主窗口")
        show_action.triggered.connect(self._show_from_tray)
        quit_action = menu.addAction("退出")
        quit_action.triggered.connect(self._quit_from_tray)

        # 保存引用防止被垃圾回收（不设 setContextMenu，改为手动处理右键）
        self._tray_menu = menu

    def _on_tray_activated(self, reason: int) -> None:
        """托盘图标点击处理：左键打开主窗口，右键在图标上方弹出命令菜单。"""
        if reason == QSystemTrayIcon.DoubleClick:
            self._show_from_tray()
        elif reason == QSystemTrayIcon.Trigger:
            # 左键单击 — 打开主窗口
            self._show_from_tray()
        elif reason == QSystemTrayIcon.Context:
            # 右键单击 — 在托盘图标上方弹出菜单
            self._rebuild_tray_menu()  # 确保菜单是最新的
            geo = self.tray_icon.geometry()
            menu_pos = geo.topLeft()
            # 将菜单位置偏移到图标左上方
            menu_pos.setX(menu_pos.x() - self._tray_menu.sizeHint().width())
            menu_pos.setY(menu_pos.y() - self._tray_menu.sizeHint().height())
            self._tray_menu.popup(menu_pos)

    def _show_from_tray(self) -> None:
        """从托盘恢复主窗口。"""
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _quit_from_tray(self) -> None:
        """从托盘菜单彻底退出应用。"""
        self.tray_icon.hide()
        self.config.close_action = "quit"
        self.close()

    def _run_from_tray(self, project, command) -> None:
        """从托盘菜单执行命令。"""
        try:
            self.runner.run_custom(command.command, project.path)
        except Exception as exc:
            QMessageBox.critical(self, "启动失败", f"{command.command}\n\n{exc}")

    def _open_github_repository(self) -> None:
        """打开项目 GitHub 仓库。

        Returns:
            无返回值。
        """
        QDesktopServices.openUrl(
            QUrl("https://github.com/Latbby/CommandLauncher.git")
        )

    def _apply_theme(self, value: int) -> None:
        """根据主题开关值应用浅色或深色样式。

        Args:
            value: 0 表示浅色，1 表示深色。

        Returns:
            无返回值。
        """
        app = QApplication.instance()
        if not app:
            return
        # 右侧位置代表深色模式，其他值回落到浅色模式。
        app.setStyleSheet(DARK_STYLESHEET if value == 1 else LIGHT_STYLESHEET)
        self.github_button.setIcon(_github_mark_icon(dark_mode=value == 1))
        self.settings_button.setIcon(_gear_icon(dark_mode=value == 1))

        # 持久化主题偏好
        new_theme = "dark" if value == 1 else "light"
        if self.config.theme != new_theme:
            self.config.theme = new_theme
            self.store.save(self.config)

    # ── 设置 ──────────────────────────────────────────────────────

    def _open_settings(self) -> None:
        """打开设置对话框，保存用户选择的开机自启和退出行为。"""
        from command_launcher.ui.dialogs import SettingsDialog

        dialog = SettingsDialog(
            auto_start=self.config.auto_start,
            close_action=self.config.close_action,
            parent=self,
        )
        if dialog.exec() != SettingsDialog.Accepted:
            return

        self.config.auto_start = dialog.auto_start()
        self.config.close_action = dialog.close_action()
        self.store.save(self.config)

        # 应用开机自启设置
        self._apply_auto_start(self.config.auto_start)

    @staticmethod
    def _apply_auto_start(enable: bool) -> None:
        """通过 Windows 注册表 Run 键设置或移除开机自启。

        Args:
            enable: True 时添加开机启动项，False 时移除。
        """
        if sys.platform != "win32":
            return

        import winreg

        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "CommandLauncher"

        try:
            if enable:
                # 写入注册表：指向当前可执行文件，附加 --tray 以静默启动到系统托盘
                exe_path = sys.executable
                if getattr(sys, "frozen", False):
                    command = f'"{exe_path}" --tray'
                else:
                    script = str(Path(sys.argv[0]).resolve())
                    command = f'"{exe_path}" "{script}" --tray'

                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
                ) as key:
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)
            else:
                # 移除注册表项
                try:
                    with winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
                    ) as key:
                        winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass  # 本来就没有，忽略
        except OSError:
            pass  # 权限不足等，静默失败

    # ── 项目列表 ──────────────────────────────────────────────────

    def _refresh_projects(self) -> None:
        """Render the saved project list."""
        self.project_list.clear()
        for project in self.config.projects:
            item = QListWidgetItem(project.name)
            item.setData(Qt.UserRole, project.id)
            self.project_list.addItem(item)

    def _select_initial_project(self) -> None:
        """Select the last used project or the first available project."""
        selected = self.config.selected_project()
        if not selected:
            self._render_project(None)
            return

        for index in range(self.project_list.count()):
            item = self.project_list.item(index)
            if item.data(Qt.UserRole) == selected.id:
                self.project_list.setCurrentItem(item)
                return

    def _selected_project(self) -> Project | None:
        """Return the project selected in the project list.

        Returns:
            Currently selected project or None.
        """
        item = self.project_list.currentItem()
        if not item:
            return None
        project_id = item.data(Qt.UserRole)
        return next((p for p in self.config.projects if p.id == project_id), None)

    def _project_changed(self) -> None:
        """Persist and render the newly selected project."""
        project = self._selected_project()
        self.config.last_selected_project_id = project.id if project else None
        self.store.save(self.config)
        self._render_project(project)

    def _render_project(self, project: Project | None) -> None:
        """渲染项目详情和命令区域。

        Args:
            project: 需要渲染的项目，未选择时为 None。
        """
        enabled = bool(project and Path(project.path).exists())
        self.project_name.setText(project.name if project else "未选择项目")
        path_text = f"▸ {project.path}" if project else ""
        self.project_path.setText(path_text)
        for button in (self.cmd_button, self.powershell_button, self.explorer_button):
            button.setEnabled(enabled)
        self.statusBar().clearMessage()
        self.statusBar().hide()

        # 无项目时隐藏项目命令区域
        has_project = project is not None
        self.project_commands_title.setVisible(has_project)
        self.project_cards_scroll.setVisible(has_project)
        self.add_project_command_button.setVisible(has_project)

        self._refresh_command_list()

    # ── 命令列表刷新 ──────────────────────────────────────────────

    def _refresh_command_list(self) -> None:
        """刷新全局命令芯片和项目命令卡片。"""
        self._clear_flow_layout(self.global_commands_flow)
        self._clear_flow_layout(self.project_cards_flow)

        # 全局命令芯片
        for command in self.config.global_commands:
            self._add_global_command_chip(command)

        # 添加全局命令按钮（始终在末尾，每次重建）
        add_chip = _AddGlobalCommandChip()
        add_chip.add_requested.connect(
            lambda: self._add_command(global_command=True)
        )
        self.global_commands_flow.addWidget(add_chip)

        # 项目命令卡片
        project = self._selected_project()
        if project:
            for command in project.commands:
                self._add_project_command_card(command)

    def _clear_flow_layout(self, flow: FlowLayout) -> None:
        """清空流式布局中的所有控件。

        Args:
            flow: 目标流式布局。
        """
        while flow.count():
            item = flow.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def _add_global_command_chip(self, command: LaunchCommand) -> None:
        """向全局命令流式布局添加一个命令芯片。

        Args:
            command: 命令数据模型。
        """
        chip = _GlobalCommandChip(command.id, command.name)
        chip.run_requested.connect(
            lambda cid: self._run_command_by_id(cid, is_global=True)
        )
        chip.edit_requested.connect(
            lambda cid: self._edit_command_by_id(cid, is_global=True)
        )
        chip.delete_requested.connect(
            lambda cid: self._delete_command_by_id(cid, is_global=True)
        )
        self.global_commands_flow.addWidget(chip)

    def _add_project_command_card(self, command: LaunchCommand) -> None:
        """向项目命令卡片流式布局添加一个命令卡片。

        Args:
            command: 命令数据模型。
        """
        card = _ProjectCommandCard(command.id, command.name, command.command)
        card.run_requested.connect(
            lambda cid: self._run_command_by_id(cid, is_global=False)
        )
        card.edit_requested.connect(
            lambda cid: self._edit_command_by_id(cid, is_global=False)
        )
        card.delete_requested.connect(
            lambda cid: self._delete_command_by_id(cid, is_global=False)
        )
        self.project_cards_flow.addWidget(card)

    # ── 项目增删 ──────────────────────────────────────────────────

    def _add_project(self) -> None:
        """Prompt for a directory and save it as a project."""
        directory = QFileDialog.getExistingDirectory(self, "选择项目目录")
        if not directory:
            return
        project = self.config.add_project(directory)
        self.store.save(self.config)
        self._rebuild_tray_menu()
        self._refresh_projects()

        for index in range(self.project_list.count()):
            item = self.project_list.item(index)
            if item.data(Qt.UserRole) == project.id:
                self.project_list.setCurrentItem(item)
                break

    def _remove_project(self) -> None:
        """Remove the selected project from local configuration only."""
        project = self._selected_project()
        if not project:
            return
        self.config.projects = [p for p in self.config.projects if p.id != project.id]
        self.config.last_selected_project_id = None
        self.store.save(self.config)
        self._rebuild_tray_menu()
        self._refresh_projects()
        self._select_initial_project()

    # ── 命令增删改 ────────────────────────────────────────────────

    def _add_command(self, global_command: bool) -> None:
        """创建全局或项目命令。

        Args:
            global_command: True 时添加为全局命令。
        """
        project = self._selected_project()
        if not global_command and not project:
            return

        dialog = CommandDialog(parent=self)
        if dialog.exec() != CommandDialog.Accepted:
            return

        name, command_text = dialog.command_values()
        if not LaunchCommand.is_valid(name, command_text):
            QMessageBox.warning(self, "命令无效", "名称和命令不能为空。")
            return

        command = LaunchCommand(name=name, command=command_text)
        if global_command:
            self.config.global_commands.append(command)
        elif project:
            project.commands.append(command)
        self.store.save(self.config)
        self._rebuild_tray_menu()
        self._refresh_command_list()

    def _edit_command_by_id(self, command_id: str, is_global: bool) -> None:
        """根据命令 ID 编辑命令。

        Args:
            command_id: 要编辑的命令 ID。
            is_global: 是否为全局命令。
        """
        project = self._selected_project()
        commands = (
            self.config.global_commands if is_global
            else (project.commands if project else [])
        )
        command = next((c for c in commands if c.id == command_id), None)
        if not command:
            return

        dialog = CommandDialog(command=command, parent=self)
        if dialog.exec() != CommandDialog.Accepted:
            return

        name, command_text = dialog.command_values()
        if not LaunchCommand.is_valid(name, command_text):
            QMessageBox.warning(self, "命令无效", "名称和命令不能为空。")
            return

        command.name = name
        command.command = command_text
        self.store.save(self.config)
        self._rebuild_tray_menu()
        self._refresh_command_list()

    def _delete_command_by_id(self, command_id: str, is_global: bool) -> None:
        """根据命令 ID 删除命令。

        Args:
            command_id: 要删除的命令 ID。
            is_global: 是否为全局命令。
        """
        project = self._selected_project()
        if is_global:
            self.config.global_commands = [
                c for c in self.config.global_commands if c.id != command_id
            ]
        elif project:
            project.commands = [
                c for c in project.commands if c.id != command_id
            ]
        self.store.save(self.config)
        self._rebuild_tray_menu()
        self._refresh_command_list()

    # ── 命令执行 ──────────────────────────────────────────────────

    def _run_builtin(self, command_type: str) -> None:
        """运行内置命令：CMD/PowerShell 弹窗，资源管理器打开目录。

        Args:
            command_type: 命令类型，\"cmd\"、\"powershell\" 或 \"explorer\"。
        """
        project = self._selected_project()
        if not project:
            return

        try:
            if command_type == "cmd":
                self.runner.run_cmd(project.path)
            elif command_type == "powershell":
                self.runner.run_powershell(project.path)
            else:
                self.runner.run_explorer(project.path)
        except Exception as exc:
            QMessageBox.critical(self, "启动失败", str(exc))

    def _run_command_by_id(self, command_id: str, is_global: bool) -> None:
        """根据命令 ID 执行自定义命令。

        Args:
            command_id: 要执行的命令 ID。
            is_global: 是否为全局命令。
        """
        project = self._selected_project()
        if not project:
            return

        commands = (
            self.config.global_commands if is_global
            else project.commands
        )
        command = next((c for c in commands if c.id == command_id), None)
        if not command:
            return

        try:
            self.runner.run_custom(command.command, project.path)
        except Exception as exc:
            QMessageBox.critical(self, "启动失败", f"{command.command}\n\n{exc}")
