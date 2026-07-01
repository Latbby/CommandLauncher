"""Dialogs for editing launcher commands."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
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
        self.setMinimumWidth(760)
        self.resize(760, 420)

        # ── 名称 ──
        name_label = QLabel("名称")
        self.name_input = QLineEdit(command.name if command else "")
        self.name_input.setPlaceholderText("例如：启动前端")

        # ── 命令 — 多行编辑区 ──
        cmd_label = QLabel("命令")
        self.command_input = QPlainTextEdit()
        self.command_input.setPlaceholderText("例如：npm run dev")
        self.command_input.setMinimumHeight(220)
        # 长命令按代码编辑器方式横向滚动，避免自动软换行造成参数排版混乱。
        self.command_input.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.command_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.command_input.setTabChangesFocus(True)
        if command:
            self.command_input.setPlainText(command.command)

        # 等宽字体 — 命令内容含脚本和参数，等宽便于阅读
        cmd_font = QFont("Consolas")
        cmd_font.setStyleHint(QFont.Monospace)
        cmd_font.setFixedPitch(True)
        self.command_input.setFont(cmd_font)

        # ── 布局 ──
        form = QFormLayout()
        form.setSpacing(10)
        form.addRow(name_label, self.name_input)
        form.addRow(cmd_label, self.command_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("保存")
        buttons.button(QDialogButtonBox.Cancel).setText("取消")
        buttons.button(QDialogButtonBox.Ok).setProperty("variant", "primary")
        buttons.button(QDialogButtonBox.Cancel).setProperty("variant", "secondary")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addSpacing(4)
        layout.addWidget(buttons)

    def command_values(self) -> tuple[str, str]:
        """返回去除首尾空白后的命令名称和命令文本。

        命令文本保留中间换行，便于编辑模式按用户原始排版回显。
        实际执行前由 CommandRunner 统一转换为单行，避免换行影响命令执行。
        """
        name = self.name_input.text().strip()
        command = self.command_input.toPlainText().strip()
        return name, command


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


class SettingsDialog(QDialog):
    """设置对话框 — 开机自启和退出行为。"""

    CLOSE_OPTIONS = [
        ("ask", "每次询问"),
        ("minimize", "最小化到系统托盘"),
        ("quit", "直接退出程序"),
    ]

    def __init__(
        self,
        auto_start: bool = False,
        close_action: str = "ask",
        parent=None,
    ) -> None:
        """初始化设置对话框。

        Args:
            auto_start: 当前开机自启状态。
            close_action: 当前退出行为。
            parent: 可选的 Qt 父控件。
        """
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setObjectName("settingsDialog")
        self.setFixedWidth(480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(14)

        title = QLabel("设置")
        title.setObjectName("settingsTitle")
        subtitle = QLabel("管理启动和关闭窗口时的默认行为")
        subtitle.setObjectName("settingsSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        start_card = QFrame()
        start_card.setObjectName("settingsCard")
        start_layout = QVBoxLayout(start_card)
        start_layout.setContentsMargins(16, 14, 16, 14)
        start_layout.setSpacing(8)

        start_label = QLabel("启动")
        start_label.setObjectName("settingsCardTitle")
        start_hint = QLabel("登录 Windows 后自动打开命令启动器")
        start_hint.setObjectName("settingsCardHint")
        start_hint.setWordWrap(True)
        self.auto_start_checkbox = QCheckBox("开机时自动启动命令启动器")
        self.auto_start_checkbox.setChecked(auto_start)

        start_layout.addWidget(start_label)
        start_layout.addWidget(start_hint)
        start_layout.addSpacing(4)
        start_layout.addWidget(self.auto_start_checkbox)
        layout.addWidget(start_card)

        close_card = QFrame()
        close_card.setObjectName("settingsCard")
        close_layout = QVBoxLayout(close_card)
        close_layout.setContentsMargins(16, 14, 16, 14)
        close_layout.setSpacing(10)

        close_label = QLabel("关闭窗口时")
        close_label.setObjectName("settingsCardTitle")
        close_hint = QLabel("关闭主窗口时执行所选操作")
        close_hint.setObjectName("settingsCardHint")
        close_hint.setWordWrap(True)

        self.close_combo = QComboBox()
        self.close_combo.setObjectName("settingsCloseCombo")
        for value, label in self.CLOSE_OPTIONS:
            self.close_combo.addItem(label, value)
        # 选中当前值
        for i, (value, _) in enumerate(self.CLOSE_OPTIONS):
            if value == close_action:
                self.close_combo.setCurrentIndex(i)
                break

        close_row = QFrame()
        close_row.setObjectName("settingsCloseActionRow")
        close_row_layout = QHBoxLayout(close_row)
        close_row_layout.setContentsMargins(0, 0, 0, 0)
        close_row_layout.setSpacing(12)
        close_row_label = QLabel("默认行为")
        close_row_label.setObjectName("settingsFieldLabel")
        close_row_layout.addWidget(close_row_label)
        close_row_layout.addStretch()
        close_row_layout.addWidget(self.close_combo)

        close_layout.addWidget(close_label)
        close_layout.addWidget(close_hint)
        close_layout.addWidget(close_row)
        layout.addWidget(close_card)

        layout.addSpacing(4)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("保存")
        buttons.button(QDialogButtonBox.Cancel).setText("取消")
        buttons.button(QDialogButtonBox.Ok).setProperty("variant", "primary")
        buttons.button(QDialogButtonBox.Cancel).setProperty("variant", "secondary")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def auto_start(self) -> bool:
        """返回用户选择的开机自启状态。"""
        return self.auto_start_checkbox.isChecked()

    def close_action(self) -> str:
        """返回用户选择的退出行为（ask / minimize / quit）。"""
        return self.close_combo.currentData()
