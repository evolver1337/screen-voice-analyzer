import sys
from PyQt6.QtCore import Qt, QRect, QPoint, QSize, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication, QWidget, QRubberBand


class ScreenSelectionOverlay(QWidget):
    selection_made = pyqtSignal(QRect)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen_geometry)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 120);")

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
            print(f"Selection made: {rect}")
            self.selection_made.emit(rect)
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    overlay = ScreenSelectionOverlay()

    def on_selection(rect):
        print(f"Selected area: {rect}")
        app.quit()

    overlay.selection_made.connect(on_selection)
    overlay.show()
    overlay.raise_()
    overlay.activateWindow()
    sys.exit(app.exec())
