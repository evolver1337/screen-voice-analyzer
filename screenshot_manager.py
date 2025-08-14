import logging
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPixmap, QGuiApplication
from ocr_analyzer import CodeAnalyzer


class ScreenshotManager(QObject):
    screenshot_taken = pyqtSignal(QPixmap)
    text_extracted = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.selected_region = None
        self.code_analyzer = CodeAnalyzer()
        logging.info("Screenshot manager initialized")

    def set_region(self, region):
        """Установка области для захвата"""
        self.selected_region = region
        logging.info(f"Region set: {region}")

    def capture_and_analyze(self):
        """Захват экрана и анализ кода"""
        if not self.selected_region:
            self.error_occurred.emit("Не выбрана область для захвата")
            logging.error("Сначала выберите область для захвата")
            return

        try:
            x, y, w, h = self.selected_region
            screen = QGuiApplication.primaryScreen()

            if not screen:
                raise RuntimeError("Экран не найден")

            screenshot: QPixmap = screen.grabWindow(0, x, y, w, h)

            if screenshot.isNull():
                raise ValueError("Не удалось сделать скриншот")

            self.screenshot_taken.emit(screenshot)

            # ➤ Передаём изображение в CodeAnalyzer
            text = self.code_analyzer.analyze_image(screenshot)

            if not text.strip():
                raise ValueError("Не удалось распознать текст")

            self.text_extracted.emit(text)
            logging.info("Screenshot captured and analyzed")

        except Exception as e:
            self.error_occurred.emit(str(e))
            logging.error(f"Screenshot error: {e}")

    def cleanup(self):
        """Очистка ресурсов"""
        logging.info("Screenshot manager cleaned up")
