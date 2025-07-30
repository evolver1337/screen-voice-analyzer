from PyQt6.QtCore import QThread, pyqtSignal, QObject
import numpy as np
import sounddevice as sd
from queue import Queue
import logging
from datetime import datetime
from speech_recognizer import WhisperRecognizer


class AudioProcessor(QThread):
    finished = pyqtSignal(str, str)  # text, session_id

    def __init__(self, audio_queue, model_size="small"):
        super().__init__()
        self.queue = audio_queue
        self.recognizer = WhisperRecognizer(model_size)
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


class AudioSystem(QObject):
    text_ready = pyqtSignal(str, str)  # text, session_id
    status_changed = pyqtSignal(str, str)  # status, session_id

    def __init__(self, model_size="small"):
        super().__init__()
        self.is_recording = False
        self.stream = None
        self.audio_queue = Queue(maxsize=3)
        self.sample_rate = 16000
        self.buffer = []
        self.processors = []
        self.current_session = None
        self._init_processors(model_size)

        # Настройка логгера
        self.logger = logging.getLogger("AUDIO")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler("audio_sessions.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.logger.addHandler(handler)

    def _init_processors(self, model_size):
        for i in range(2):
            processor = AudioProcessor(self.audio_queue, model_size)
            processor.finished.connect(self.text_ready.emit)
            processor.start()
            self.processors.append(processor)

    def _new_session_id(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def audio_callback(self, indata, frames, time, status):
        if status:
            self.logger.warning(f"Session {self.current_session} - Audio status: {status}")

        self.buffer.append(indata.copy())
        if len(self.buffer) >= self.sample_rate * 3:  # 3 секунды
            self._process_buffer()

    def _process_buffer(self):
        audio_chunk = np.concatenate(self.buffer)
        self.buffer = []
        try:
            self.audio_queue.put_nowait((audio_chunk, self.current_session))
            self.logger.info(f"Session {self.current_session} - Audio chunk queued")
        except:
            self.logger.warning(f"Session {self.current_session} - Queue full, chunk dropped")

    def start_recording(self):
        if self.is_recording:
            return

        self.current_session = self._new_session_id()
        self.is_recording = True

        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='int16',
            callback=self.audio_callback,
            blocksize=self.sample_rate
        )
        self.stream.start()

        start_msg = f"STARTED Session {self.current_session}"
        self.status_changed.emit(start_msg, self.current_session)
        self.logger.info(start_msg)

    def stop_recording(self):
        if not self.is_recording:
            return

        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()

        if self.buffer:
            self._process_buffer()

        stop_msg = f"STOPPED Session {self.current_session}"
        self.status_changed.emit(stop_msg, self.current_session)
        self.logger.info(stop_msg)
        self.current_session = None

    def cleanup(self):
        self.stop_recording()
        for _ in self.processors:
            self.audio_queue.put(None)
        for p in self.processors:
            p.wait(3000)
        self.logger.info("Service shutdown")