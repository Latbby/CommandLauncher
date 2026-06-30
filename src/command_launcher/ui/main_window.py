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
        """Load configuration and initialize the main window widgets.

        Args:
            store: Optional config store, primarily for tests.
            runner: Optional command runner, primarily for tests.
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
        self.cmd_button = QPushButton("打开命令提示符")
        self.powershell_button = QPushButton("打开 PowerShell")
        self.explorer_button = QPushButton("打开资源管理器")
        self.global_commands = QListWidget()
        self.project_commands = QListWidget()

        self._build_layout()
        self._connect_signals()
        self._refresh_projects()
        self._select_initial_project()

    def _build_layout(self) -> None:
        """Build the fixed two-column UI layout."""
        root = QHBoxLayout()
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        sidebar = QFrame()
        sidebar_layout = QVBoxLayout(sidebar)
        self.add_project_button = QPushButton("添加项目")
        self.remove_project_button = QPushButton("删除项目")
        sidebar_layout.addWidget(QLabel("项目"))
        sidebar_layout.addWidget(self.project_list, 1)
        sidebar_layout.addWidget(self.add_project_button)
        sidebar_layout.addWidget(self.remove_project_button)
        root.addWidget(sidebar, 1)

        content = QFrame()
        content_layout = QVBoxLayout(content)
        content_layout.addWidget(self.project_name)
        content_layout.addWidget(self.project_path)

        builtins = QHBoxLayout()
        builtins.addWidget(self.cmd_button)
        builtins.addWidget(self.powershell_button)
        builtins.addWidget(self.explorer_button)
        content_layout.addLayout(builtins)

        content_layout.addWidget(QLabel("全局命令"))
        content_layout.addWidget(self.global_commands)
        self.add_global_button = QPushButton("添加全局命令")
        self.edit_global_button = QPushButton("编辑全局命令")
        self.delete_global_button = QPushButton("删除全局命令")
        content_layout.addWidget(self.add_global_button)
        content_layout.addWidget(self.edit_global_button)
        content_layout.addWidget(self.delete_global_button)

        content_layout.addWidget(QLabel("项目命令"))
        content_layout.addWidget(self.project_commands)
        self.add_project_command_button = QPushButton("添加项目命令")
        self.edit_project_command_button = QPushButton("编辑项目命令")
        self.delete_project_command_button = QPushButton("删除项目命令")
        content_layout.addWidget(self.add_project_command_button)
        content_layout.addWidget(self.edit_project_command_button)
        content_layout.addWidget(self.delete_project_command_button)
        root.addWidget(content, 3)

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)

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
        """Render project details and command lists.

        Args:
            project: Project to render, or None for an empty selection.
        """
        enabled = bool(project and Path(project.path).exists())
        self.project_name.setText(project.name if project else "未选择项目")
        self.project_path.setText(project.path if project else "")
        for button in (self.cmd_button, self.powershell_button, self.explorer_button):
            button.setEnabled(enabled)

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
