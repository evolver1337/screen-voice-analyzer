import os
import sys
import requests
from PyQt6.QtCore import QSize, QPoint
from PyQt6.QtWidgets import (
    QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QTextEdit, QComboBox, QProgressBar, QLabel,
    QHBoxLayout, QGroupBox, QLineEdit, QRubberBand,
    QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QRect
from PyQt6.QtGui import QTextCursor

from api_client import APIWorker
from audio_processor import AudioSystem
from ocr_analyzer import CodeAnalyzer


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Инициализация систем
        self.audio = AudioSystem()
        self.current_mode = "system"  # system/microphone/off
        self.api_worker = None
        self.selected_region = None

        # Настройка интерфейса
        self.setMouseTracking(True)
        self.origin = QPoint()
        self.setup_ui()
        self.setup_styles()
        self.setWindowTitle("AI Code Analyzer Pro")
        self.setMinimumSize(1000, 800)

    def setup_ui(self):
        """Инициализация основного интерфейса"""
        self.setup_main_widgets()
        self.setup_tool_panel()
        self.setup_rubber_band()
        self.setup_layout()

    def setup_main_widgets(self):
        """Создание основных виджетов"""
        self.response_area = QTextEdit()
        self.response_area.setReadOnly(False)
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Введите вопрос...")
        self.progress_bar = QProgressBar()
        self.status_label = QLabel("🔴 Ожидание действий")

    def setup_tool_panel(self):
        """Панель инструментов"""
        self.tool_group = QGroupBox("Инструменты")

        # Виджеты
        self.api_selector = QComboBox()
        self.api_selector.addItems(["Cody" ,"DeepSeek", "OpenAI"])

        self.audio_mode = QComboBox()
        self.audio_mode.addItems(["Системный звук", "Микрофон", "Выключено"])
        self.audio_mode.setCurrentIndex(0)  # По умолчанию "Системный звук"

        self.btn_select_area = QPushButton("🖱️ Выбрать область")
        self.btn_select_area.setCheckable(True)
        self.btn_analyze = QPushButton("📸 Анализ кода")
        self.btn_ask = QPushButton("❓ Задать вопрос")
        self.btn_clear = QPushButton("🧹 Очистить")
        self.btn_audio_toggle = QPushButton("🎤 Включить аудио")

        # Компоновка
        tool_layout = QHBoxLayout()
        tool_layout.addWidget(QLabel("API:"))
        tool_layout.addWidget(self.api_selector)
        tool_layout.addWidget(QLabel("Режим:"))
        tool_layout.addWidget(self.audio_mode)
        tool_layout.addWidget(self.btn_select_area)
        tool_layout.addWidget(self.btn_analyze)
        tool_layout.addWidget(self.btn_ask)
        tool_layout.addWidget(self.btn_clear)
        tool_layout.addWidget(self.btn_audio_toggle)
        self.tool_group.setLayout(tool_layout)

        # Сигналы
        self.btn_select_area.clicked.connect(self.toggle_area_selection)
        self.btn_analyze.clicked.connect(self.analyze_code)
        self.btn_ask.clicked.connect(self.ask_question)
        self.btn_clear.clicked.connect(self.clear_output)
        self.btn_audio_toggle.clicked.connect(self.toggle_audio_analysis)
        self.audio_mode.currentIndexChanged.connect(self.change_audio_mode)
        self.question_input.returnPressed.connect(self.ask_question)

    def setup_rubber_band(self):
        """Настройка резиновой полосы для выделения области"""
        self.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.rubber_band.setStyleSheet("""
            QRubberBand {
                border: 2px dashed #0078d7;
                background-color: rgba(0, 120, 215, 20%);
            }
        """)

    def setup_layout(self):
        """Главная компоновка"""
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tool_group)
        main_layout.addWidget(self.response_area)
        main_layout.addWidget(self.question_input)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def setup_styles(self):
        """Стилизация приложения"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f7fa;
                font-family: 'Segoe UI', Arial;
            }
            QGroupBox {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Consolas';
            }
            QPushButton {
                padding: 8px 12px;
                border-radius: 6px;
                min-width: 100px;
                background-color: #e5e7eb;
            }
            QPushButton:hover {
                background-color: #d1d5db;
            }
            QProgressBar {
                height: 12px;
                border-radius: 6px;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 6px;
            }
        """)

    # --- Функционал выделения области ---
    def toggle_area_selection(self, checked):
        """Переключение режима выделения области"""
        self.setCursor(Qt.CursorShape.CrossCursor if checked else Qt.CursorShape.ArrowCursor)
        self.btn_select_area.setText("🚫 Отменить" if checked else "🖱️ Выбрать область")

        if checked:
            self.rubber_band.show() if hasattr(self, 'origin') else self.rubber_band.hide()
        else:
            self.rubber_band.hide()

    def mousePressEvent(self, event):
        """Обработка нажатия кнопки мыши"""
        if self.btn_select_area.isChecked() and event.button() == Qt.MouseButton.LeftButton:
            self.origin = event.pos()  # Фиксируем начальную позицию
            self.rubber_band.setGeometry(QRect(self.origin, QSize()))
            self.rubber_band.show()
            event.accept()  # Явно принимаем событие
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Обработка движения мыши"""
        if self.btn_select_area.isChecked() and self.rubber_band.isVisible():
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Обработка отпускания кнопки мыши"""
        if self.btn_select_area.isChecked() and self.rubber_band.isVisible():
            rect = self.rubber_band.geometry()
            if rect.width() > 10 and rect.height() > 10:
                # Конвертируем координаты относительно экрана
                screen_rect = QRect(
                    self.mapToGlobal(rect.topLeft()),
                    self.mapToGlobal(rect.bottomRight())
                )
                self.selected_region = (
                    screen_rect.x(),
                    screen_rect.y(),
                    screen_rect.width(),
                    screen_rect.height()
                )
                self.status_label.setText(f"✅ Область: {rect.width()}x{rect.height()} пикс.")

            self.rubber_band.hide()
            self.btn_select_area.setChecked(False)
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    # --- Основной функционал ---
    def analyze_code(self):
        """Анализ кода в выделенной области"""
        if not self.selected_region:
            self.status_label.setText("❌ Сначала выберите область!")
            return

        try:
            x, y, w, h = self.selected_region
            self.start_processing("🟡 Захват экрана...")

            # Получение кода через OCR
            code_text = CodeAnalyzer.capture_and_analyze(region=(x, y, x + w, y + h))
            self.response_area.append(f"🔍 Код:\n```\n{code_text}\n```\n")

            # Отправка на анализ в ИИ
            self.ask_ai(f"Проанализируй этот код:\n```\n{code_text}\n```")

        except Exception as e:
            self.handle_error(str(e))

    def ask_question(self):
        """Обработка вопроса пользователя"""
        question = self.question_input.text().strip()
        if not question:
            return

        self.question_input.clear()
        self.start_processing("🟡 Обработка вопроса...")
        self.ask_ai(question)

    def ask_ai(self, prompt):
        """Отправка запроса к API ИИ"""
        self.api_worker = APIWorker(
            api_name=self.api_selector.currentText(),
            prompt=prompt
        )
        self.api_worker.finished.connect(self.handle_response)
        self.api_worker.error.connect(self.handle_error)
        self.api_worker.progress.connect(self.update_progress)
        self.api_worker.start()

    # --- Аудио функционал ---
    def change_audio_mode(self, index):
        """Изменение режима аудио (system/microphone/off)"""
        self.current_mode = ["system", "microphone", "off"][index]

    def toggle_audio_analysis(self):
        """Включение/выключение аудиоанализа"""
        if self.btn_audio_toggle.text().startswith("🎤"):
            self.start_audio_listening()
            self.btn_audio_toggle.setText("⏹ Остановить аудио")
            self.btn_audio_toggle.setStyleSheet("background-color: #ffcccc;")
        else:
            self.stop_audio_listening()
            self.btn_audio_toggle.setText("🎤 Включить аудио")
            self.btn_audio_toggle.setStyleSheet("")

    def start_audio_listening(self):
        """Запуск аудиозаписи в выбранном режиме"""
        try:
            if self.current_mode == "system":
                self.audio.start_system_recording()
            elif self.current_mode == "microphone":
                self.audio.start_microphone_recording()
            self.status_label.setText("🟢 Аудиоанализ активен")
        except Exception as e:
            self.handle_error(str(e))

    def stop_audio_listening(self):
        """Остановка аудиозаписи"""
        self.audio.stop_recording()
        self.status_label.setText("🔴 Аудиоанализ остановлен")

    # --- Вспомогательные методы ---
    def start_processing(self, message):
        """Начало длительной операции"""
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText(message)

    def handle_response(self, response):
        """Обработка ответа от API"""
        self.response_area.append(f"🤖 Ответ:\n{response}\n{'=' * 50}\n")
        self.scroll_to_bottom()
        self.progress_bar.setVisible(False)
        self.status_label.setText("🟢 Готово")

    def handle_error(self, error_msg):
        """Обработка ошибок"""
        self.response_area.append(f"❌ Ошибка: {error_msg}\n")
        self.scroll_to_bottom()
        self.progress_bar.setVisible(False)
        self.status_label.setText("🔴 Ошибка")

    def clear_output(self):
        """Очистка поля вывода"""
        self.response_area.clear()
        self.status_label.setText("🔴 Ожидание действий")

    def scroll_to_bottom(self):
        """Прокрутка в конец текста"""
        cursor = self.response_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.response_area.setTextCursor(cursor)

    def update_progress(self, value):
        """Обновление прогресс-бара"""
        self.progress_bar.setValue(value)
        if value < 30:
            self.status_label.setText("🟡 Подготовка данных...")
        elif value < 70:
            self.status_label.setText(f"🟡 Запрос к {self.api_selector.currentText()}...")
        else:
            self.status_label.setText("🟡 Обработка ответа...")

    def closeEvent(self, event):
        """Действия при закрытии окна"""
        self.stop_audio_listening()
        if self.api_worker and self.api_worker.isRunning():
            self.api_worker.terminate()
        event.accept()
