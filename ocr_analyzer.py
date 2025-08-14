import logging
import io
from PIL import Image
from PyQt6.QtGui import QPixmap
import pytesseract


class CodeAnalyzer:
    def analyze_image(self, pixmap: QPixmap) -> str:
        """Анализ изображения и извлечение текста"""
        try:
            image = self.qpixmap_to_pil(pixmap)
            text = pytesseract.image_to_string(image, lang="eng")
            logging.info("Image analyzed successfully")
            return text
        except Exception as e:
            logging.error(f"Image analysis failed: {e}")
            return ""

    @staticmethod
    def qpixmap_to_pil(pixmap: QPixmap) -> Image.Image:
        """Преобразование QPixmap в PIL.Image"""
        from PyQt6.QtCore import QByteArray, QBuffer, QIODevice

        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        pixmap.save(buffer, "PNG")
        buffer.close()
        return Image.open(io.BytesIO(byte_array.data()))
