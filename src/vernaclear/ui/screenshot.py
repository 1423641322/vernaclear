from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QKeyEvent, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QWidget

from vernaclear.core.i18n import normalize_ui_language, tr
from vernaclear.core.paths import data_dir


class ScreenSnipOverlay(QWidget):
    captured = Signal(str)
    cancelled = Signal()
    failed = Signal(str)

    def __init__(self, language: str = "zh") -> None:
        super().__init__(None)
        self.locale = normalize_ui_language(language)
        self._origin = QPoint()
        self._current = QPoint()
        self._selecting = False
        self._screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        if self._screen is None:
            raise RuntimeError(tr(self.locale, "no_screen"))
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setGeometry(self._screen.geometry())

    @property
    def selection(self) -> QRect:
        return QRect(self._origin, self._current).normalized()

    def start(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(7, 10, 16, 176))
        rect = self.selection
        if not rect.isNull() and rect.width() > 1 and rect.height() > 1:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor("#8B83FF"), 2))
            painter.drawRect(rect)
            label = f" {rect.width()} × {rect.height()}  {tr(self.locale, 'snip_release')} "
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#171B25"))
            label_rect = QRect(rect.left(), max(8, rect.top() - 34), 260, 28)
            painter.drawRoundedRect(label_rect, 6, 6)
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, label)
        else:
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(
                self.rect(), Qt.AlignmentFlag.AlignCenter, tr(self.locale, "snip_drag")
            )

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.position().toPoint()
            self._current = self._origin
            self._selecting = True
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._selecting:
            self._current = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton or not self._selecting:
            return
        self._current = event.position().toPoint()
        self._selecting = False
        rect = self.selection.intersected(self.rect())
        if rect.width() < 8 or rect.height() < 8:
            self.update()
            return
        self.hide()
        QTimer.singleShot(180, lambda: self._capture(rect))

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            self.cancelled.emit()
            return
        super().keyPressEvent(event)

    def _capture(self, rect: QRect) -> None:
        try:
            pixmap = self._screen.grabWindow(0, rect.x(), rect.y(), rect.width(), rect.height())
            if pixmap.isNull():
                raise RuntimeError(tr(self.locale, "capture_failed"))
            output = data_dir() / "last-capture.png"
            if not pixmap.save(str(output), "PNG"):
                raise RuntimeError(tr(self.locale, "capture_save_failed"))
            self.captured.emit(str(output))
        except Exception as error:
            self.failed.emit(str(error))
        finally:
            self.close()

