import os
import sys
from PyQt6.QtWidgets import QApplication
from dotenv import load_dotenv
from gui_app import MainWindow
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Проверка пути к .env перед загрузкой
def load_environment():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    print(f"Пытаюсь загрузить .env по пути: {env_path}")  # Для отладки

    if not os.path.exists(env_path):
        print("❌ Файл .env не найден! Создайте его в корне проекта")
        print(f"Текущая рабочая директория: {os.getcwd()}")
        return False

    load_dotenv(env_path)


if __name__ == "__main__":
    load_environment()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())