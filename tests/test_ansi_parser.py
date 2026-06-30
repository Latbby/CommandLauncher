"""ANSI 转义序列解析器单元测试。"""

from PySide6.QtGui import QColor, QTextCharFormat

from command_launcher.ui.ansi_parser import AnsiParser


def _default_fmt() -> QTextCharFormat:
    """构造默认格式用于比较。"""
    return QTextCharFormat()


def test_plain_text_passthrough():
    """纯文本无转义序列时原样输出。

    入参: "hello world"
    出参: [(text="hello world", format=default)]
    """
    parser = AnsiParser()
    segments = parser.feed("hello world")
    assert len(segments) == 1
    text, fmt = segments[0]
    assert text == "hello world"
    assert fmt.fontWeight() == _default_fmt().fontWeight()


def test_reset_code():
    """ESC[0m 重置所有格式。

    入参: "bold\x1b[0m normal"
    出参: 两段文本均为默认格式（重置后格式不变）
    """
    parser = AnsiParser()
    segments = parser.feed("bold\x1b[0m normal")
    assert len(segments) == 2
    assert segments[0][0] == "bold"
    assert segments[1][0] == " normal"


def test_bold_code():
    """ESC[1m 启用粗体。

    入参: "\x1b[1mbold"
    出参: 粗体文本
    """
    parser = AnsiParser()
    segments = parser.feed("\x1b[1mbold")
    assert len(segments) == 1
    text, fmt = segments[0]
    assert text == "bold"
    assert fmt.fontWeight() == 700


def test_fg_color_16():
    """ESC[31m 设置红色前景。

    入参: "\x1b[31mred"
    出参: 红色前景文本
    """
    parser = AnsiParser()
    segments = parser.feed("\x1b[31mred")
    assert len(segments) == 1
    text, fmt = segments[0]
    assert text == "red"
    assert fmt.foreground().color() == QColor(205, 0, 0)


def test_bg_color_16():
    """ESC[44m 设置蓝色背景。

    入参: "\x1b[44mblue bg"
    出参: 蓝色背景文本
    """
    parser = AnsiParser()
    segments = parser.feed("\x1b[44mblue bg")
    assert len(segments) == 1
    text, fmt = segments[0]
    assert text == "blue bg"
    assert fmt.background().color() == QColor(0, 0, 238)


def test_bright_fg():
    """ESC[91m 设置亮红色前景。

    入参: "\x1b[91mbright red"
    出参: 亮红色前景文本
    """
    parser = AnsiParser()
    segments = parser.feed("\x1b[91mbright red")
    text, fmt = segments[0]
    assert text == "bright red"
    assert fmt.foreground().color() == QColor(255, 0, 0)


def test_256_color_fg():
    """ESC[38;5;196m 设置 256 色调色板前景。

    入参: "\x1b[38;5;196mred"
    出参: 红色前景（256 色索引 196）
    """
    parser = AnsiParser()
    segments = parser.feed("\x1b[38;5;196mred")
    text, fmt = segments[0]
    assert text == "red"
    # 索引 196 在 6×6×6 立方体中是纯红色
    assert fmt.foreground().color() == QColor(255, 0, 0)


def test_256_color_bg():
    """ESC[48;5;21m 设置 256 色调色板背景。

    入参: "\x1b[48;5;21mblue bg"
    出参: 蓝色背景
    """
    parser = AnsiParser()
    segments = parser.feed("\x1b[48;5;21mblue bg")
    text, fmt = segments[0]
    assert text == "blue bg"
    assert fmt.background().color() == QColor(0, 0, 255)


def test_compound_sgr():
    """复合 SGR 代码用分号分隔。

    入参: "\x1b[1;31mbold red"
    出参: 粗体 + 红色前景
    """
    parser = AnsiParser()
    segments = parser.feed("\x1b[1;31mbold red")
    text, fmt = segments[0]
    assert text == "bold red"
    assert fmt.fontWeight() == 700
    assert fmt.foreground().color() == QColor(205, 0, 0)


def test_incomplete_escape_buffering():
    """跨数据块的不完整转义序列正确缓冲。

    第一块入参: "text\x1b[3"
    第二块入参: "1mred"
    出参: 第一块输出 "text"，第二块输出 "red"（红色前景）
    """
    parser = AnsiParser()
    segments1 = parser.feed("text\x1b[3")
    assert len(segments1) == 1
    assert segments1[0][0] == "text"

    segments2 = parser.feed("1mred")
    assert len(segments2) == 1
    assert segments2[0][0] == "red"
    assert segments2[0][1].foreground().color() == QColor(205, 0, 0)


def test_reset_state():
    """重置后格式恢复默认。

    入参: "\x1b[1mbold\x1b[0mnormal"
    出参: 两段，第一段粗体，第二段默认
    """
    parser = AnsiParser()
    segments = parser.feed("\x1b[1mbold\x1b[0mnormal")
    assert len(segments) == 2
    assert segments[0][0] == "bold"
    assert segments[0][1].fontWeight() == 700
    assert segments[1][0] == "normal"
    assert segments[1][1].fontWeight() == _default_fmt().fontWeight()


def test_cursor_sequences_ignored():
    """光标移动序列 (H, J, K 等) 被静默消费且不改变格式。

    入参: "before\x1b[2J\x1b[Hafter"
    出参: 两段文本格式一致，转义序列被移除
    """
    parser = AnsiParser()
    segments = parser.feed("before\x1b[2J\x1b[Hafter")
    assert len(segments) == 2
    assert segments[0][0] == "before"
    assert segments[1][0] == "after"
    # 两段格式应相同（光标序列未改变 SGR 状态）
    assert segments[0][1].fontWeight() == segments[1][1].fontWeight()


def test_multiple_sgr_in_sequence():
    """连续两个 SGR 序列正确切换颜色。

    入参: "\x1b[31mred\x1b[34mblue"
    出参: 两段，分别为红色和蓝色
    """
    parser = AnsiParser()
    segments = parser.feed("\x1b[31mred\x1b[34mblue")
    assert len(segments) == 2
    assert segments[0][0] == "red"
    assert segments[0][1].foreground().color() == QColor(205, 0, 0)
    assert segments[1][0] == "blue"
    assert segments[1][1].foreground().color() == QColor(0, 0, 238)


def test_italic_code():
    """ESC[3m 启用斜体。

    入参: "\x1b[3mitalic"
    出参: 斜体文本
    """
    parser = AnsiParser()
    segments = parser.feed("\x1b[3mitalic")
    text, fmt = segments[0]
    assert text == "italic"
    assert fmt.fontItalic() is True


def test_underline_code():
    """ESC[4m 启用下划线。

    入参: "\x1b[4munderline"
    出参: 带下划线文本
    """
    parser = AnsiParser()
    segments = parser.feed("\x1b[4munderline")
    text, fmt = segments[0]
    assert text == "underline"
    assert fmt.fontUnderline() is True


def test_empty_sgr_params_acts_as_reset():
    """空 SGR 参数等同重置。

    入参: "\x1b[31mred\x1b[mnormal"
    出参: 两段，第一段红色，第二段默认
    """
    parser = AnsiParser()
    segments = parser.feed("\x1b[31mred\x1b[mnormal")
    assert len(segments) == 2
    assert segments[0][0] == "red"
    assert segments[0][1].foreground().color() == QColor(205, 0, 0)
    assert segments[1][0] == "normal"
    assert segments[1][1].foreground().color() != QColor(205, 0, 0)


def test_feed_empty_string():
    """空字符串不产生任何输出。

    入参: ""
    出参: []
    """
    parser = AnsiParser()
    segments = parser.feed("")
    assert segments == []


def test_without_reset_colors_accumulate():
    """未重置时颜色状态在不同 feed 间保持。

    第一块入参: "\x1b[31m"
    第二块入参: "red text"
    出参: 两段红色文本
    """
    parser = AnsiParser()
    segments1 = parser.feed("\x1b[31m")
    assert len(segments1) == 0  # 仅转义序列无可见文本

    segments2 = parser.feed("red text")
    assert len(segments2) == 1
    assert segments2[0][1].foreground().color() == QColor(205, 0, 0)


def test_reset_method():
    """reset() 清除所有状态和缓冲区。

    入参: 先 feed 部分数据后 reset
    出参: 之后 feed 使用默认格式
    """
    parser = AnsiParser()
    parser.feed("\x1b[31m\x1b[1mpartial")
    parser.reset()
    segments = parser.feed("after reset")
    assert len(segments) == 1
    text, fmt = segments[0]
    assert text == "after reset"
    assert fmt.fontWeight() == _default_fmt().fontWeight()


def test_inverse_swaps_fg_bg():
    """ESC[7m 反色模式交换前景色和背景色。

    入参: "\x1b[31m\x1b[44m\x1b[7minverse"
    出参: 前景蓝色、背景红色（与设置相反）
    """
    parser = AnsiParser()
    segments = parser.feed("\x1b[31m\x1b[44m\x1b[7minverse")
    text, fmt = segments[0]
    assert text == "inverse"
    # 设置了红色前景、蓝色背景，反色后应：前景 = 蓝色，背景 = 红色
    assert fmt.foreground().color() == QColor(0, 0, 238)
    assert fmt.background().color() == QColor(205, 0, 0)
