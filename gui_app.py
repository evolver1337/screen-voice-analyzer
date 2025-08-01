import logging

from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QTextEdit, QPushButton, QComboBox, QProgressBar,
    QLabel, QGroupBox, QLineEdit, QListWidget, QRubberBand, QSizePolicy
)
from markdown import markdown
from markdown.extensions.codehilite import CodeHiliteExtension

from api_client import APIWorker, APIClient  # Ваш реальный клиент API
from audio_manager import AudioManager
from history_manager import HistoryManager
from screenshot_manager import ScreenshotManager
from speech_recognizer import WhisperRecognizer
from text_formatter import TextFormatter, MarkdownHighlighter


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.whisper = WhisperRecognizer()
        self._init_managers()
        self.audio_manager.text_ready.connect(self._on_audio_text_ready)
        self._setup_ui()
        self._connect_signals()
        self._setup_styles()
        self._init_rubber_band()
        self.audio_manager.audio.audio_data_ready.connect(self._process_audio_data)
        self.whisper.text_recognized.connect(self._on_audio_text_ready)
        self.whisper.error_occurred.connect(self._handle_error)
        self.history = []
        logging.info("Application initialized")

    def _process_audio_data(self, audio_data):
        try:
            text = self.whisper.recognize_audio(audio_data)
            if text:
                self.whisper.text_recognized.emit(text)
        except Exception as e:
            self._handle_error(f"Ошибка распознавания аудио: {e}")

    def _init_managers(self):
        """Инициализация всех менеджеров"""
        self.api_client = APIClient()  # Ваш реальный API клиент
        self.audio_manager = AudioManager()
        self.screenshot_manager = ScreenshotManager()
        self.text_formatter = TextFormatter()

        self.history_panel = QListWidget()
        self.history_manager = HistoryManager(self.history_panel)

    def _setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.setWindowTitle("AI Code Analyzer Pro")
        self.setMinimumSize(1000, 700)

        # Главный контейнер
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # Панель истории (слева)
        self._setup_history_panel()
        main_layout.addWidget(self.history_panel, stretch=1)

        # Основная панель (справа)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)

        # Виджеты
        self._setup_tool_panel()
        self._setup_text_areas()
        self._setup_status_bar()

        right_layout.addWidget(self.tool_group)
        right_layout.addWidget(self.response_area, stretch=3)
        right_layout.addWidget(self.question_input)
        right_layout.addWidget(self.progress_bar)
        right_layout.addWidget(self.status_label)

        main_layout.addWidget(right_panel, stretch=3)
        self.setCentralWidget(main_widget)

        # Подсветка Markdown
        self.highlighter = MarkdownHighlighter(self.response_area.document())

    def _init_rubber_band(self):
        """Инициализация резиновой полосы выделения"""
        self.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.rubber_band.setStyleSheet("""
            QRubberBand {
                border: 2px dashed #0078d7;
                background-color: rgba(0, 120, 215, 20%);
            }
        """)

    def _setup_history_panel(self):
        """Настройка панели истории"""
        self.history_panel.setMinimumWidth(250)
        self.history_panel.setStyleSheet("""
            QListWidget {
                border: 1px solid #e1e4e8;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
            }
        """)

    def _setup_tool_panel(self):
        """Настройка панели инструментов с двумя горизонтальными линиями"""
        self.tool_group = QGroupBox("Инструменты")
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)

        # Верхняя линия с кнопками очистки истории и повторным запросом
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        self.btn_clear_history = QPushButton(" 🗑️Очистить историю")
        self.btn_repeat_request = QPushButton(" 🔁Повторить запрос")

        # Ограничим ширину кнопок, чтобы были аккуратнее
        for btn in [self.btn_clear_history, self.btn_repeat_request]:
            btn.setMaximumWidth(140)
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        top_layout.addWidget(self.btn_clear_history)
        top_layout.addWidget(self.btn_repeat_request)
        top_layout.addStretch(1)  # Отодвинем кнопки влево

        # Нижняя линия с остальными контролами
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        self.api_selector = QComboBox()
        self.api_selector.addItems(["Cody", "OpenAI", "DeepSeek"])

        self.audio_mode = QComboBox()
        self.audio_mode.addItems(["Системный звук", "Выключено"])

        self.btn_select_area = QPushButton("Выбрать область")
        self.btn_select_area.setCheckable(True)
        self.btn_analyze = QPushButton(" 📸Анализ кода")
        self.btn_clear = QPushButton("🧹Очистить")
        self.btn_audio_toggle = QPushButton(" 🎤Включить аудио")

        # Ограничим ширину кнопок
        buttons = [
            self.btn_select_area,
            self.btn_analyze,
            self.btn_clear,
            self.btn_audio_toggle,
        ]
        for btn in buttons:
            btn.setMaximumWidth(130)
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        bottom_layout.addWidget(QLabel("API:"))
        bottom_layout.addWidget(self.api_selector)
        bottom_layout.addWidget(QLabel("Режим:"))
        bottom_layout.addWidget(self.audio_mode)
        bottom_layout.addWidget(self.btn_select_area)
        bottom_layout.addWidget(self.btn_analyze)
        bottom_layout.addWidget(self.btn_clear)
        bottom_layout.addWidget(self.btn_audio_toggle)
        bottom_layout.addStretch(1)

        # Собираем общий лэйаут
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)

        self.tool_group.setLayout(main_layout)

    def _setup_text_areas(self):
        """Настройка текстовых областей"""
        # Область ответа
        self.response_area = QTextEdit()
        self.response_area.setReadOnly(False)
        self.response_area.setAcceptRichText(True)

        # Поле ввода вопроса
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Введите ваш вопрос...")
        self.question_input.setClearButtonEnabled(True)

    def _setup_status_bar(self):
        """Настройка статус-бара"""
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)

        self.status_label = QLabel("🔴 Ожидание действий")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _on_audio_text_ready(self, text):
        logging.info(f"Audio text received: {text}")
        self.response_area.append(f"<b>🎤 Распознано аудио:</b><br>{text}<br>")

        # Для отправки в API
        self._start_processing("Отправка распознанного текста в API...")
        self.api_client.send_request(
            api_name=self.api_selector.currentText(),
            prompt=text
        )

    def _connect_signals(self):
        """Подключение сигналов и слотов"""
        # Кнопки
        self.btn_select_area.clicked.connect(self._toggle_area_selection)
        self.btn_analyze.clicked.connect(self._analyze_code)
        self.btn_clear.clicked.connect(self._clear_output)
        self.btn_audio_toggle.clicked.connect(self._toggle_audio)

        self.btn_repeat_request.clicked.connect(self._repeat_request)
        self.btn_clear_history.clicked.connect(self._clear_history)

        # Выпадающие списки
        self.audio_mode.currentIndexChanged.connect(self._change_audio_mode)

        # Поле ввода
        self.question_input.returnPressed.connect(self._ask_question)

        # Менеджеры
        self.audio_manager.status_changed.connect(self._update_status)
        self.audio_manager.error_occurred.connect(self._handle_error)

        self.screenshot_manager.text_extracted.connect(self._handle_text_extracted)
        self.screenshot_manager.error_occurred.connect(self._handle_error)
        self.screenshot_manager.screenshot_taken.connect(self._handle_screenshot_taken)

        self.history_manager.item_requested.connect(self._load_history_item)

        # API клиент
        self.api_client.response_received.connect(self._handle_api_response)
        self.api_client.error_occurred.connect(self._handle_error)
        self.api_client.progress_updated.connect(self._update_progress)

    def _clear_history(self):
        self.history_manager.clear_history()
        self._update_status("История запросов очищена")

    def _repeat_request(self):
        """Повторно отправляет выбранный запрос из истории"""
        item = self.history_panel.currentItem()
        if not item:
            return

        item_data = item.data(Qt.ItemDataRole.UserRole)
        question = item_data.get("prompt", "")
        if question:
            self.question_input.setText(question)
            self._send_prompt()
    def _send_prompt(self):
        # Если есть существующий метод send_prompt, просто вызови его
        self._ask_question()

    def _setup_styles(self):
        """Настройка стилей приложения"""
        self.setStyleSheet("""
            /* Основные стили */
            QMainWindow {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Arial;
            }

            /* Группы */
            QGroupBox {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }

            /* Кнопки */
            QPushButton {
                padding: 6px 12px;
                border-radius: 4px;
                border: 1px solid #ced4da;
                background-color: #f8f9fa;
                min-width: 80px;
            }

            QPushButton:hover {
                background-color: #e2e6ea;
            }

            QPushButton:pressed {
                background-color: #dae0e5;
            }

            QPushButton:checked {
                background-color: #d1e7ff;
            }

            /* Выпадающие списки */
            QComboBox {
                padding: 5px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                min-width: 100px;
            }

            /* Текстовые поля */
            QTextEdit, QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                selection-background-color: #4CAF50;
            }

            /* Прогресс-бар */
            QProgressBar {
                border: 1px solid #ced4da;
                border-radius: 4px;
                text-align: center;
                height: 20px;
            }

            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
            }

            /* Список истории */
            QListWidget {
                alternate-background-color: #f8f9fa;
            }

            QListWidget::item:hover {
                background-color: #e9ecef;
            }

            QListWidget::item:selected {
                background-color: #d1e7ff;
                color: #000;
            }
        """)

    def mousePressEvent(self, event):
        """Обработка нажатия мыши для выделения области"""
        if self.btn_select_area.isChecked() and event.button() == Qt.MouseButton.LeftButton:
            self.origin = event.pos()
            self.rubber_band.setGeometry(QRect(self.origin, QSize()))
            self.rubber_band.show()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Обработка движения мыши для выделения области"""
        if self.btn_select_area.isChecked() and self.rubber_band.isVisible():
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Обработка отпускания мыши для завершения выделения"""
        if self.btn_select_area.isChecked() and self.rubber_band.isVisible():
            rect = self.rubber_band.geometry()
            if rect.width() > 10 and rect.height() > 10:
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
                self._update_status(f"✅ Область: {rect.width()}x{rect.height()} пикс.")

            self.rubber_band.hide()
            self.btn_select_area.setChecked(False)
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def _toggle_area_selection(self, checked):
        """Переключение режима выбора области"""
        self.setCursor(Qt.CursorShape.CrossCursor if checked else Qt.CursorShape.ArrowCursor)
        self.btn_select_area.setText("🚫 Отменить" if checked else "🖱️ Выбрать область")

    def _analyze_code(self):
        """Анализ кода в выделенной области"""
        if not hasattr(self, 'selected_region') or not self.selected_region:
            self._handle_error("Сначала выберите область для захвата")
            return

        self._start_processing("Захват экрана...")
        self.screenshot_manager.set_region(self.selected_region)
        self.screenshot_manager.capture_and_analyze()

    def _ask_question(self):
        """Отправка вопроса на анализ"""
        question = self.question_input.text().strip()
        if not question:
            return

        self._start_processing("Отправка запроса...")
        self.question_input.setProperty("last_question", question)
        self.question_input.clear()

        # Реальная отправка через API клиент
        self.api_client.send_request(
            api_name=self.api_selector.currentText(),
            prompt=question
        )

    def _toggle_audio(self):
        """Переключение режима аудио"""
        self.audio_manager.toggle_recording()
        self.btn_audio_toggle.setText(
            "⏹ Остановить" if self.audio_manager.is_recording
            else "🎤 Включить аудио"
        )

    def _change_audio_mode(self, index):
        """Изменение режима аудио"""
        self.audio_manager.set_mode(index)

    def _clear_output(self):
        """Очистка вывода"""
        self.response_area.clear()
        self._update_status("Готово")

    def _start_processing(self, message):
        """Начало обработки"""
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self._update_status(message)

    def _finish_processing(self):
        """Завершение обработки"""
        self.progress_bar.setVisible(False)
        self._update_status("Готово")

    def _update_progress(self, value):
        """Обновление прогресса"""
        self.progress_bar.setValue(value)

    def _update_status(self, message):
        """Обновление статуса"""
        self.status_label.setText(message)

    def _handle_error(self, error):
        """Обработка ошибки"""
        self.response_area.append(self.text_formatter.format_error(error))
        self._finish_processing()
        logging.error(error)

    def _handle_text_extracted(self, text):
        """Обработка извлеченного текста"""
        self.response_area.append(self.text_formatter.format_code(text))
        self.ask_ai(text)

    def _handle_screenshot_taken(self, pixmap):
        """Обработка сделанного скриншота (можно сохранить или показать)"""
        pass

    def _handle_api_response(self, response):
        """Обработка ответа от API"""
        try:
            # Сохраняем в историю
            question = self.question_input.property("last_question")
            self.history_manager.add_item(question, response)

            # Отображаем ответ
            html = markdown(
                response,
                extensions=[
                    'fenced_code',
                    CodeHiliteExtension(linenums=False, guess_lang=True, noclasses=True)
                ]
            )
            self.response_area.setHtml(html)
            self._finish_processing()

        except Exception as e:
            self._handle_error(f"Ошибка обработки ответа: {str(e)}")

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

    def _load_history_item(self, item_data):
        """Загрузка элемента истории"""
        self.response_area.clear()
        question = item_data.get("prompt", "")
        response = item_data.get("response", "")

        self.response_area.append(
            self.text_formatter.format_text(f"💬 Вопрос: {question}")
        )
        self.response_area.append(
            self.text_formatter.format_text(f"🤖 Ответ: {response}")
        )

        # --- Вспомогательные методы ---

    def start_processing(self, message):
        """Начало длительной операции"""
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText(message)

    def handle_response(self, response):
        """Обработка ответа от API"""
        logging.info(response)
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
        """Обработка закрытия окна"""
        self.audio_manager.cleanup()
        self.screenshot_manager.cleanup()
        self.history_manager.cleanup()
        self.api_client.cancel_current()
        logging.info("Application closed")
        super().closeEvent(event)
