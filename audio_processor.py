import sounddevice as sd
import numpy as np
from speech_analyzer import SpeechDetector


class AudioSystem:
    def __init__(self):
        self.is_recording = False
        self.stream = None

    def start_system_recording(self):
        """Захват системного звука через виртуальный кабель"""
        self.is_recording = True
        self.stream = sd.InputStream(
            device=self.get_system_device_id(),
            callback=self.audio_callback
        )
        self.stream.start()

    def start_microphone_recording(self):
        """Захват с микрофона"""
        self.is_recording = True
        self.stream = sd.InputStream(
            device=self.get_microphone_device_id(),
            callback=self.audio_callback
        )
        self.stream.start()

    def stop_recording(self):
        """Остановка записи"""
        if self.stream:
            self.stream.stop()
            self.stream.close()
        self.is_recording = False

    def get_system_device_id(self):
        """Найти ID виртуального аудиоустройства"""
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if "CABLE Output" in dev['name']:  # Для VB-Cable на Windows
                return i
            if "BlackHole" in dev['name']:    # Для macOS
                return i
        return 0  # Fallback

    def get_microphone_device_id(self):
        """Найти ID микрофона"""
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                return i
        return 0  # Fallback