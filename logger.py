import logging
import sys
import structlog
from rich.logging import RichHandler
from rich.console import Console
from rich.traceback import install
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.syntax import Syntax
from rich.panel import Panel
from rich import print
from rich.table import Table
import time
import json

# Richによるトレースバック表示を有効化
install(show_locals=True)

# Richのコンソールインスタンスを作成
console = Console()


def configure_logging(level=logging.DEBUG, stream=sys.stdout):
    """
    structlog の設定を行う関数。
    structlog を使用して、構造化ロギングを行うための設定を行う。
    RichHandler を使用して、リッチなログ出力を実現。

    Args:
        level (int): ロギングレベル (例: logging.DEBUG, logging.INFO, logging.WARNING)。
        stream (io.TextIOBase): ログ出力先ストリーム (例: sys.stdout, sys.stderr, ファイルオブジェクト)。
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=structlog.threadlocal.wrap_dict(dict),
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # RichHandler を使用してリッチなログ出力を実現
    logging.basicConfig(
        level=level,
        format="%(message)s",  # structlog がフォーマットするので空にする
        handlers=[RichHandler(console=console, rich_tracebacks=True, markup=True, log_time_format="[%Y-%m-%d %H:%M:%S]",
                                highlighter=get_highlighter())]  # ハイライト処理追加
    )


def get_logger(name=None):
    """
    structlog のロガーインスタンスを取得する関数。

    Args:
        name (str, optional): ロガー名。指定しない場合はルートロガーを取得。

    Returns:
        structlog.stdlib.BoundLogger: structlog のロガーインスタンス。
    """
    return structlog.get_logger(name)


def print_separator(title=None, style="[bold blue]"):
    """
    区切り線を出力する関数。

    Args:
        title (str, optional): 区切り線の中央に表示するタイトル。
        style (str, optional): 区切り線のスタイル。
    """
    if title:
        print(Panel(f"{style}{title}[/]", expand=False))
    else:
        print(f"{style}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")


def print_syntax_highlight(code, lexer="python", title="Code"):
    """
    コードをシンタックスハイライトして出力する関数。

    Args:
        code (str): ハイライトするコード。
        lexer (str, optional): 使用するlexerの名前。デフォルトは "python"。
        title (str, optional): コードパネルのタイトル。
    """
    syntax = Syntax(code, lexer, theme="monokai", line_numbers=True)
    print(Panel(syntax, title=title))


def create_progress_bar():
    """
    プログレスバーを作成する関数。
    """
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console
    )
    return progress


def print_exception(e):
    """
    例外情報を出力する関数。
    """
    print_separator(title="[bold red]Exception Traceback[/]")
    console.print_exception(extra_lines=5, show_locals=True)  # スタックフレームを５つまで、ローカル変数も表示
    print_separator()


def get_highlighter():
    """
    ログレベルに応じた色分けを行うためのRichのHighlighterを定義する。
    """
    from rich.highlighter import ReprHighlighter
    from rich.highlighter import Highlighter

    class LogLevelHighlighter(Highlighter):
        def highlight(self, text):
            if "INFO" in text:
                text.stylize("green", 0, len(text))
            elif "WARNING" in text:
                text.stylize("yellow", 0, len(text))
            elif "ERROR" in text or "CRITICAL" in text:
                text.stylize("bold red", 0, len(text))
            elif "DEBUG" in text:
                text.stylize("blue", 0, len(text))
            return text

    return LogLevelHighlighter()


def format_exception_code(code, language="python"):
    """
        例外発生時に表示するコードをフォーマットする関数。
        Args:
            code (str): コード文字列
            language(str) : コード言語
    """

    try:
        if language == "json":
            json.loads(code)  # JSON形式かをチェック

        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        print(Panel(syntax, title=f"[b red]Exception Code ({language})[/b red]"))

    except json.JSONDecodeError as e:
        print(f"[red]Invalid JSON format: {e}[/red]")
        print(code)
    except Exception as e:
        print(f"[red]Error formatting code: {e}[/red]")
        print(code)


if __name__ == "__main__":
    # ロギング設定を初期化 (DEBUGレベル、標準出力)
    configure_logging(level=logging.DEBUG, stream=sys.stdout)
    logger_debug = get_logger(__name__)  # ロガーを取得 (名前付き)

    # 区切り線を表示
    print_separator(title="Debug Log Example")
    logger_debug.debug("デバッグログ", detail="詳細情報", value=123)  # 構造化ログ出力
    print_separator()

    # ロギング設定を初期化 (INFOレベル、標準エラー出力)
    configure_logging(level=logging.INFO, stream=sys.stderr)
    logger_info = get_logger("info_logger")  # ロガーを取得 (名前付き)

    # 区切り線を表示
    print_separator(title="Info Log Example")
    logger_info.info("情報ログ", action="実行", status="成功")  # 構造化ログ出力
    print_separator()

    # ロギング設定を初期化 (WARNINGレベル、ファイル出力)
    import tempfile

    log_file = tempfile.NamedTemporaryFile(mode='w', delete=False)  # 一時ファイル作成
    configure_logging(level=logging.WARNING, stream=log_file)
    logger_warning = get_logger()  # ロガーを取得 (ルートロガー)

    # 区切り線を表示
    print_separator(title="Warning Log Example")
    logger_warning.warning("警告ログ", problem="ディスク容量不足")  # 構造化ログ出力
    log_file.close()  # ファイルを閉じる

    print("\nログ出力例 (DEBUGレベル、標準出力):")
    logger_debug.debug("これはデバッグメッセージです。")
    print("\nログ出力例 (INFOレベル、標準エラー出力):")
    logger_info.info("これは情報メッセージです。")
    print("\nログ出力例 (WARNINGレベル、ファイル出力):")
    with open(log_file.name, 'r') as f:  # 一時ファイルの内容を読み込んで表示
        print(f.read())
    print(f"ログファイル出力先: {log_file.name}")  # ログファイル名を表示

    # 区切り線を表示
    print_separator(title="Syntax Highlight Example")
    code_example = """
def hello_world():
    print("Hello, World!")

hello_world()
    """
    print_syntax_highlight(code_example)
    print_separator()

    # プログレスバーを表示
    print_separator(title="Progress Bar Example")
    progress = create_progress_bar()
    with progress:
        task = progress.add_task("[green]Processing...", total=100)
        while not progress.finished:
            progress.update(task, advance=1)
            time.sleep(0.05)
    print_separator()

    # 例外情報を表示
    print_separator(title="Exception Example")
    try:
        result = 1 / 0
    except ZeroDivisionError as e:
        print_exception(e)
    print_separator()

    print_separator(title="format_exception_code Example")
    code_python = """
def hello():
    print("hello")

hello()
"""
    code_json = """
{
    "name": "test",
    "value": 123
}
"""
    code_invalid_json = """
{
    "name": "test",
    "value": 123,
}
"""

    format_exception_code(code_python)
    format_exception_code(code_json, "json")
    format_exception_code(code_invalid_json, "json")
    print_separator()

    # 例外が発生した際のリッチなトレースバック表示
    print_separator(title="Rich Traceback Example")
    try:
        def inner_function():
            raise ValueError("This is a test error!")


        def outer_function():
            inner_function()


        outer_function()

    except ValueError:
        # Richのトレースバック表示
        console.print_exception(extra_lines=5, show_locals=True)
    print_separator()