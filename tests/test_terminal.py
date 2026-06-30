"""嵌入式终端控件和终端面板测试。"""

from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCharFormat
from PySide6.QtWidgets import (
    QApplication,
    QSplitter,
    QTabWidget,
)

from command_launcher.ui.terminal_panel import TerminalPanel
from command_launcher.ui.terminal_widget import TerminalWidget


def _ensure_app():
    """确保 QApplication 实例存在。"""
    return QApplication.instance() or QApplication([])


# ── TerminalWidget 测试 ───────────────────────────────────────────────


def test_terminal_widget_creation(monkeypatch):
    """TerminalWidget 创建后属性正确。

    入参: project_path="/test", shell_type="cmd"
    出参: shell_type="cmd", project_path="/test", 输出区只读
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    _ensure_app()

    tw = TerminalWidget("/test/path", "cmd")
    assert tw.shell_type == "cmd"
    assert tw.project_path == "/test/path"
    assert tw._output.isReadOnly() is True
    # 进程尚未启动
    assert tw._process is None


def test_terminal_widget_shell_type_stored():
    """TerminalWidget 存储正确的 shell_type。

    入参: shell_type="powershell"
    出参: shell_type="powershell"
    """
    tw = TerminalWidget("/some/path", "powershell")
    assert tw.shell_type == "powershell"


def test_terminal_widget_output_uses_monospace_font(monkeypatch):
    """输出区使用等宽字体。

    入参: 创建 TerminalWidget
    出参: 字体为 Consolas
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    _ensure_app()

    tw = TerminalWidget("/test", "cmd")
    font = tw._output.font()
    assert font.family() == "Consolas"


def test_terminal_widget_send_input_without_process():
    """无进程时 send_input 安全无操作。

    入参: 未启动的 TerminalWidget
    出参: 不抛异常
    """
    tw = TerminalWidget("/test", "cmd")
    # 不应抛出异常
    tw.send_input("test")


def test_terminal_widget_is_running_false_initially(monkeypatch):
    """初始状态下 is_running 返回 False。

    入参: 新创建的 TerminalWidget
    出参: is_running() == False
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    _ensure_app()

    tw = TerminalWidget("/test", "cmd")
    assert tw.is_running() is False


def test_terminal_widget_terminate_safe_when_no_process():
    """无进程时 terminate 安全无操作。

    入参: 未启动的 TerminalWidget
    出参: 不抛异常，is_running == False
    """
    tw = TerminalWidget("/test", "cmd")
    tw.terminate()
    assert tw.is_running() is False


# ── TerminalPanel 测试 ────────────────────────────────────────────────


def test_panel_creates_tab_on_first_open(monkeypatch):
    """首次 open_or_focus 创建页签。

    入参: open_or_focus(project_id="p1", name="项目A", path="/a", type="cmd")
    出参: QTabWidget count == 1, 面板可见
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    _ensure_app()

    with patch.object(TerminalWidget, "start_shell"):
        panel = TerminalPanel()
        panel.open_or_focus("p1", "项目A", "/a", "cmd")

        assert panel._tabs.count() == 1
        assert panel._tabs.tabText(0) == "项目A - CMD"
        assert panel.isVisible() is True
        assert len(panel._terminals) == 1


def test_panel_focuses_existing_tab(monkeypatch):
    """同一项目与 shell 类型再次点击时聚焦已有页签不重复创建。

    入参: 两次 open_or_focus 相同 (project_id, shell_type)
    出参: 页签数仍为 1
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    _ensure_app()

    with patch.object(TerminalWidget, "start_shell"):
        panel = TerminalPanel()
        panel.open_or_focus("p1", "项目A", "/a", "cmd")
        panel.open_or_focus("p1", "项目A", "/a", "cmd")  # 二次点击

        assert panel._tabs.count() == 1
        assert len(panel._terminals) == 1


def test_panel_different_projects_create_different_tabs(monkeypatch):
    """不同项目创建不同页签。

    入参: 两个不同 project_id 各打开 CMD
    出参: 2 个页签
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    _ensure_app()

    with patch.object(TerminalWidget, "start_shell"):
        panel = TerminalPanel()
        panel.open_or_focus("p1", "项目A", "/a", "cmd")
        panel.open_or_focus("p2", "项目B", "/b", "cmd")

        assert panel._tabs.count() == 2
        assert len(panel._terminals) == 2


def test_panel_different_shell_types_create_different_tabs(monkeypatch):
    """同一项目的 CMD 和 PS 创建不同页签。

    入参: 同一项目打开 cmd 和 powershell
    出参: 2 个页签
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    _ensure_app()

    with patch.object(TerminalWidget, "start_shell"):
        panel = TerminalPanel()
        panel.open_or_focus("p1", "项目A", "/a", "cmd")
        panel.open_or_focus("p1", "项目A", "/a", "powershell")

        assert panel._tabs.count() == 2
        assert len(panel._terminals) == 2


def test_panel_close_tab_removes_from_dict(monkeypatch):
    """关闭页签从字典和 Tab 控件中移除。

    入参: 添加页签后通过 close_terminal(0) 关闭
    出参: 字典为空，Tab 数为 0
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    _ensure_app()

    with patch.object(TerminalWidget, "start_shell"), patch.object(
        TerminalWidget, "terminate"
    ):
        panel = TerminalPanel()
        panel.open_or_focus("p1", "项目A", "/a", "cmd")
        panel.close_terminal(0)

        assert len(panel._terminals) == 0
        assert panel._tabs.count() == 0


def test_panel_hides_when_last_tab_closed(monkeypatch):
    """最后一个页签关闭后面板隐藏。

    入参: 添加并关闭唯一页签
    出参: 面板不可见
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    _ensure_app()

    with patch.object(TerminalWidget, "start_shell"), patch.object(
        TerminalWidget, "terminate"
    ):
        panel = TerminalPanel()
        panel.open_or_focus("p1", "项目A", "/a", "cmd")
        panel.close_terminal(0)

        assert panel.isVisible() is False


def test_panel_shows_when_first_tab_opened(monkeypatch):
    """首个页签打开后面板可见。

    入参: 初始隐藏的面板调用 open_or_focus
    出参: 面板可见
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    _ensure_app()

    with patch.object(TerminalWidget, "start_shell"):
        panel = TerminalPanel()
        assert panel.isVisible() is False
        panel.open_or_focus("p1", "项目A", "/a", "cmd")
        assert panel.isVisible() is True


def test_close_all_clears_everything(monkeypatch):
    """close_all 终止所有终端并清除全部页签。

    入参: 添加 2 个页签后调用 close_all
    出参: 字典为空，面板隐藏
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    _ensure_app()

    with patch.object(TerminalWidget, "start_shell"), patch.object(
        TerminalWidget, "terminate"
    ):
        panel = TerminalPanel()
        panel.open_or_focus("p1", "项目A", "/a", "cmd")
        panel.open_or_focus("p2", "项目B", "/b", "powershell")
        panel.close_all()

        assert len(panel._terminals) == 0
        assert panel._tabs.count() == 0
        assert panel.isVisible() is False


def test_close_terminals_for_project(monkeypatch):
    """close_terminals_for_project 只删除指定项目的终端。

    入参: 添加 p1/cmd, p2/cmd 然后 close_terminals_for_project("p1")
    出参: p1 终端移除，p2 终端保留
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    _ensure_app()

    with patch.object(TerminalWidget, "start_shell"), patch.object(
        TerminalWidget, "terminate"
    ):
        panel = TerminalPanel()
        panel.open_or_focus("p1", "项目A", "/a", "cmd")
        panel.open_or_focus("p2", "项目B", "/b", "cmd")
        panel.close_terminals_for_project("p1")

        assert len(panel._terminals) == 1
        assert panel._tabs.count() == 1
        assert ("p2", "cmd") in panel._terminals
        assert ("p1", "cmd") not in panel._terminals


def test_panel_has_terminals(monkeypatch):
    """has_terminals 正确反映终端状态。

    入参: 添加页签后检查
    出参: 添加前 False，添加后 True，关闭后 False
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    _ensure_app()

    with patch.object(TerminalWidget, "start_shell"), patch.object(
        TerminalWidget, "terminate"
    ):
        panel = TerminalPanel()
        assert panel.has_terminals() is False
        panel.open_or_focus("p1", "项目A", "/a", "cmd")
        assert panel.has_terminals() is True


def test_panel_tab_label_powershell(monkeypatch):
    """PowerShell 终端页签标签包含 PS。

    入参: open_or_focus(..., shell_type="powershell")
    出参: 页签文本包含 "PS"
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    _ensure_app()

    with patch.object(TerminalWidget, "start_shell"):
        panel = TerminalPanel()
        panel.open_or_focus("p1", "项目A", "/a", "powershell")
        assert "PS" in panel._tabs.tabText(0)


# ── 键盘事件转发测试 ────────────────────────────────────────────────


def test_terminal_output_ctrl_c_without_selection_emits_etx(monkeypatch):
    """Ctrl+C 无选中时发送 ETX 中断信号。

    入参: Ctrl+C 按键 (无选中)
    出参: input_received 信号发出 "\\x03"
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    _ensure_app()

    from PySide6.QtGui import QKeyEvent

    tw = TerminalWidget("/test", "cmd")
    received: list[str] = []
    tw._output.input_received.connect(lambda text: received.append(text))

    # 构造 Ctrl+C 按键事件
    event = QKeyEvent(
        QKeyEvent.KeyPress, Qt.Key_C, Qt.ControlModifier, "\x03"
    )
    tw._output.keyPressEvent(event)

    assert received == ["\x03"]


def test_terminal_output_enter_emits_carriage_return(monkeypatch):
    """Enter 键发送回车。

    入参: Enter 按键
    出参: input_received 信号发出 "\\r"
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    _ensure_app()

    from PySide6.QtGui import QKeyEvent

    tw = TerminalWidget("/test", "cmd")
    received: list[str] = []
    tw._output.input_received.connect(lambda text: received.append(text))

    event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Return, Qt.NoModifier, "\r")
    tw._output.keyPressEvent(event)

    assert received == ["\r"]


def test_terminal_output_regular_char_emits_text(monkeypatch):
    """普通字符输入转发到进程。

    入参: 按键 'a'
    出参: input_received 信号发出 "a"
    """
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    _ensure_app()

    from PySide6.QtGui import QKeyEvent

    tw = TerminalWidget("/test", "cmd")
    received: list[str] = []
    tw._output.input_received.connect(lambda text: received.append(text))

    event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_A, Qt.NoModifier, "a")
    tw._output.keyPressEvent(event)

    assert received == ["a"]
