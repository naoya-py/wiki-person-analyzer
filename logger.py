from loguru import logger
import sys
import os

# ログファイルの保存先 (data/logsディレクトリ)
LOG_DIR = "data/logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# ログファイル名 (日付でローテーション)
LOG_FILE = os.path.join(LOG_DIR, "biography_analyzer_{time:YYYY-MM-DD}.log")

# ロガーの設定
logger.remove()  # デフォルトのハンドラを削除

# 標準エラー出力(コンソール)へのログ出力設定
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",  # DEBUG以上のレベルを記録
)

# ファイルへのログ出力設定
logger.add(
    LOG_FILE,
    rotation="1 day",  # 1日ごとに新しいログファイルを作成
    retention="7 days",  # 7日分のログファイルを保持
    level="INFO",  # INFO以上のレベルを記録
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    enqueue=True,  # 非同期書き込み (パフォーマンス向上)
)

def setup_logger(level="INFO"):
    """
    ログレベルを設定する関数 (必要に応じて使用)

    Args:
        level (str): ログレベル ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
    """
    # 既存のハンドラを削除 (設定をリセットするため)
    logger.remove()

    # 標準エラー出力へのハンドラを追加
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
    )

    # ファイルへのハンドラを追加
    logger.add(
        LOG_FILE,
        rotation="1 day",
        retention="7 days",
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        enqueue=True,
    )
    return logger

# このモジュールをインポートしたときに、`logger` オブジェクトが利用可能になる
# 例: from logger import logger
# setup_logger()は必要に応じて呼び出す。呼び出さなければデフォルトで、INFOレベル