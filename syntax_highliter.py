from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
import html
import re


class SyntaxHighlighter:
    @staticmethod
    def highlight(code, language="text"):
        try:
            # Сохраняем табы и переносы
            code = code.replace('\t', '    ')

            # Экранируем только опасные символы (<, >, &), но не кавычки
            code = re.sub(r'([<>&])',
                          lambda m: {'<': '&lt;', '>': '&gt;', '&': '&amp;'}[m.group(1)], code)

            lexer = get_lexer_by_name(language, stripall=True)
            formatter = HtmlFormatter(
                style="friendly",
                noclasses=True,
                nowrap=True,
                prestyles="margin:0;padding:0;white-space:pre;"
            )

            highlighted = highlight(code, lexer, formatter)
            # Восстанавливаем кавычки после подсветки
            highlighted = highlighted.replace('&quot;', '"')
            return highlighted.replace('\n', '<br>')
        except Exception as e:
            print(f"Ошибка подсветки: {e}")
            return f'<pre style="white-space:pre-wrap">{code}</pre>'