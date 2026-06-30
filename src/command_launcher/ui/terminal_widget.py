"""嵌入式终端控件 — 使用 Windows ConPTY (pywinpty) 运行 shell 并显示。

通过 PtyProcess + 工作线程实现完整的终端交互：
方向键、Tab 补全、命令行历史等全部可用。
"""

from __future__ import annotations

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtGui import QKeyEvent, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget
from winpty import PtyProcess

from command_launcher.ui.ansi_parser import AnsiParser

# 输出最大行数限制，防止长时间运行导致内存持续增长
_MAX_BLOCK_COUNT = 2000
_TRIM_BLOCK_COUNT = 500


# ── 工作线程：阻塞读取 PtyProcess 输出 ──────────────────────────────

class _TerminalReader(QThread):
    """工作线程：阻塞读取终端伪控制台输出并通知主线程。

    信号:
        data_received(bytes): 从终端读取到的原始字节数据。
        process_exited(int): 进程退出时发出，携带退出码。
    """

    data_received = Signal(bytes)
    process_exited = Signal(int)

    def __init__(self, process: PtyProcess) -> None:
        """初始化读取线程。

        Args:
            process: 已启动的 PtyProcess 实例。
        """
        super().__init__()
        self._process = process
        self._running = True

    def run(self) -> None:
        """在线程中循环读取终端输出直到进程退出或主动停止。

        使用阻塞 read() 高效等待数据，有数据时通过信号通知主线程。
        """
        while self._running:
            try:
                data = self._process.read(4096)
                if data:
                    self.data_received.emit(data)
            except EOFError:
                # Pty 已关闭
                break
            except Exception:
                break

        # 进程退出后获取退出码
        exit_code = self._process.exitstatus or 0
        self.process_exited.emit(exit_code)

    def stop(self) -> None:
        """请求线程停止。调用后线程将在下一次 read 返回后退出。"""
        self._running = False


# ── 终端输出显示区 ──────────────────────────────────────────────────

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
        """拦截键盘事件，将所有按键转发到进程。

        ConPTY 模式下方向键和 Tab 都发送到 shell 进程，
        shell 内部处理命令行编辑、补全和历史。

        处理规则:
        - 方向键/Home/End/PgUp/PgDn → 全部转发（ConPTY 支持）
        - Tab → 转发（shell 处理补全）
        - Enter/Backspace/Escape → 转发
        - Ctrl+C 无选中 → 发送 ETX (中断)
        - Ctrl+C 有选中 → 复制到剪贴板
        - Ctrl+V → 粘贴剪贴板内容
        - Ctrl+L → 转发（清屏）
        - 可打印字符 → 转发

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

        # Ctrl+L 清屏
        if modifiers == Qt.ControlModifier and key == Qt.Key_L:
            self.input_received.emit("\x0c")
            return

        # ── 全部按键转发到 ConPTY ──
        # 方向键
        if key == Qt.Key_Up:
            self.input_received.emit("\x1b[A")
            return
        if key == Qt.Key_Down:
            self.input_received.emit("\x1b[B")
            return
        if key == Qt.Key_Right:
            self.input_received.emit("\x1b[C")
            return
        if key == Qt.Key_Left:
            self.input_received.emit("\x1b[D")
            return

        # Home / End
        if key == Qt.Key_Home:
            self.input_received.emit("\x1b[H")
            return
        if key == Qt.Key_End:
            self.input_received.emit("\x1b[F")
            return

        # Page Up / Page Down
        if key == Qt.Key_PageUp:
            self.input_received.emit("\x1b[5~")
            return
        if key == Qt.Key_PageDown:
            self.input_received.emit("\x1b[6~")
            return

        # Delete
        if key == Qt.Key_Delete:
            self.input_received.emit("\x1b[3~")
            return
        if key == Qt.Key_Insert:
            self.input_received.emit("\x1b[2~")
            return

        # Enter
        if key in (Qt.Key_Return, Qt.Key_Enter):
            self.input_received.emit("\r")
            return

        # Backspace
        if key == Qt.Key_Backspace:
            self.input_received.emit("\x7f")
            return

        # Tab
        if key == Qt.Key_Tab:
            # Shift+Tab 发送反向 Tab
            if modifiers == Qt.ShiftModifier:
                self.input_received.emit("\x1b[Z")
            else:
                self.input_received.emit("\t")
            return

        # Escape
        if key == Qt.Key_Escape:
            self.input_received.emit("\x1b")
            return

        # 功能键 F1-F12
        if Qt.Key_F1 <= key <= Qt.Key_F12:
            fn = key - Qt.Key_F1 + 1
            self.input_received.emit(f"\x1b[1{fn}~"
                if fn <= 5 else f"\x1b[{11 + fn}~"
                if fn <= 8 else f"\x1b[{10 + fn}~")
            return

        # 可打印字符
        text = event.text()
        if text and not modifiers:
            self.input_received.emit(text)
            return


# ── 嵌入式终端控件 ──────────────────────────────────────────────────

class TerminalWidget(QWidget):
    """单个嵌入式终端会话。

    使用 Windows ConPTY (pywinpty PtyProcess) 运行 cmd.exe 或
    powershell.exe，在 QPlainTextEdit 中显示 ANSI 彩色输出，
    通过工作线程读取终端数据，支持完整的交互式终端功能。

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
        self._process: PtyProcess | None = None
        self._reader: _TerminalReader | None = None
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
        """启动 shell 进程（通过 ConPTY）并开始捕获输出。"""
        if self._process is not None:
            return

        # 构建 shell 参数
        if self._shell_type == "cmd":
            argv = ["cmd.exe", "/K", "cd", "/d", self._project_path]
        elif self._shell_type == "powershell":
            escaped = self._project_path.replace("'", "''")
            argv = [
                "powershell.exe",
                "-NoExit",
                "-Command",
                f"Set-Location -LiteralPath '{escaped}'",
            ]
        else:
            raise ValueError(f"不支持的 shell 类型: {self._shell_type}")

        # 通过 Windows ConPTY 启动进程
        self._process = PtyProcess.spawn(
            argv,
            cwd=self._project_path,
            dimensions=(40, 120),  # 终端尺寸 (行, 列)
        )

        # 启动工作线程读取输出
        self._reader = _TerminalReader(self._process)
        self._reader.data_received.connect(self._on_data_received)
        self._reader.process_exited.connect(self._on_process_exited)
        self._reader.start()

    def send_input(self, text: str) -> None:
        """向终端写入文本（包括控制序列）。

        Args:
            text: 要发送的文本或控制序列。
        """
        if self._process is not None and self._reader is not None:
            try:
                self._process.write(text)
            except Exception:
                pass

    def terminate(self) -> None:
        """终止进程和读取线程并清理资源。"""
        # 先停止读取线程
        if self._reader is not None:
            reader = self._reader
            self._reader = None
            reader.stop()
            reader.data_received.disconnect()
            reader.process_exited.disconnect()
            reader.quit()
            reader.wait(2000)

        # 终止进程
        if self._process is not None:
            process = self._process
            self._process = None
            try:
                if process.isalive():
                    process.terminate()
            except Exception:
                pass
            try:
                process.close()
            except Exception:
                pass

    def is_running(self) -> bool:
        """检查终端进程是否仍在运行。

        Returns:
            True 如果进程正在运行。
        """
        return (
            self._process is not None
            and self._reader is not None
            and self._process.isalive()
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

    def _on_data_received(self, data: bytes) -> None:
        """主线程回调：解析终端输出并追加到显示区。

        Args:
            data: 工作线程从 ConPTY 读取的原始字节数据。
        """
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

    def _on_process_exited(self, exit_code: int) -> None:
        """进程退出回调：追加退出信息并发出 finished 信号。

        Args:
            exit_code: 进程退出码。
        """
        # 追加退出提示到显示区
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

        # 清理读取线程
        self._reader = None
        self._process = None

        self.finished.emit(exit_code)
