"""Generate application icon assets.

This script creates a theme-matched PNG source and a multi-size Windows ICO
for PyInstaller and Qt window icons.
"""

from __future__ import annotations

import struct
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen


ROOT = Path(__file__).resolve().parents[1]
PNG_PATH = ROOT / "assets" / "icon.png"
ICO_PATH = ROOT / "assets" / "icon.ico"
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)


def draw_icon(size: int) -> QImage:
    """Draw the application icon at the requested size.

    Args:
        size: Target square image size in pixels.

    Returns:
        A transparent ARGB image containing the command launcher icon.
    """
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    scale = size / 1024
    outer = QRectF(88 * scale, 88 * scale, 848 * scale, 848 * scale)
    outer_radius = 190 * scale
    inner = QRectF(206 * scale, 258 * scale, 612 * scale, 478 * scale)
    inner_radius = 66 * scale

    # 主体使用应用主色，保持与按钮和选中态一致。
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#5b5fe3"))
    painter.drawRoundedRect(outer, outer_radius, outer_radius)

    # 轻微叠加深色侧边，让小尺寸图标也有清晰轮廓。
    side_path = QPainterPath()
    side_path.addRoundedRect(outer, outer_radius, outer_radius)
    painter.setClipPath(side_path)
    painter.setBrush(QColor("#4a4ecf"))
    painter.drawRect(QRectF(612 * scale, 88 * scale, 324 * scale, 848 * scale))
    painter.setClipping(False)

    # 终端面板使用界面暖白底色，避免图标偏离当前浅色主题。
    painter.setBrush(QColor("#f8f7f4"))
    painter.drawRoundedRect(inner, inner_radius, inner_radius)

    header = QRectF(inner.left(), inner.top(), inner.width(), 108 * scale)
    header_path = QPainterPath()
    header_path.addRoundedRect(inner, inner_radius, inner_radius)
    painter.setClipPath(header_path)
    painter.setBrush(QColor("#eeede8"))
    painter.drawRect(header)
    painter.setClipping(False)

    # 三个状态点呼应桌面工具窗口，但保持颜色克制。
    dot_y = 312 * scale
    for x, color in ((266, "#d64545"), (326, "#d4d2cc"), (386, "#5b5fe3")):
        painter.setBrush(QColor(color))
        painter.drawEllipse(QRectF((x - 17) * scale, dot_y - 17 * scale, 34 * scale, 34 * scale))

    # 命令提示符是应用功能识别点：启动命令而非普通文件夹。
    pen = QPen(QColor("#4a4ecf"))
    pen.setWidthF(max(4.0, 34 * scale))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.drawLine(315 * scale, 493 * scale, 392 * scale, 570 * scale)
    painter.drawLine(392 * scale, 570 * scale, 315 * scale, 647 * scale)

    pen = QPen(QColor("#1c1c22"))
    pen.setWidthF(max(4.0, 34 * scale))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.drawLine(465 * scale, 650 * scale, 665 * scale, 650 * scale)

    painter.end()
    return image


def image_to_ico_dib(image: QImage) -> bytes:
    """Convert a QImage to a 32-bit DIB block for an ICO image entry.

    Args:
        image: Square ARGB image to encode.

    Returns:
        ICO-compatible DIB bytes containing BGRA pixels and an alpha mask.
    """
    width = image.width()
    height = image.height()
    dib = bytearray()
    and_row_bytes = ((width + 31) // 32) * 4

    # ICO DIB headers store double height because the AND mask follows pixels.
    dib.extend(
        struct.pack(
            "<IIIHHIIIIII",
            40,
            width,
            height * 2,
            1,
            32,
            0,
            width * height * 4 + and_row_bytes * height,
            0,
            0,
            0,
            0,
        )
    )

    for y in range(height - 1, -1, -1):
        for x in range(width):
            color = image.pixelColor(x, y)
            dib.extend((color.blue(), color.green(), color.red(), color.alpha()))

    for y in range(height - 1, -1, -1):
        row = bytearray(and_row_bytes)
        for x in range(width):
            # Alpha below 128 is marked transparent for older icon readers.
            if image.pixelColor(x, y).alpha() < 128:
                row[x // 8] |= 0x80 >> (x % 8)
        dib.extend(row)

    return bytes(dib)


def write_multi_size_ico(icon_path: Path, sizes: tuple[int, ...]) -> None:
    """Write a multi-resolution Windows ICO file.

    Args:
        icon_path: Destination .ico path.
        sizes: Square icon sizes to include.

    Returns:
        None.
    """
    images = [image_to_ico_dib(draw_icon(size)) for size in sizes]
    offset = 6 + 16 * len(images)

    header = bytearray(struct.pack("<HHH", 0, 1, len(images)))
    payload = bytearray()
    for size, data in zip(sizes, images, strict=True):
        # ICO stores 256 as 0 in the width and height byte fields.
        dimension = 0 if size == 256 else size
        header.extend(struct.pack("<BBBBHHII", dimension, dimension, 0, 0, 1, 32, len(data), offset))
        payload.extend(data)
        offset += len(data)

    icon_path.write_bytes(bytes(header + payload))


def main() -> None:
    """Generate icon.png and icon.ico in the assets directory.

    Args:
        None.

    Returns:
        None.
    """
    PNG_PATH.parent.mkdir(parents=True, exist_ok=True)
    draw_icon(1024).save(str(PNG_PATH), "PNG")
    write_multi_size_ico(ICO_PATH, ICO_SIZES)


if __name__ == "__main__":
    main()
