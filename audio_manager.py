import logging
from PyQt6.QtCore import QObject, pyqtSignal  # Ваш существующий класс

from audio_processor import AudioSystem


class AudioManager(QObject):
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.audio = AudioSystem()
        self.current_mode = "system"
        self.is_recording = False

    def set_mode(self, mode_index):
        """Установка режима работы (0-system, 1-microphone, 2-off)"""
        modes = ["system", "microphone", "off"]
        self.current_mode = modes[mode_index]
        logging.info(f"Audio mode changed to: {self.current_mode}")

    def toggle_recording(self):
        """Переключение состояния записи"""
        if self.is_recording:
            self.stop()
        else:
            self.start()

    def start(self):
        """Запуск записи"""
        try:
            if self.current_mode == "system":
                self.audio.start_recording()
            else:
                return

            self.is_recording = True
            self.status_changed.emit("🟢 Аудиоанализ активен")
            logging.info("Audio recording started")

        except Exception as e:
            self.error_occurred.emit(str(e))
            logging.error(f"Audio start error: {e}")

    def stop(self):
        """Остановка записи"""
        self.audio.stop_recording()
        self.is_recording = False
        self.status_changed.emit("🔴 Аудиоанализ остановлен")
        logging.info("Audio recording stopped")

    def cleanup(self):
        """Очистка ресурсов"""
        if self.is_recording:
            self.stop()
        logging.info("Audio manager cleaned up")