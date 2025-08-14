from PyQt6.QtCore import Qt, QRect, QPoint, QSize, pyqtSignal
from PyQt6.QtGui import QGuiApplication, QKeyEvent
from PyQt6.QtWidgets import QWidget, QRubberBand


class ScreenSelectionOverlay(QWidget):
    selection_made = pyqtSignal(QRect)

    def __init__(self):
        super().__init__()

        # Настройка окна — без рамок, поверх всех окон, с прозрачным фоном
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool  # чтобы не появлялся в таскбаре
        )
        screen_geom = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen_geom)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: rgba(0, 0, 0, 100);")  # затемнённый фон

        self.origin = QPoint()
        self.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.rubber_band.hide()

    def mousePressEvent(self, event):
        self.origin = event.pos()
        self.rubber_band.setGeometry(QRect(self.origin, QSize()))
        self.rubber_band.show()

    def mouseMoveEvent(self, event):
        if self.rubber_band.isVisible():
            rect = QRect(self.origin, event.pos()).normalized()
            self.rubber_band.setGeometry(rect)

    def mouseReleaseEvent(self, event):
        if self.rubber_band.isVisible():
            self.rubber_band.hide()
            rect = QRect(self.origin, event.pos()).normalized()

            # Если выделение пустое, подставляем весь экран
            if rect.isNull() or rect.isEmpty():
                rect = QGuiApplication.primaryScreen().geometry()

            self.selection_made.emit(rect)
            self.close()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            # Закрыть оверлей без выбора (null rect)
            self.selection_made.emit(QRect())  # пустой QRect
            self.close()
        else:
            super().keyPressEvent(event)

    def select_full_screen_and_close(self):
        """Программно выбрать весь экран и закрыть оверлей"""
        rect = QGuiApplication.primaryScreen().geometry()
        self.selection_made.emit(rect)
        self.close()
