from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import logging
import numpy as np

from audio_processor import AudioSystem
from speech_recognizer import WhisperRecognizer


class AudioManager(QObject):
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    text_ready = pyqtSignal(str)  # Готовый распознанный текст

    def __init__(self):
        super().__init__()
        self.audio = AudioSystem()
        self.audio.audio_data_ready.connect(self._on_audio_data_ready)
        self.audio.silence_timeout.connect(self._on_silence_timeout)

        self.recognizer = WhisperRecognizer()

        self.current_text = ""
        self.is_recording = False
        self.current_mode = "system"

    def set_mode(self, mode_index):
        modes = ["system", "microphone", "off"]
        self.current_mode = modes[mode_index]
        logging.info(f"Audio mode changed to: {self.current_mode}")

    def toggle_recording(self):
        if self.is_recording:
            self.stop()
        else:
            self.start()

    def start(self):
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
        self.audio.stop_recording()
        self.is_recording = False
        self.status_changed.emit("🔴 Аудиоанализ остановлен")
        logging.info("Audio recording stopped")

    def _on_audio_data_ready(self, audio_data: np.ndarray):
        try:
            text = self.recognizer.recognize_audio(audio_data)
            if text:
                self.current_text += " " + text
                logging.info(f"Recognized partial text: {text}")
        except Exception as e:
            self.error_occurred.emit(f"Recognition error: {e}")
            logging.error(f"Recognition error: {e}")

    def _on_silence_timeout(self, session_id):
        # Таймаут тишины — значит закончился фрагмент речи
        if self.current_text.strip():
            self.text_ready.emit(self.current_text.strip())
            logging.info(
                f"Final text emitted for session {session_id}: {self.current_text.strip()}")
            self.current_text = ""

    def cleanup(self):
        self.audio.cleanup()
