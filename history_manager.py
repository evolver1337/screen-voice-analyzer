import json
import os
import logging
from datetime import datetime
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QMenu
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QIcon


class HistoryManager(QObject):
    history_cleared = pyqtSignal()
    item_deleted = pyqtSignal(int)
    item_requested = pyqtSignal(dict)

    def __init__(self, list_widget: QListWidget):
        super().__init__()
        self.history_panel = list_widget
        self.history_file = "history.json"
        self._setup_ui()
        self.load_history()
        logging.info("History manager initialized")

    def _setup_ui(self):
        """Настройка интерфейса истории"""
        self.history_panel.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_panel.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.history_panel.customContextMenuRequested.connect(self._show_context_menu)

    def add_item(self, prompt: str, response: str):
        """Добавляет новый элемент в историю"""
        try:
            is_error = "❌" in response
            timestamp = datetime.now().isoformat()

            item_data = {
                "prompt": prompt,
                "response": response,
                "timestamp": timestamp,
                "is_error": is_error
            }

            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, item_data)

            time_str = datetime.now().strftime('%H:%M')
            prefix = "[Ошибка] " if is_error else ""
            item.setText(f"{prefix}{time_str}: {prompt[:30]}...")

            self.history_panel.insertItem(0, item)
            self._save_history()
            logging.info("New item added to history")

        except Exception as e:
            logging.error(f"Error adding history item: {e}")

    def _show_context_menu(self, pos):
        """Показывает контекстное меню для истории"""
        try:
            menu = QMenu()
            current_item = self.history_panel.currentItem()

            repeat_action = menu.addAction("↻ Повторить запрос")
            delete_action = menu.addAction("🗑️ Удалить")
            clear_action = menu.addAction("🧹 Очистить всю историю")

            action = menu.exec_(self.history_panel.mapToGlobal(pos))

            if not current_item:
                return

            if action == repeat_action:
                data = current_item.data(Qt.ItemDataRole.UserRole)
                self.item_requested.emit(data)
            elif action == delete_action:
                self._delete_item(current_item)
            elif action == clear_action:
                self.clear_history()

        except Exception as e:
            logging.error(f"Context menu error: {e}")

    def clear_history(self):
        """Очищает всю историю"""
        self.history_panel.clear()
        self._save_history()
        self.history_cleared.emit()
        logging.info("History cleared")

    def _delete_item(self, item):
        """Удаляет конкретный элемент истории"""
        row = self.history_panel.row(item)
        self.history_panel.takeItem(row)
        self._save_history()
        self.item_deleted.emit(row)
        logging.info(f"History item deleted at row {row}")

    def _save_history(self):
        """Сохраняет историю в файл"""
        try:
            history = []
            for i in range(self.history_panel.count()):
                item = self.history_panel.item(i)
                history.append(item.data(Qt.ItemDataRole.UserRole))

            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logging.error(f"Error saving history: {e}")

    def load_history(self):
        """Загружает историю из файла"""
        try:
            if not os.path.exists(self.history_file):
                return

            with open(self.history_file, "r", encoding="utf-8") as f:
                history = json.load(f)

            self.history_panel.clear()
            for item_data in sorted(history, key=lambda x: x["timestamp"], reverse=True):
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, item_data)

                time_str = item_data["timestamp"][11:16]
                prefix = "[Ошибка] " if item_data.get("is_error") else ""
                item.setText(f"{prefix}{time_str}: {item_data['prompt'][:30]}...")

                self.history_panel.addItem(item)

            logging.info("History loaded from file")

        except Exception as e:
            logging.error(f"Error loading history: {e}")

    def _on_item_double_clicked(self, item):
        """Обработчик двойного клика по элементу"""
        data = item.data(Qt.ItemDataRole.UserRole)
        self.item_requested.emit(data)

    def cleanup(self):
        """Очистка ресурсов"""
        self._save_history()
        logging.info("History manager cleaned up")