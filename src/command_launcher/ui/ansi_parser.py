"""ANSI/VT100 转义序列增量解析器。

解析终端输出中的 SGR (Select Graphic Rendition) 转义序列，输出
(纯文本, QTextCharFormat) 片段列表，供 QPlainTextEdit 渲染使用。
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QTextCharFormat


# ── ANSI 标准 16 色映射 ──────────────────────────────────────────────
_ANSI_16_COLORS: dict[int, QColor] = {
    0: QColor(0, 0, 0),        # Black
    1: QColor(205, 0, 0),      # Red
    2: QColor(0, 205, 0),      # Green
    3: QColor(205, 205, 0),    # Yellow
    4: QColor(0, 0, 238),      # Blue
    5: QColor(205, 0, 205),    # Magenta
    6: QColor(0, 205, 205),    # Cyan
    7: QColor(229, 229, 229),  # White
}

# 亮色变体 (索引 8-15)
_ANSI_BRIGHT_COLORS: dict[int, QColor] = {
    8: QColor(127, 127, 127),   # Bright Black (Gray)
    9: QColor(255, 0, 0),       # Bright Red
    10: QColor(0, 255, 0),      # Bright Green
    11: QColor(255, 255, 0),    # Bright Yellow
    12: QColor(92, 92, 255),    # Bright Blue
    13: QColor(255, 0, 255),    # Bright Magenta
    14: QColor(0, 255, 255),    # Bright Cyan
    15: QColor(255, 255, 255),  # Bright White
}


def _build_256_color_map() -> dict[int, QColor]:
    """构建 256 色调色板。

    Returns:
        索引到 QColor 的映射字典。
    """
    color_map: dict[int, QColor] = {}

    # 0-15: 标准 ANSI 色
    for idx in range(16):
        if idx < 8:
            color_map[idx] = _ANSI_16_COLORS.get(idx, QColor(0, 0, 0))
        else:
            color_map[idx] = _ANSI_BRIGHT_COLORS.get(idx, QColor(255, 255, 255))

    # 16-231: 6×6×6 RGB 立方体
    for r in range(6):
        for g in range(6):
            for b in range(6):
                idx = 16 + (r * 36) + (g * 6) + b
                red = 0 if r == 0 else (r * 40 + 55)
                green = 0 if g == 0 else (g * 40 + 55)
                blue = 0 if b == 0 else (b * 40 + 55)
                color_map[idx] = QColor(red, green, blue)

    # 232-255: 24 级灰度
    for i in range(24):
        idx = 232 + i
        gray = i * 10 + 8
        color_map[idx] = QColor(gray, gray, gray)

    return color_map


_256_COLORS = _build_256_color_map()


class AnsiParser:
    """增量 ANSI/VT100 SGR 转义序列解析器。

    接受终端原始输出字节流，输出 (纯文本, QTextCharFormat) 片段列表。
    仅处理 SGR (m) 序列以控制颜色和文本属性；光标移动等序列被静默丢弃。
    """

    def __init__(self) -> None:
        """初始化增量缓冲区和默认格式状态。"""
        self._buffer: str = ""
        self._bold: bool = False
        self._dim: bool = False
        self._italic: bool = False
        self._underline: bool = False
        self._inverse: bool = False
        self._fg_color: QColor | None = None
        self._bg_color: QColor | None = None

    # ── 公共 API ──────────────────────────────────────────────────────

    def feed(self, data: str) -> list[tuple[str, QTextCharFormat]]:
        """喂入原始文本，返回格式化片段列表。

        未完成的转义序列保留在内部缓冲区，等待下次 feed 补充。

        Args:
            data: 终端输出的原始文本片段。

        Returns:
            (纯文本, 格式) 元组列表，其中文本不含任何转义序列。
        """
        self._buffer += data
        result: list[tuple[str, QTextCharFormat]] = []
        buf = self._buffer
        i = 0
        plain_start = 0
        length = len(buf)

        while i < length:
            if buf[i] == "\x1b":
                # 先把转义序列之前的纯文本输出
                if plain_start < i:
                    result.append(
                        (buf[plain_start:i], self._build_format())
                    )
                end = self._parse_escape(buf, i)
                if end == -1:
                    # 转义序列不完整，从 ESC 位置开始保留等待更多数据
                    self._buffer = buf[i:]
                    return result
                i = end
                plain_start = end
            else:
                i += 1

        # 尾部纯文本输出
        if plain_start < length:
            result.append((buf[plain_start:], self._build_format()))

        self._buffer = ""
        return result

    def reset(self) -> None:
        """重置解析器状态和缓冲区，所有格式回到默认值。"""
        self._buffer = ""
        self._bold = False
        self._dim = False
        self._italic = False
        self._underline = False
        self._inverse = False
        self._fg_color = None
        self._bg_color = None

    # ── 内部方法 ──────────────────────────────────────────────────────

    def _default_format(self) -> QTextCharFormat:
        """构造默认文本格式。

        Returns:
            无任何属性/颜色设置的 QTextCharFormat。
        """
        return QTextCharFormat()

    def _build_format(self) -> QTextCharFormat:
        """根据当前解析状态构造 QTextCharFormat。

        处理粗体、斜体、下划线、前景色、背景色和反色模式。

        Returns:
            反映当前格式状态的 QTextCharFormat 实例。
        """
        fmt = QTextCharFormat()

        if self._bold:
            fmt.setFontWeight(700)
        if self._italic:
            fmt.setFontItalic(True)
        if self._underline:
            fmt.setFontUnderline(True)

        if self._inverse:
            # 反色：交换前后景色
            fg = self._bg_color
            bg = self._fg_color
        else:
            fg = self._fg_color
            bg = self._bg_color

        if fg is not None:
            fmt.setForeground(fg)
        if bg is not None:
            fmt.setBackground(bg)

        return fmt

    def _parse_escape(self, text: str, start: int) -> int:
        """从 start 位置开始解析一个转义序列。

        支持 CSI 序列（ESC [ 后跟参数和终结字符）。
        非完整序列返回 -1，非 SGR 序列静默消费。

        Args:
            text: 包含转义序列的完整文本。
            start: ESC 字符 ('\\x1b') 的索引位置。

        Returns:
            转义序列结束后的下一个索引，不完整时返回 -1。
        """
        # 转义序列至少需要 ESC + 1 个字符
        if start + 1 >= len(text):
            return -1
        # CSI (Control Sequence Introducer): ESC [
        if text[start + 1] == "[":
            return self._parse_csi(text, start)
        # 其他转义序列，消费 ESC + 1 字符后返回
        return start + 2

    def _parse_csi(self, text: str, start: int) -> int:
        """解析 CSI 序列 ESC [ ... <final>。

        从 text[start] (=ESC) 开始扫描，收集参数直到遇到终结字符
        (0x40-0x7E 范围内)。如果未找到终结字符则返回 -1。

        Args:
            text: 包含 CSI 序列的文本。
            start: ESC 字符的索引。

        Returns:
            CSI 序列结束后的索引，或 -1。
        """
        i = start + 2  # 跳过 ESC [
        params_start = i
        params: list[int] = []

        while i < len(text):
            ch = text[i]
            code = ord(ch)
            if 0x40 <= code <= 0x7E:
                # 终结字符
                param_str = text[params_start:i]
                if param_str:
                    for part in param_str.split(";"):
                        # 空参数视为 0 (如 ESC[m)
                        try:
                            params.append(int(part) if part else 0)
                        except ValueError:
                            params.append(0)
                else:
                    params.append(0)
                self._dispatch_csi(ch, params)
                return i + 1
            i += 1
        # 未找到终结字符
        return -1

    def _dispatch_csi(self, final: str, params: list[int]) -> None:
        """根据 CSI 终结字符分派处理。

        Args:
            final: CSI 序列的终结字符 (如 'm', 'J', 'H')。
            params: 解析出的数值参数列表。
        """
        if final == "m":
            self._apply_sgr(params)
        # 其他序列 (J, K, H, f, A-D, G, s, u, ?25h, ?25l 等) 静默忽略

    def _apply_sgr(self, params: list[int]) -> None:
        """应用 SGR (Select Graphic Rendition) 参数。

        空参数列表等同于 [0]（重置）。

        Args:
            params: SGR 数值参数列表。
        """
        if not params:
            self._reset_state()
            return

        i = 0
        while i < len(params):
            code = params[i]

            # 重置 / 属性开关
            if code == 0:
                self._reset_state()
            elif code == 1:
                self._bold = True
            elif code == 2:
                self._dim = True
            elif code == 3:
                self._italic = True
            elif code == 4:
                self._underline = True
            elif code == 7:
                self._inverse = True
            elif code == 22:
                self._bold = False
                self._dim = False
            elif code == 23:
                self._italic = False
            elif code == 24:
                self._underline = False
            elif code == 27:
                self._inverse = False
            # 16 色前景 (30-37) 和亮色前景 (90-97)
            elif 30 <= code <= 37:
                self._fg_color = _ANSI_16_COLORS.get(code - 30)
            elif 90 <= code <= 97:
                self._fg_color = _ANSI_BRIGHT_COLORS.get(code - 82)
            # 16 色背景 (40-47) 和亮色背景 (100-107)
            elif 40 <= code <= 47:
                self._bg_color = _ANSI_16_COLORS.get(code - 40)
            elif 100 <= code <= 107:
                self._bg_color = _ANSI_BRIGHT_COLORS.get(code - 92)
            # 256 色前景 (38;5;N) / 背景 (48;5;N)
            elif code == 38 and i + 2 < len(params) and params[i + 1] == 5:
                color_idx = params[i + 2]
                self._fg_color = _256_COLORS.get(color_idx, QColor(255, 255, 255))
                i += 2
            elif code == 48 and i + 2 < len(params) and params[i + 1] == 5:
                color_idx = params[i + 2]
                self._bg_color = _256_COLORS.get(color_idx, QColor(0, 0, 0))
                i += 2
            # 默认色恢复 (39: 前景默认, 49: 背景默认)
            elif code == 39:
                self._fg_color = None
            elif code == 49:
                self._bg_color = None
            i += 1

    def _reset_state(self) -> None:
        """重置所有格式标志和颜色为默认值。"""
        self._bold = False
        self._dim = False
        self._italic = False
        self._underline = False
        self._inverse = False
        self._fg_color = None
        self._bg_color = None
