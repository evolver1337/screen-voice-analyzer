import pytesseract
from PIL import ImageGrab

class CodeAnalyzer:
    @staticmethod
    def capture_and_analyze(region):
        screenshot = ImageGrab.grab(bbox=region)
        code_text = pytesseract.image_to_string(screenshot)
        return code_text