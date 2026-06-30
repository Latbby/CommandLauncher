"""嵌入式终端控件 — 使用 QProcess 运行 shell 并在 QPlainTextEdit 中显示。"""

from __future__ import annotations

from PySide6.QtCore import QProcess, Qt, Signal
from PySide6.QtGui import QKeyEvent, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget

from command_launcher.ui.ansi_parser import AnsiParser

# 输出最大行数限制，防止长时间运行导致内存持续增长
_MAX_BLOCK_COUNT = 2000
_TRIM_BLOCK_COUNT = 500


class _TerminalOutput(QPlainTextEdit):
    """终端输出显示区域，拦截键盘事件转发到进程 stdin。

    信号:
        input_received(str): 用户输入文本需要转发到进程时发出。
    """

    input_received = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """初始化只读终端输出显示区。"""
        super().__init__(parent)
        self.setReadOnly(True)
        self.setUndoRedoEnabled(False)
        self.setObjectName("terminalOutput")
        # 使用等宽字体
        font = self.font()
        font.setFamily("Consolas")
        font.setPointSize(10)
        self.setFont(font)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """拦截键盘事件，将可输入字符转发到进程。

        处理规则:
        - 可打印字符 + Enter/Backspace/Tab/Escape → 转发
        - Ctrl+C 无选中 → 发送 ETX (中断)
        - Ctrl+C 有选中 → 复制（默认行为）
        - Ctrl+V → 粘贴剪贴板内容到进程
        - 方向键/Home/End/PgUp/PgDn → 滚动（readOnly 下默认行为）

        Args:
            event: Qt 键盘事件。
        """
        key = event.key()
        modifiers = event.modifiers()

        # Ctrl+C 处理
        if modifiers == Qt.ControlModifier and key == Qt.Key_C:
            cursor = self.textCursor()
            if cursor.hasSelection():
                super().keyPressEvent(event)  # 正常复制
            else:
                self.input_received.emit("\x03")  # 发送中断信号
            return

        # Ctrl+V 粘贴
        if modifiers == Qt.ControlModifier and key == Qt.Key_V:
            from PySide6.QtWidgets import QApplication

            clipboard = QApplication.clipboard()
            if clipboard:
                self.input_received.emit(clipboard.text())
            return

        # 可转发到进程的按键
        if key in (Qt.Key_Return, Qt.Key_Enter):
            self.input_received.emit("\r")
            return
        if key == Qt.Key_Backspace:
            self.input_received.emit("\x7f")
            return
        if key == Qt.Key_Tab:
            self.input_received.emit("\t")
            return
        if key == Qt.Key_Escape:
            self.input_received.emit("\x1b")
            return

        # 可打印字符
        text = event.text()
        if text and not modifiers:
            self.input_received.emit(text)
            return

        # 方向键等：交给默认处理（只读模式下仅滚动）
        super().keyPressEvent(event)


class TerminalWidget(QWidget):
    """单个嵌入式终端会话。

    使用 QProcess 运行 cmd.exe 或 powershell.exe，在 QPlainTextEdit
    中显示 ANSI 彩色输出，并将用户键盘输入转发到进程 stdin。

    信号:
        finished(int): 进程退出时发出，携带退出码。
    """

    finished = Signal(int)

    def __init__(
        self,
        project_path: str,
        shell_type: str,
        parent: QWidget | None = None,
    ) -> None:
        """初始化终端控件。

        Args:
            project_path: shell 的工作目录。
            shell_type: 终端类型，\"cmd\" 或 \"powershell\"。
            parent: 可选的 Qt 父控件。
        """
        super().__init__(parent)
        self._project_path = project_path
        self._shell_type = shell_type
        self._process: QProcess | None = None
        self._parser = AnsiParser()

        # 构建布局
        self._output = _TerminalOutput()
        self._output.input_received.connect(self.send_input)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._output)

    # ── 公共 API ──────────────────────────────────────────────────────

    def start_shell(self) -> None:
        """启动 shell 进程并开始捕获输出。"""
        if self._process is not None:
            return

        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.MergedChannels)
        self._process.setWorkingDirectory(self._project_path)

        # 根据 shell 类型设置程序和参数
        if self._shell_type == "cmd":
            self._process.setProgram("cmd.exe")
            self._process.setArguments(
                ["/K", "cd", "/d", self._project_path]
            )
        elif self._shell_type == "powershell":
            # 转义路径中的单引号
            escaped = self._project_path.replace("'", "''")
            self._process.setProgram("powershell.exe")
            self._process.setArguments(
                [
                    "-NoExit",
                    "-Command",
                    f"Set-Location -LiteralPath '{escaped}'",
                ]
            )

        # 连接信号
        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.finished.connect(self._on_finished)
        self._process.errorOccurred.connect(self._on_error)

        self._process.start()

    def send_input(self, text: str) -> None:
        """向进程标准输入写入文本。

        Args:
            text: 要发送的文本。
        """
        if (
            self._process is not None
            and self._process.state() == QProcess.Running
        ):
            self._process.write(text.encode("utf-8"))

    def terminate(self) -> None:
        """优雅终止进程：先 terminate，等 3 秒后强制 kill。"""
        if self._process is None:
            return
        state = self._process.state()
        if state not in (QProcess.NotRunning,):
            self._process.terminate()
            if not self._process.waitForFinished(3000):
                self._process.kill()
                self._process.waitForFinished(2000)
        self._process = None

    def is_running(self) -> bool:
        """检查进程是否仍在运行。

        Returns:
            True 如果进程正在运行。
        """
        return (
            self._process is not None
            and self._process.state() == QProcess.Running
        )

    @property
    def shell_type(self) -> str:
        """终端类型。

        Returns:
            \"cmd\" 或 \"powershell\"。
        """
        return self._shell_type

    @property
    def project_path(self) -> str:
        """终端工作目录。

        Returns:
            项目路径字符串。
        """
        return self._project_path

    # ── 内部方法 ──────────────────────────────────────────────────────

    def _on_stdout(self) -> None:
        """读取进程输出，解析 ANSI 并追加到显示区。"""
        if self._process is None:
            return
        data = self._process.readAllStandardOutput().data()
        try:
            text = data.decode("utf-8", errors="replace")
        except UnicodeDecodeError:
            text = data.decode("latin-1", errors="replace")

        segments = self._parser.feed(text)
        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.End)

        for segment_text, fmt in segments:
            cursor.insertText(segment_text, fmt)

        # 确保显示区跟随最新输出
        self._output.ensureCursorVisible()

        # 限制最大行数，防止内存无限增长
        self._trim_output()

    def _trim_output(self) -> None:
        """当输出行数超过上限时裁剪最早的行。"""
        doc = self._output.document()
        if doc.blockCount() <= _MAX_BLOCK_COUNT:
            return

        # 从开头选择要删除的块
        remove_count = doc.blockCount() - _TRIM_BLOCK_COUNT
        cursor = QTextCursor(doc.firstBlock())
        for _ in range(remove_count):
            cursor.movePosition(QTextCursor.NextBlock, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()

    def _on_finished(self, exit_code: int) -> None:
        """进程退出时发出信号并在显示区追加退出信息。

        Args:
            exit_code: 进程退出码。
        """
        # 向显示区追加退出提示
        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.End)
        exit_fmt = self._parser._default_format()
        exit_fmt.setForeground(
            QWidget().palette().color(self._output.palette().WindowText)
        )
        cursor.insertText(
            f"\n\n[进程已退出，退出码: {exit_code}]\n", exit_fmt
        )
        self._output.ensureCursorVisible()
        self.finished.emit(exit_code)

    def _on_error(self, error: QProcess.ProcessError) -> None:
        """进程启动失败时在显示区追加错误信息。

        Args:
            error: QProcess 错误码。
        """
        error_messages = {
            QProcess.FailedToStart: "无法启动 shell 程序，请检查 cmd.exe 或 powershell.exe 是否可用。",
            QProcess.Crashed: "Shell 进程意外崩溃。",
            QProcess.Timedout: "等待 Shell 进程超时。",
            QProcess.WriteError: "向 Shell 进程写入数据失败。",
            QProcess.ReadError: "读取 Shell 进程输出失败。",
        }
        msg = error_messages.get(error, f"未知错误 (错误码: {error})")

        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.End)
        error_fmt = self._parser._default_format()
        error_fmt.setForeground(
            QWidget().palette().color(self._output.palette().WindowText)
        )
        cursor.insertText(f"\n\n[错误] {msg}\n", error_fmt)
        self._output.ensureCursorVisible()
