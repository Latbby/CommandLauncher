"""Main Project Launcher window."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from command_launcher.command_runner import CommandRunner
from command_launcher.config_store import ConfigStore
from command_launcher.models import AppConfig, LaunchCommand, Project
from command_launcher.ui.dialogs import CommandDialog


# ── 命令列表项控件：名称 + 悬浮编辑/删除 ──────────────────────────

class _CommandItemWidget(QWidget):
    """命令列表项控件，鼠标悬浮时显示编辑和删除按钮。

    信号:
        edit_requested(str): 用户点击编辑按钮，携带命令 ID。
        delete_requested(str): 用户点击删除按钮，携带命令 ID。
        run_requested(str): 用户双击项目名称区域，携带命令 ID。
    """

    edit_requested = Signal(str)
    delete_requested = Signal(str)
    run_requested = Signal(str)

    def __init__(
        self,
        command_id: str,
        command_name: str,
        is_global: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        """初始化命令列表项。

        Args:
            command_id: 命令唯一标识。
            command_name: 命令显示名称。
            is_global: 是否为全局命令。
            parent: 可选的 Qt 父控件。
        """
        super().__init__(parent)
        self._command_id = command_id
        self._is_global = is_global
        self.setMouseTracking(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 8, 4)
        layout.setSpacing(8)

        # 命令名称 — 终端风格 "> xxx"，全局命令文字颜色偏淡
        self._name_label = QLabel(f"> {command_name}")
        self._name_label.setObjectName("commandName")
        if is_global:
            # 全局命令用弱化的文字颜色区分
            self._name_label.setStyleSheet("color: #8b8896;")
        layout.addWidget(self._name_label, 1)

        # 编辑按钮 — 默认隐藏，悬浮时显示
        self._edit_btn = QPushButton("编辑")
        self._edit_btn.setObjectName("itemActionBtn")
        self._edit_btn.setProperty("variant", "secondary")
        self._edit_btn.setFixedHeight(24)
        self._edit_btn.hide()
        self._edit_btn.clicked.connect(lambda: self.edit_requested.emit(self._command_id))

        # 删除按钮 — 默认隐藏，悬浮时显示
        self._delete_btn = QPushButton("删除")
        self._delete_btn.setObjectName("itemActionBtn")
        self._delete_btn.setProperty("variant", "danger")
        self._delete_btn.setFixedHeight(24)
        self._delete_btn.hide()
        self._delete_btn.clicked.connect(lambda: self.delete_requested.emit(self._command_id))

        layout.addWidget(self._edit_btn)
        layout.addWidget(self._delete_btn)

    # ── 鼠标悬浮控制 ──────────────────────────────────────────────

    def enterEvent(self, event) -> None:
        """鼠标进入时只显示操作按钮，不修改列表项背景。"""
        self._edit_btn.show()
        self._delete_btn.show()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """鼠标离开时隐藏操作按钮，不修改列表项背景。"""
        self._edit_btn.hide()
        self._delete_btn.hide()
        super().leaveEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        """双击时发出运行请求。"""
        self.run_requested.emit(self._command_id)
        super().mouseDoubleClickEvent(event)


# ── 主窗口 ────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    """Main two-column project launcher window."""

    def __init__(
        self,
        store: ConfigStore | None = None,
        runner: CommandRunner | None = None,
    ) -> None:
        """加载配置并初始化主窗口控件。

        Args:
            store: 可选配置存储，主要用于测试。
            runner: 可选命令运行器，主要用于测试。
        """
        super().__init__()
        self.store = store or ConfigStore()
        self.runner = runner or CommandRunner()
        self.config: AppConfig = self.store.load()

        self.setWindowTitle("命令启动器")
        # 设置窗口图标 (src/command_launcher/ui/main_window.py → 项目根/assets/icon.ico)
        icon_path = Path(__file__).parent.parent.parent.parent / "assets" / "icon.ico"
        if icon_path.exists():
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
        self.global_command_list = QListWidget()
        self.project_command_list = QListWidget()
        self.command_tabs = QTabWidget()
        self.main_splitter = QSplitter()

        self._build_layout()
        self._connect_signals()
        self._refresh_projects()
        self._select_initial_project()

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
        """构建命令区域：顶部标题栏 + 全局/项目命令页签。

        添加按钮根据当前页签决定添加全局命令或项目命令。

        Returns:
            包含标题栏、添加按钮和命令页签的控件。
        """
        area = QWidget()
        layout = QVBoxLayout(area)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)

        # ── 顶部栏：标题 + 添加按钮 ──
        top_bar = QHBoxLayout()
        top_bar.setSpacing(0)

        title = QLabel("命令")
        title.setObjectName("sectionTitle")
        top_bar.addWidget(title)
        top_bar.addStretch(1)

        # 添加按钮根据当前页签添加全局命令或项目命令。
        self.add_command_button = QPushButton("添加")
        self.add_command_button.setProperty("variant", "secondary")
        self.add_command_button.clicked.connect(self._add_command_for_current_tab)

        top_bar.addWidget(self.add_command_button)
        layout.addLayout(top_bar)

        # ── 命令页签：列表贴近面板边框，只保留列表自身少量内边距 ──
        self.command_tabs.setObjectName("commandTabs")
        for command_list in (self.global_command_list, self.project_command_list):
            command_list.setObjectName("commandList")
            command_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            command_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.command_tabs.addTab(self.global_command_list, "全局命令")
        self.command_tabs.addTab(self.project_command_list, "项目命令")
        layout.addWidget(self.command_tabs, 1)

        return area

    # ── 信号连接 ──────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        """Connect UI events to application actions."""
        self.add_project_button.clicked.connect(self._add_project)
        self.remove_project_button.clicked.connect(self._remove_project)
        self.project_list.currentItemChanged.connect(self._project_changed)
        self.cmd_button.clicked.connect(lambda: self._run_builtin("cmd"))
        self.powershell_button.clicked.connect(lambda: self._run_builtin("powershell"))
        self.explorer_button.clicked.connect(lambda: self._run_builtin("explorer"))

    # ── 项目列表 ──────────────────────────────────────────────────

    def _refresh_projects(self) -> None:
        """Render the saved project list."""
        self.project_list.clear()
        for project in self.config.projects:
            item = QListWidgetItem(project.name)
            item.setData(1, project.id)
            self.project_list.addItem(item)

    def _select_initial_project(self) -> None:
        """Select the last used project or the first available project."""
        selected = self.config.selected_project()
        if not selected:
            self._render_project(None)
            return

        for index in range(self.project_list.count()):
            item = self.project_list.item(index)
            if item.data(1) == selected.id:
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
        project_id = item.data(1)
        return next((p for p in self.config.projects if p.id == project_id), None)

    def _project_changed(self) -> None:
        """Persist and render the newly selected project."""
        project = self._selected_project()
        self.config.last_selected_project_id = project.id if project else None
        self.store.save(self.config)
        self._render_project(project)

    def _render_project(self, project: Project | None) -> None:
        """渲染项目详情和统一命令列表。

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

        self._refresh_command_list()

    def _refresh_command_list(self) -> None:
        """刷新全局命令列表和项目命令列表。"""
        self.global_command_list.clear()
        self.project_command_list.clear()

        # 全局命令固定展示在全局命令页签。
        for command in self.config.global_commands:
            self._add_command_item(self.global_command_list, command, is_global=True)

        # 项目命令只展示当前选中项目的命令。
        project = self._selected_project()
        if project:
            for command in project.commands:
                self._add_command_item(self.project_command_list, command, is_global=False)

    def _add_command_item(
        self, command_list: QListWidget, command: LaunchCommand, is_global: bool
    ) -> None:
        """向指定命令列表追加一个命令项。

        Args:
            command_list: 目标命令列表控件。
            command: 命令数据模型。
            is_global: 是否为全局命令。
        """
        item_widget = _CommandItemWidget(command.id, command.name, is_global)
        # 确保项不会被压缩，最小高度 36px
        item_widget.setMinimumHeight(36)

        # 连接编辑/删除/运行信号
        item_widget.edit_requested.connect(
            lambda cid: self._edit_command_by_id(cid, is_global)
        )
        item_widget.delete_requested.connect(
            lambda cid: self._delete_command_by_id(cid, is_global)
        )
        item_widget.run_requested.connect(
            lambda cid: self._run_command_by_id(cid, is_global)
        )

        list_item = QListWidgetItem()
        list_item.setSizeHint(item_widget.sizeHint())
        list_item.setData(1, command.id)
        command_list.addItem(list_item)
        command_list.setItemWidget(list_item, item_widget)

    # ── 项目增删 ──────────────────────────────────────────────────

    def _add_project(self) -> None:
        """Prompt for a directory and save it as a project."""
        directory = QFileDialog.getExistingDirectory(self, "选择项目目录")
        if not directory:
            return
        project = self.config.add_project(directory)
        self.store.save(self.config)
        self._refresh_projects()

        for index in range(self.project_list.count()):
            item = self.project_list.item(index)
            if item.data(1) == project.id:
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
        self._refresh_projects()
        self._select_initial_project()

    # ── 命令增删改 ────────────────────────────────────────────────

    def _add_command_for_current_tab(self) -> None:
        """根据当前命令页签创建全局命令或项目命令。"""
        self._add_command(self.command_tabs.currentIndex() == 0)

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
