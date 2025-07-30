import os
import requests
from PyQt6.QtCore import QThread, pyqtSignal
from dotenv import load_dotenv

load_dotenv()

import os
from PyQt6.QtCore import QObject, pyqtSignal


class APIClient(QObject):
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    progress_updated = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.current_worker = None

    def send_request(self, api_name: str, prompt: str):
        """Отправка запроса через APIWorker"""
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.terminate()

        self.current_worker = APIWorker(api_name, prompt)
        self.current_worker.finished.connect(self._handle_response)
        self.current_worker.error.connect(self._handle_error)
        self.current_worker.progress.connect(self._handle_progress)
        self.current_worker.start()

    def cancel_current(self):
        """Отмена текущего запроса"""
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.terminate()

    def _handle_response(self, response: str):
        """Обработка успешного ответа"""
        self.response_received.emit(response)

    def _handle_error(self, error: str):
        """Обработка ошибки"""
        self.error_occurred.emit(error)

    def _handle_progress(self, value: int):
        """Обновление прогресса"""
        self.progress_updated.emit(value)

class APIWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, api_name: str, prompt: str, parent=None):
        super().__init__(parent)
        self.api_name = api_name.lower()
        self.prompt = prompt

    def run(self):
        try:
            self.progress.emit(10)
            api_key = self._get_api_key()
            if not api_key:
                raise Exception(f"API ключ для {self.api_name} не найден")

            response = self.call_api(api_key)
            self.progress.emit(100)
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))

    def _get_api_key(self):
        if self.api_name == "deepseek":
            return os.getenv("DEEPSEEK_API_KEY")
        elif self.api_name == "openai":
            return os.getenv("OPENAI_API_KEY")
        elif self.api_name == "cody":
            return os.getenv("CODY_API_KEY")
        return None

    def call_api(self, api_key: str) -> str:
        """Маршрутизация запросов к разным API"""
        if self.api_name == "deepseek":
            return self._call_deepseek_api(api_key)
        elif self.api_name == "openai":
            return self._call_openai_api(api_key)
        elif self.api_name == "cody":
            return self._call_cody_api(api_key)
        raise ValueError(f"Неподдерживаемый API: {self.api_name}")

    def _call_deepseek_api(self, api_key: str) -> str:
        """Реализация DeepSeek API"""
        self.progress.emit(20)
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": self.prompt}],
            "temperature": 0.7
        }
        self.progress.emit(40)
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        self.progress.emit(80)
        return response.json()["choices"][0]["message"]["content"]

    def _call_cody_api(self, api_key: str) -> str:
        """Реализация запросов к Cody API"""
        self.progress.emit(20)
        url = "https://cody.su/api/v1"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4.1",
            "messages": [{"role": "user", "content": self.prompt}],
            "temperature": 0.7
        }
        self.progress.emit(40)
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        self.progress.emit(80)
        return response.json()["choices"][0]["message"]["content"]

    def _call_openai_api(self, api_key: str) -> str:
        """Реализация OpenAI API"""
        self.progress.emit(20)
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": self.prompt}],
            "temperature": 0.7
        }
        self.progress.emit(40)
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        self.progress.emit(80)
        return response.json()["choices"][0]["message"]["content"]