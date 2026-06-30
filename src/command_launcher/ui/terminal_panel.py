"""终端页签面板 — 管理多个嵌入式终端会话，按项目+shell 类型去重。"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from command_launcher.ui.terminal_widget import TerminalWidget

# 页签键类型：(project_id, shell_type)
_TabKey = tuple[str, str]


class TerminalPanel(QWidget):
    """终端页签管理面板。

    使用 QTabWidget 管理多个 TerminalWidget 实例。
    按 (project_id, shell_type) 元组作为唯一键实现去重：
    同一项目的同类型终端再次点击时聚焦已有页签而非重复创建。

    面板在无页签时自动隐藏，有页签时自动显示。
    """

    def __init__(
        self,
        current_project_callback: Callable[[], object | None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """初始化终端面板。

        Args:
            current_project_callback: 获取当前选中项目的回调（用于 "+" 按钮）。
            parent: 可选的 Qt 父控件。
        """
        super().__init__(parent)
        self.setObjectName("terminalPanel")
        self._get_current_project = current_project_callback
        # 页签键 → TerminalWidget 映射
        self._terminals: dict[_TabKey, TerminalWidget] = {}

        # 构建布局
        self._tabs = QTabWidget()
        self._tabs.setObjectName("terminalTabs")
        self._tabs.setTabsClosable(True)
        self._tabs.setMovable(True)

        # 添加 "+" 按钮在页签栏右侧
        self._add_button = QPushButton("+")
        self._add_button.setFixedSize(28, 28)
        self._add_button.setToolTip("新建终端页签")
        self._add_button.clicked.connect(self._on_add_tab_requested)
        self._tabs.setCornerWidget(self._add_button, corner=Qt.TopRightCorner)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._tabs)

        # 连接信号
        self._tabs.tabCloseRequested.connect(self.close_terminal)

        # 初始隐藏
        self.hide()

    # ── 公共 API ──────────────────────────────────────────────────────

    def open_or_focus(
        self,
        project_id: str,
        project_name: str,
        project_path: str,
        shell_type: str,
    ) -> None:
        """打开终端页签或聚焦已有页签。

        如果 (project_id, shell_type) 对应的终端已存在，切换到该页签；
        否则创建新的 TerminalWidget 并添加页签。

        Args:
            project_id: 项目 UUID。
            project_name: 项目显示名称（用于页签标签）。
            project_path: shell 工作目录。
            shell_type: 终端类型，\"cmd\" 或 \"powershell\"。
        """
        key = (project_id, shell_type)

        # 已存在 → 聚焦
        if key in self._terminals:
            tw = self._terminals[key]
            for i in range(self._tabs.count()):
                if self._tabs.widget(i) is tw:
                    self._tabs.setCurrentIndex(i)
                    break
            return

        # 新建 TerminalWidget
        tw = TerminalWidget(project_path, shell_type)
        self._terminals[key] = tw

        shell_label = "CMD" if shell_type == "cmd" else "PS"
        label = f"{project_name} - {shell_label}"
        index = self._tabs.addTab(tw, label)
        self._tabs.setCurrentIndex(index)
        tw.start_shell()

        # 确保面板可见
        self.show()

    def close_terminal(self, index: int) -> None:
        """关闭指定索引的终端页签。

        终止进程并从内部字典和 Tab 控件中移除。

        Args:
            index: 要关闭的页签索引。
        """
        widget = self._tabs.widget(index)
        if not isinstance(widget, TerminalWidget):
            return

        # 从字典中移除
        key_to_remove: _TabKey | None = None
        for key, tw in self._terminals.items():
            if tw is widget:
                key_to_remove = key
                break

        if key_to_remove is not None:
            del self._terminals[key_to_remove]

        # 终止进程并移除页签
        widget.terminate()
        self._tabs.removeTab(index)

        # 无剩余页签 → 隐藏面板
        if self._tabs.count() == 0:
            self.hide()

    def close_all(self) -> None:
        """终止所有终端并清除全部页签。

        在应用退出时调用，确保无残留进程。
        """
        for tw in list(self._terminals.values()):
            tw.terminate()
        self._terminals.clear()
        self._tabs.clear()
        self.hide()

    def close_terminals_for_project(self, project_id: str) -> None:
        """关闭指定项目的所有终端页签。

        在项目被删除时调用。

        Args:
            project_id: 被删除的项目 UUID。
        """
        keys_to_remove = [
            key for key in self._terminals if key[0] == project_id
        ]
        for key in keys_to_remove:
            tw = self._terminals[key]
            tw.terminate()
            del self._terminals[key]
            # 从 QTabWidget 中移除
            for i in range(self._tabs.count()):
                if self._tabs.widget(i) is tw:
                    self._tabs.removeTab(i)
                    break

        if self._tabs.count() == 0:
            self.hide()

    def has_terminals(self) -> bool:
        """检查是否有活跃的终端页签。

        Returns:
            True 如果至少有一个终端页签。
        """
        return len(self._terminals) > 0

    # ── 内部方法 ──────────────────────────────────────────────────────

    def _on_add_tab_requested(self) -> None:
        """"+" 按钮点击处理：为当前项目打开另一种 shell 类型。

        如果当前项目已有 CMD 页签，则打开 PS 页签，反之亦然。
        若两种都已存在则提示用户。
        """
        if self._get_current_project is None:
            return

        project = self._get_current_project()
        if project is None:
            QMessageBox.information(
                self, "提示", "请先在左侧选择一个项目。"
            )
            return

        # 确定需要打开哪种 shell 类型
        cmd_key = (project.id, "cmd")
        ps_key = (project.id, "powershell")

        has_cmd = cmd_key in self._terminals
        has_ps = ps_key in self._terminals

        if has_cmd and not has_ps:
            shell_type = "powershell"
        elif has_ps and not has_cmd:
            shell_type = "cmd"
        elif not has_cmd and not has_ps:
            shell_type = "cmd"  # 默认打开 CMD
        else:
            QMessageBox.information(
                self,
                "提示",
                f"项目 \"{project.name}\" 的 CMD 和 PowerShell 终端均已打开。",
            )
            return

        self.open_or_focus(
            project.id, project.name, project.path, shell_type
        )
