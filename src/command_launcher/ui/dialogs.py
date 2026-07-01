"""Dialogs for editing launcher commands."""

from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from command_launcher.models import LaunchCommand


class CommandDialog(QDialog):
    """Dialog for creating or editing a launch command."""

    def __init__(self, command: LaunchCommand | None = None, parent=None) -> None:
        """Initialize fields from an optional existing command.

        Args:
            command: Existing command values for edit mode.
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("编辑命令" if command else "添加命令")
        self.setFixedWidth(460)
        self.name_input = QLineEdit(command.name if command else "")
        self.command_input = QLineEdit(command.command if command else "")
        self.name_input.setPlaceholderText("例如：启动前端")
        self.command_input.setPlaceholderText("例如：npm run dev")

        # 命令内容通常包含脚本和参数，等宽字体更便于阅读。
        command_font = QFont("Consolas")
        command_font.setStyleHint(QFont.Monospace)
        command_font.setFixedPitch(True)
        self.command_input.setFont(command_font)

        form = QFormLayout()
        form.addRow("名称", self.name_input)
        form.addRow("命令", self.command_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("保存")
        buttons.button(QDialogButtonBox.Cancel).setText("取消")
        buttons.button(QDialogButtonBox.Ok).setProperty("variant", "primary")
        buttons.button(QDialogButtonBox.Cancel).setProperty("variant", "secondary")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def command_values(self) -> tuple[str, str]:
        """Return trimmed command name and command text.

        Returns:
            Tuple containing display name and command text.
        """
        return self.name_input.text().strip(), self.command_input.text().strip()


class CloseConfirmDialog(QDialog):
    """关闭窗口确认对话框 — 选择最小化到系统托盘还是退出程序。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("关闭命令启动器")
        self.setFixedWidth(360)

        message = QLabel("请选择关闭窗口时的操作：")
        hint = QLabel("最小化后可通过系统托盘图标恢复窗口")
        hint.setStyleSheet("color: #888; font-size: 12px;")

        self.remember_checkbox = QCheckBox("记住我的选择")

        minimize_btn = QPushButton("最小化到系统托盘")
        quit_btn = QPushButton("退出程序")
        minimize_btn.setProperty("variant", "primary")
        quit_btn.setProperty("variant", "secondary")

        minimize_btn.clicked.connect(self._on_minimize)
        quit_btn.clicked.connect(self._on_quit)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(minimize_btn)
        button_layout.addWidget(quit_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(message)
        layout.addWidget(hint)
        layout.addSpacing(8)
        layout.addWidget(self.remember_checkbox)
        layout.addSpacing(12)
        layout.addLayout(button_layout)

        self._should_minimize = False

    def _on_minimize(self) -> None:
        self._should_minimize = True
        self.accept()

    def _on_quit(self) -> None:
        self._should_minimize = False
        self.accept()

    def should_minimize(self) -> bool:
        """返回用户是否选择了最小化。"""
        return self._should_minimize

    def remember_choice(self) -> bool:
        """返回用户是否勾选了"记住我的选择"。"""
        return self.remember_checkbox.isChecked()
