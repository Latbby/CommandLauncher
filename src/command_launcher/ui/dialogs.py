"""Dialogs for editing launcher commands."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
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
        self.setWindowTitle("命令")
        self.name_input = QLineEdit(command.name if command else "")
        self.command_input = QLineEdit(command.command if command else "")

        form = QFormLayout()
        form.addRow("名称", self.name_input)
        form.addRow("命令", self.command_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("确定")
        buttons.button(QDialogButtonBox.Cancel).setText("取消")
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
