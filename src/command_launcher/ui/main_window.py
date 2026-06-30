"""Main Project Launcher window."""

from __future__ import annotations

from pathlib import Path

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
        self.resize(980, 620)
        self.project_list = QListWidget()
        self.project_name = QLabel("未选择项目")
        self.project_path = QLabel("")
        # 项目路径使用等宽字体 — 签名元素，模拟终端路径提示符
        path_font = self.project_path.font()
        path_font.setFamily("Consolas")
        path_font.setPointSize(10)
        self.project_path.setFont(path_font)
        self.cmd_button = QPushButton("打开命令提示符")
        self.powershell_button = QPushButton("打开 PowerShell")
        self.explorer_button = QPushButton("打开资源管理器")
        self.global_commands = QListWidget()
        self.project_commands = QListWidget()
        self.main_splitter = QSplitter()
        self.command_tabs = QTabWidget()

        self._build_layout()
        self._connect_signals()
        self._refresh_projects()
        self._select_initial_project()

    def _build_layout(self) -> None:
        """构建左右分栏的现代化主界面布局。"""
        root = QHBoxLayout()
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(0)

        self.main_splitter.setObjectName("mainSplitter")
        self.main_splitter.setChildrenCollapsible(False)

        sidebar = self._build_sidebar()
        content = self._build_content_panel()
        self.main_splitter.addWidget(sidebar)
        self.main_splitter.addWidget(content)
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 3)
        self.main_splitter.setSizes([260, 720])

        root.addWidget(self.main_splitter)

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)
        self.statusBar().setObjectName("statusBar")

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
        content_layout.setContentsMargins(18, 18, 18, 18)
        content_layout.setSpacing(14)

        self.project_name.setObjectName("projectTitle")
        self.project_path.setObjectName("projectPath")
        self.project_path.setWordWrap(True)

        content_layout.addWidget(self.project_name)
        content_layout.addWidget(self.project_path)
        content_layout.addLayout(self._build_builtin_actions())
        content_layout.addWidget(self._build_command_tabs(), 1)
        return content

    def _build_builtin_actions(self) -> QHBoxLayout:
        """构建内置启动操作按钮组。

        Returns:
            包含 CMD、PowerShell 和资源管理器按钮的横向布局。
        """
        for button in (self.cmd_button, self.powershell_button, self.explorer_button):
            button.setProperty("variant", "primary")

        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addWidget(self.cmd_button)
        actions.addWidget(self.powershell_button)
        actions.addWidget(self.explorer_button)
        actions.addStretch(1)
        return actions

    def _build_command_tabs(self) -> QTabWidget:
        """构建全局命令和项目命令 Tab。

        Returns:
            包含两个命令列表页面的 Tab 控件。
        """
        self.command_tabs.setObjectName("commandTabs")
        self.add_global_button = QPushButton("添加")
        self.edit_global_button = QPushButton("编辑")
        self.delete_global_button = QPushButton("删除")
        self.add_project_command_button = QPushButton("添加")
        self.edit_project_command_button = QPushButton("编辑")
        self.delete_project_command_button = QPushButton("删除")

        global_tab = self._build_command_tab(
            self.global_commands,
            self.add_global_button,
            self.edit_global_button,
            self.delete_global_button,
        )
        project_tab = self._build_command_tab(
            self.project_commands,
            self.add_project_command_button,
            self.edit_project_command_button,
            self.delete_project_command_button,
        )
        self.command_tabs.addTab(global_tab, "全局命令")
        self.command_tabs.addTab(project_tab, "项目命令")
        return self.command_tabs

    def _build_command_tab(
        self,
        command_list: QListWidget,
        add_button: QPushButton,
        edit_button: QPushButton,
        delete_button: QPushButton,
    ) -> QWidget:
        """构建单个命令 Tab 页面。

        Args:
            command_list: 用于展示命令的列表控件。
            add_button: 添加命令按钮。
            edit_button: 编辑命令按钮。
            delete_button: 删除命令按钮。

        Returns:
            包含命令列表和按钮组的 Tab 页面。
        """
        command_list.setObjectName("commandList")
        add_button.setProperty("variant", "secondary")
        edit_button.setProperty("variant", "secondary")
        delete_button.setProperty("variant", "danger")

        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.addWidget(add_button)
        actions.addWidget(edit_button)
        actions.addWidget(delete_button)
        actions.addStretch(1)

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(command_list, 1)
        layout.addLayout(actions)
        return tab

    def _connect_signals(self) -> None:
        """Connect UI events to application actions."""
        self.add_project_button.clicked.connect(self._add_project)
        self.remove_project_button.clicked.connect(self._remove_project)
        self.project_list.currentItemChanged.connect(self._project_changed)
        self.cmd_button.clicked.connect(lambda: self._run_builtin("cmd"))
        self.powershell_button.clicked.connect(lambda: self._run_builtin("powershell"))
        self.explorer_button.clicked.connect(lambda: self._run_builtin("explorer"))
        self.add_global_button.clicked.connect(lambda: self._add_command(global_command=True))
        self.add_project_command_button.clicked.connect(
            lambda: self._add_command(global_command=False)
        )
        self.edit_global_button.clicked.connect(
            lambda: self._edit_command(global_command=True)
        )
        self.edit_project_command_button.clicked.connect(
            lambda: self._edit_command(global_command=False)
        )
        self.delete_global_button.clicked.connect(
            lambda: self._delete_command(global_command=True)
        )
        self.delete_project_command_button.clicked.connect(
            lambda: self._delete_command(global_command=False)
        )
        self.global_commands.itemDoubleClicked.connect(
            lambda item: self._run_command_item(item, True)
        )
        self.project_commands.itemDoubleClicked.connect(
            lambda item: self._run_command_item(item, False)
        )

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
        return next((project for project in self.config.projects if project.id == project_id), None)

    def _project_changed(self) -> None:
        """Persist and render the newly selected project."""
        project = self._selected_project()
        self.config.last_selected_project_id = project.id if project else None
        self.store.save(self.config)
        self._render_project(project)

    def _render_project(self, project: Project | None) -> None:
        """渲染项目详情和命令列表。

        Args:
            project: 需要渲染的项目，未选择时为 None。
        """
        enabled = bool(project and Path(project.path).exists())
        self.project_name.setText(project.name if project else "未选择项目")
        # 终端路径提示符样式 — 签名元素
        path_text = f"▸ {project.path}" if project else ""
        self.project_path.setText(path_text)
        for button in (self.cmd_button, self.powershell_button, self.explorer_button):
            button.setEnabled(enabled)
        if not project:
            self.statusBar().showMessage("请选择或添加一个项目。")
        elif enabled:
            self.statusBar().showMessage("已选择项目。")
        else:
            self.statusBar().showMessage("项目路径不存在，启动操作已禁用。")

        self.global_commands.clear()
        for command in self.config.global_commands:
            item = QListWidgetItem(command.name)
            item.setData(1, command.id)
            self.global_commands.addItem(item)

        self.project_commands.clear()
        if project:
            for command in project.commands:
                item = QListWidgetItem(command.name)
                item.setData(1, command.id)
                self.project_commands.addItem(item)

    def _add_project(self) -> None:
        """Prompt for a directory and save it as a project."""
        directory = QFileDialog.getExistingDirectory(self, "选择项目目录")
        if not directory:
            return
        project = self.config.add_project(directory)
        self.store.save(self.config)
        self._refresh_projects()

        # Re-select the new or existing project after refreshing the list.
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
        self.config.projects = [item for item in self.config.projects if item.id != project.id]
        self.config.last_selected_project_id = None
        self.store.save(self.config)
        self._refresh_projects()
        self._select_initial_project()

    def _add_command(self, global_command: bool) -> None:
        """Create a global or project-specific custom command.

        Args:
            global_command: True when adding to global commands.
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
        self._render_project(project)

    def _edit_command(self, global_command: bool) -> None:
        """Edit the selected custom command.

        Args:
            global_command: True when editing a global command.
        """
        project = self._selected_project()
        command_list = self.global_commands if global_command else self.project_commands
        item = command_list.currentItem()
        if not item or (not global_command and not project):
            return

        commands = self.config.global_commands if global_command else project.commands
        command_id = item.data(1)
        command = next((entry for entry in commands if entry.id == command_id), None)
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
        self._render_project(project)

    def _delete_command(self, global_command: bool) -> None:
        """Delete the selected custom command.

        Args:
            global_command: True when deleting from global commands.
        """
        project = self._selected_project()
        command_list = self.global_commands if global_command else self.project_commands
        item = command_list.currentItem()
        if not item:
            return

        command_id = item.data(1)
        if global_command:
            self.config.global_commands = [
                command for command in self.config.global_commands if command.id != command_id
            ]
        elif project:
            project.commands = [command for command in project.commands if command.id != command_id]
        self.store.save(self.config)
        self._render_project(project)

    def _run_builtin(self, command_type: str) -> None:
        """Run one built-in command for the selected project.

        Args:
            command_type: One of `cmd`, `powershell`, or `explorer`.
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

    def _run_command_item(self, item: QListWidgetItem, global_command: bool) -> None:
        """Run a selected custom command from the current project directory.

        Args:
            item: Clicked list item containing the command id.
            global_command: True when the item belongs to global commands.
        """
        project = self._selected_project()
        if not project:
            return

        commands = self.config.global_commands if global_command else project.commands
        command_id = item.data(1)
        command = next((entry for entry in commands if entry.id == command_id), None)
        if not command:
            return

        try:
            self.runner.run_custom(command.command, project.path)
        except Exception as exc:
            QMessageBox.critical(self, "启动失败", f"{command.command}\n\n{exc}")
