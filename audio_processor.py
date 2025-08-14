from PyQt6.QtCore import QThread, pyqtSignal, QObject, QTimer, QMetaObject, Qt
import numpy as np
import sounddevice as sd
from queue import Queue
import logging
from datetime import datetime

from speech_analyzer import SpeechDetector
from speech_recognizer import WhisperRecognizer


class AudioProcessor(QThread):
    finished = pyqtSignal(str, str)  # text, session_id

    def __init__(self, audio_queue, recognizer):
        super().__init__()
        self.queue = audio_queue
        self.recognizer = recognizer
        self.session_id = None

    def run(self):
        while True:
            data = self.queue.get()
            if data is None:
                break

            audio_data, self.session_id = data
            text = self.recognizer.recognize_audio(audio_data)
            if text:
                self.finished.emit(text, self.session_id)


from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QMetaObject, Qt
import numpy as np
import logging
from datetime import datetime
import sounddevice as sd

from speech_analyzer import SpeechDetector  # твой VAD
from speech_recognizer import WhisperRecognizer  # твой распознаватель


class AudioSystem(QObject):
    audio_data_ready = pyqtSignal(np.ndarray)  # весь буфер после тишины
    status_changed = pyqtSignal(str, str)  # статус, session_id
    silence_timeout = pyqtSignal(str)  # session_id

    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.stream = None
        self.sample_rate = 16000
        self.buffer = []
        self.current_session = None

        self.silence_timer = QTimer()
        self.silence_timer.setInterval(3000)  # 3 секунды тишины
        self.silence_timer.setSingleShot(True)
        self.silence_timer.timeout.connect(self._on_silence_timeout)

        self.logger = logging.getLogger("AUDIO")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler("audio_sessions.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.logger.addHandler(handler)

        self.speech_detector = SpeechDetector()

        self.last_speech_detected = False

    def audio_callback(self, indata, frames, time, status):
        if status:
            self.logger.warning(f"Session {self.current_session} - Audio status: {status}")

        audio_int16 = indata.flatten()

        is_speech = False
        frame_size = 480
        num_frames = len(audio_int16) // frame_size

        for i in range(num_frames):
            frame = audio_int16[i * frame_size:(i + 1) * frame_size]
            try:
                if self.speech_detector.vad.is_speech(frame.tobytes(), sample_rate=self.sample_rate):
                    is_speech = True
                    break
            except Exception as e:
                self.logger.error(f"Speech detection error: {e}")

        if is_speech:
            if not self.last_speech_detected:
                self.logger.info(f"Session {self.current_session} - Speech detected")
            self.last_speech_detected = True
            QMetaObject.invokeMethod(self.silence_timer, "stop", Qt.ConnectionType.QueuedConnection)
        else:
            if self.last_speech_detected:
                QMetaObject.invokeMethod(self.silence_timer, "start", Qt.ConnectionType.QueuedConnection)
            self.last_speech_detected = False

        # Добавляем в буфер каждый вызов audio_callback (минимальные блоки ~30ms)
        self.buffer.append(indata.copy())

    def _on_silence_timeout(self):
        if not self.buffer:
            return
        audio_chunk = np.concatenate(self.buffer)
        self.buffer.clear()

        self.logger.info(f"Session {self.current_session} - Silence timeout reached, emitting full audio chunk")
        self.audio_data_ready.emit(audio_chunk)
        self.silence_timeout.emit(self.current_session)

    def start_recording(self):
        if self.is_recording:
            return
        self.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.is_recording = True

        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='int16',
            callback=self.audio_callback,
            blocksize=480  # примерно 30 мс
        )
        self.stream.start()

        self.status_changed.emit(f"STARTED Session {self.current_session}", self.current_session)
        self.logger.info(f"STARTED Session {self.current_session}")

    def stop_recording(self):
        if not self.is_recording:
            return

        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        # Если что-то осталось в буфере — обработать и отправить
        if self.buffer:
            audio_chunk = np.concatenate(self.buffer)
            self.buffer.clear()
            self.audio_data_ready.emit(audio_chunk)
            self.logger.info(f"Session {self.current_session} - Final audio chunk emitted on stop")

        self.status_changed.emit(f"STOPPED Session {self.current_session}", self.current_session)
        self.logger.info(f"STOPPED Session {self.current_session}")

        self.current_session = None
        QMetaObject.invokeMethod(self.silence_timer, "stop", Qt.ConnectionType.QueuedConnection)

    def cleanup(self):
        self.stop_recording()
        self.logger.info("Audio system cleaned up")
