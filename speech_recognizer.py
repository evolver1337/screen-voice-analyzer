from faster_whisper import WhisperModel
from PyQt6.QtCore import QObject, pyqtSignal
import numpy as np
import os
import logging


class WhisperRecognizer(QObject):
    text_recognized = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, model_size="small"):
        super().__init__()
        self.model = None
        self.model_size = model_size
        self._init_model()

    def _init_model(self):
        try:
            model_dir = os.path.join("whisper_models", self.model_size)
            os.makedirs(model_dir, exist_ok=True)

            self.model = WhisperModel(
                model_size_or_path=self.model_size,
                device="cpu",
                compute_type="int8",
                download_root=model_dir,
                local_files_only=False
            )
            logging.info(f"Loaded Whisper model: {self.model_size}")
        except Exception as e:
            logging.error(f"Failed to load model: {str(e)}")
            self.error_occurred.emit(f"Model load error: {str(e)}")

    def recognize_audio(self, audio_data: np.ndarray, sample_rate: int = 16000):
        if self.model is None:
            self.error_occurred.emit("Model not loaded")
            return ""

        try:
            audio = self._prepare_audio(audio_data, sample_rate)
            segments, _ = self.model.transcribe(
                audio,
                language="ru",
                beam_size=5,
                vad_filter=True
            )
            return " ".join(segment.text for segment in segments)
        except Exception as e:
            self.error_occurred.emit(f"Recognition error: {str(e)}")
            return ""

    @staticmethod
    def _prepare_audio(audio_data: np.ndarray, sample_rate: int):
        audio = audio_data.astype(np.float32) / 32768.0
        return np.mean(audio, axis=1) if audio.ndim > 1 else audio