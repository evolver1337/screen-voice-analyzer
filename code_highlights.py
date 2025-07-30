from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

class CodeHighlighter:
    @staticmethod
    def highlight(code, language):
        try:
            lexer = get_lexer_by_name(language, stripall=True)
            formatter = HtmlFormatter(
                style='monokai',
                noclasses=True,
                cssstyles="font-family: 'Consolas', monospace;"
            )
            return highlight(code, lexer, formatter)
        except:
            # Fallback если язык не распознан
            return f'<pre style="font-family: Consolas">{code}</pre>'