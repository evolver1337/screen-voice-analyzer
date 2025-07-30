from PyQt6.QtGui import (
    QTextCharFormat,
    QColor,
    QSyntaxHighlighter,
    QTextDocument
)
from PyQt6.QtCore import Qt
import html
import re


class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, parent: QTextDocument = None):
        super().__init__(parent)
        self._init_formats()
        self._init_rules()

    def _init_formats(self):
        """Инициализация всех стилей форматирования"""
        # Заголовки
        self.formats = {
            'heading': self._create_format('#3b82f6', bold=True),
            'code': self._create_format('#24292e', bg='#f5f5f5', font='Consolas'),
            'bold': self._create_format(bold=True),
            'italic': self._create_format(italic=True),
            'link': self._create_format('#0366d6', underline=True),
            'list': self._create_format('#24292e'),
            'quote': self._create_format('#6a737d', bg='#f6f8fa', italic=True),
        }

    def _create_format(self, color=None, bg=None, bold=False, italic=False, underline=False, font=None):
        """Создание QTextCharFormat с заданными параметрами"""
        fmt = QTextCharFormat()
        if color:
            fmt.setForeground(QColor(color))
        if bg:
            fmt.setBackground(QColor(bg))
        if bold:
            fmt.setFontWeight(75)
        if italic:
            fmt.setFontItalic(True)
        if underline:
            fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
        if font:
            fmt.setFontFamily(font)
        return fmt

    def _init_rules(self):
        """Инициализация правил подсветки"""
        self.rules = [
            # Заголовки (###)
            (r'^#{1,6}\s.*$', 0, self.formats['heading']),
            # Блоки кода (```)
            (r'`{3}.*`{3}', 0, self.formats['code']),
            # Инлайн код (`code`)
            (r'`[^`]+`', 0, self.formats['code']),
            # Жирный текст (**bold**)
            (r'\*\*[^*]+\*\*', 0, self.formats['bold']),
            # Наклонный текст (_italic_)
            (r'_[^_]+_', 0, self.formats['italic']),
            # Ссылки ([text](url))
            (r'\[.*?\]\(.*?\)', 0, self.formats['link']),
            # Списки (- item)
            (r'^[\*\-\+] .*$', 0, self.formats['list']),
            # Цитаты (> quote)
            (r'^> .*$', 0, self.formats['quote']),
        ]

    def highlightBlock(self, text):
        """Применение правил подсветки"""
        for pattern, nth, fmt in self.rules:
            for match in re.finditer(pattern, text):
                start = match.start(nth)
                length = match.end(nth) - start
                self.setFormat(start, length, fmt)


class TextFormatter:
    @staticmethod
    def format_text(text: str) -> str:
        """Форматирование обычного текста"""
        escaped = html.escape(text)
        return f"""
        <div style="
            margin-bottom: 16px;
            line-height: 1.6;
            color: #24292e;
        ">
            {escaped.replace('\n', '<br>')}
        </div>
        """

    @staticmethod
    def format_code(code: str, language: str = '') -> str:
        """Форматирование блоков кода"""
        language = language or 'text'
        return f"""
        <div style="
            background:#f8f8f8;
            border:1px solid #e1e4e8;
            border-radius:6px;
            padding:12px;
            margin:10px 0;
            overflow-x:auto;
            font-family:'Consolas',monospace;
        ">
            <div style="
                color:#6a737d;
                font-family:sans-serif;
                font-size:12px;
                margin-bottom:8px;
            ">
                {language.upper()}
            </div>
            <div style="white-space:pre-wrap;margin:0;padding:0;">
                {html.escape(code)}
            </div>
        </div>
        """

    @staticmethod
    def format_error(message: str) -> str:
        """Форматирование сообщений об ошибках"""
        return f"""
        <div style="
            background-color: #fee2e2;
            border-left: 4px solid #dc2626;
            padding: 10px;
            margin: 5px 0;
            color: #dc2626;
        ">
            <strong>❌ Ошибка:</strong> {html.escape(message)}
        </div>
        """