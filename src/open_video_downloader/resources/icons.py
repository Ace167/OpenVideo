"""Programmatic vector-like icon generators for application assets."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)


def create_app_icon(size: int = 64) -> QIcon:
    """Create a high-resolution, modern rounded application icon."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 1. Background gradient rounded rectangle
    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0.0, QColor("#0284c7"))  # Sky blue
    gradient.setColorAt(1.0, QColor("#0369a1"))  # Deep blue

    rect = QRectF(2, 2, size - 4, size - 4)
    radius = size * 0.22
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)

    painter.fillPath(path, QBrush(gradient))

    # Border glow
    pen = QPen(QColor(255, 255, 255, 60), 1.5)
    painter.setPen(pen)
    painter.drawPath(path)

    # 2. Draw modern Play / Download glyph in center
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(255, 255, 255, 240)))

    # Play triangle on left
    tri_path = QPainterPath()
    tri_path.moveTo(size * 0.30, size * 0.32)
    tri_path.lineTo(size * 0.52, size * 0.46)
    tri_path.lineTo(size * 0.30, size * 0.60)
    tri_path.closeSubpath()
    painter.drawPath(tri_path)

    # Downward arrow on right
    arrow_path = QPainterPath()
    arrow_path.moveTo(size * 0.66, size * 0.32)
    arrow_path.lineTo(size * 0.66, size * 0.54)
    arrow_path.lineTo(size * 0.58, size * 0.54)
    arrow_path.lineTo(size * 0.70, size * 0.68)
    arrow_path.lineTo(size * 0.82, size * 0.54)
    arrow_path.lineTo(size * 0.74, size * 0.54)
    arrow_path.lineTo(size * 0.74, size * 0.32)
    arrow_path.closeSubpath()
    painter.drawPath(arrow_path)

    painter.end()
    return QIcon(pixmap)


def create_symbol_icon(symbol_type: str, size: int = 24, color: str = "#0284c7") -> QIcon:
    """Create navigation icons with clean geometric shapes."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    qcolor = QColor(color)
    pen = QPen(
        qcolor, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin
    )
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    if symbol_type == "download":
        # Arrow down into tray
        painter.drawLine(QPointF(size * 0.5, size * 0.2), QPointF(size * 0.5, size * 0.6))
        # Arrowhead
        painter.drawLine(QPointF(size * 0.32, size * 0.44), QPointF(size * 0.5, size * 0.62))
        painter.drawLine(QPointF(size * 0.68, size * 0.44), QPointF(size * 0.5, size * 0.62))
        # Tray base
        tray_path = QPainterPath()
        tray_path.moveTo(size * 0.2, size * 0.66)
        tray_path.lineTo(size * 0.2, size * 0.82)
        tray_path.lineTo(size * 0.8, size * 0.82)
        tray_path.lineTo(size * 0.8, size * 0.66)
        painter.drawPath(tray_path)

    elif symbol_type == "queue":
        # Three horizontal lines / list
        painter.drawLine(QPointF(size * 0.22, size * 0.30), QPointF(size * 0.78, size * 0.30))
        painter.drawLine(QPointF(size * 0.22, size * 0.50), QPointF(size * 0.78, size * 0.50))
        painter.drawLine(QPointF(size * 0.22, size * 0.70), QPointF(size * 0.78, size * 0.70))

    elif symbol_type == "history":
        # Clock face
        painter.drawEllipse(QRectF(size * 0.18, size * 0.18, size * 0.64, size * 0.64))
        # Clock hands
        painter.drawLine(QPointF(size * 0.5, size * 0.32), QPointF(size * 0.5, size * 0.5))
        painter.drawLine(QPointF(size * 0.5, size * 0.5), QPointF(size * 0.66, size * 0.5))

    elif symbol_type == "settings":
        # Gear / sliders
        painter.drawEllipse(QRectF(size * 0.32, size * 0.32, size * 0.36, size * 0.36))
        # Outer ticks
        painter.drawLine(QPointF(size * 0.5, size * 0.16), QPointF(size * 0.5, size * 0.28))
        painter.drawLine(QPointF(size * 0.5, size * 0.72), QPointF(size * 0.5, size * 0.84))
        painter.drawLine(QPointF(size * 0.16, size * 0.5), QPointF(size * 0.28, size * 0.5))
        painter.drawLine(QPointF(size * 0.72, size * 0.5), QPointF(size * 0.84, size * 0.5))

    elif symbol_type == "about":
        # Circle with info "i"
        painter.drawEllipse(QRectF(size * 0.18, size * 0.18, size * 0.64, size * 0.64))
        # Dot
        painter.setBrush(QBrush(qcolor))
        painter.drawEllipse(QRectF(size * 0.46, size * 0.30, size * 0.08, size * 0.08))
        # Stem
        painter.drawLine(QPointF(size * 0.5, size * 0.44), QPointF(size * 0.5, size * 0.68))

    painter.end()
    return QIcon(pixmap)
