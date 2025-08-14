from PyQt6.QtCore import QObject, pyqtSignal
import numpy as np
import logging

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
        self.audio_buffer = []  # сюда складываем аудио чанки от AudioSystem

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
        if audio_data is None or len(audio_data) == 0:
            logging.error("Получены некорректные аудиоданные: None или пустой массив")
            self.error_occurred.emit("Ошибка: пустые аудиоданные")
            return
        self.audio_buffer.append(audio_data)
        logging.info(f"Received audio chunk, length={len(audio_data)}")

    def _on_silence_timeout(self, session_id):
        logging.info(f"Silence timeout received, starting recognition. Chunks in buffer: {len(self.audio_buffer)}")
        if not self.audio_buffer:
            return

        # Собираем весь накопленный буфер в один массив
        full_audio = np.concatenate(self.audio_buffer)
        self.audio_buffer.clear()

        try:
            text = self.recognizer.recognize_audio(full_audio)
            if text:
                self.current_text = text.strip()
                self.text_ready.emit(self.current_text)
                logging.info(f"Recognized full text: {self.current_text}")
        except Exception as e:
            self.error_occurred.emit(f"Recognition error: {e}")
            logging.error(f"Recognition error: {e}")

    def cleanup(self):
        self.audio.cleanup()
