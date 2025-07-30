import numpy as np
import webrtcvad


class SpeechDetector:
    def __init__(self, aggressiveness=3):
        self.vad = webrtcvad.Vad(aggressiveness)

    def is_speech(self, audio_chunk):
        audio_int16 = (audio_chunk * 32767).astype(np.int16)
        return self.vad.is_speech(
            audio_int16.tobytes(),
            sample_rate=16000,
            length=len(audio_chunk)
        )