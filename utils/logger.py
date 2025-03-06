import sys
import os
from loguru import logger

def create_directory_if_not_exists(directory):
    """指定されたディレクトリが存在しない場合に作成する関数。"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"ディレクトリ '{directory}' を作成しました。")

def configure_logging(level="DEBUG", stream=sys.stdout, rotation="10 MB"): #  修正: rotation をリストから文字列 "10 MB" に変更
    """
    loguru を設定する関数。
    コンソール出力とファイル出力を設定し、ログフォーマットとログレベルを定義。
    ファイルローテーション設定 (サイズ上限) を追加。

    Args:
        level (str): ロギングレベル (例: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        stream (io.TextIOBase): コンソールログ出力先ストリーム (例: sys.stdout, sys.stderr)
        rotation (str, optional): ログローテーション設定 (例: "10 MB", "1 day"). Defaults to "10 MB". #  修正: rotation の型とデフォルト値を修正
    """
    # 既存の Handler をクリア (設定の重複を避けるため)
    logger.configure(handlers=[])

    # logs ディレクトリ作成
    log_directory = "logs"
    create_directory_if_not_exists(log_directory)

    # ログファイル設定
    log_file_path = os.path.join(log_directory, "app.log")
    logger.add(
        log_file_path,
        level=level, #  ファイルログレベル
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name} | {message}", #  フォーマット
        encoding="utf-8",
        enqueue=True, #  非同期化 (パフォーマンス向上)
        backtrace=True, #  バックトレースを記録
        diagnose=True,  #  診断情報を記録
        rotation=rotation,  #  修正: rotation に単一の文字列 "10 MB" を設定 (サイズローテーション)
        retention=5, #  保持するログファイル数: 5個
        compression="zip", #  ローテーション時にファイルを zip 圧縮
    )

    # コンソール出力設定
    logger.add(
        stream,
        level=level, #  コンソールログレベル
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> | <level>{message}</level>", # フォーマット (色付き)
        colorize=True, #  カラー表示
        enqueue=True, #  非同期化
    )

def get_logger(name):
    """
    loguru ロガーを取得する関数。

    Args:
        name (str): ロガー名

    Returns:
        loguru.Logger: loguru ロガーオブジェクト
    """
    return logger.bind(name=name) #  bind でロガー名を設定


if __name__ == "__main__":
    # ロギング設定 (DEBUG レベル, 標準出力)
    configure_logging(level="DEBUG", stream=sys.stdout)
    logger_example = get_logger(__name__) #  ロガーを取得

    logger_example.debug("デバッグログ: 変数の値", variable_name="example", value=123) #  構造化ログ
    logger_example.info("情報ログ: 処理開始", process_name="データ収集")
    logger_example.warning("警告ログ: ディスク容量", free_space="10GB")
    logger_example.error("エラーログ: ファイル読み込み失敗", filename="data.csv", exc_info=True) #  exc_info=True で例外情報も出力
    logger_example.critical("致命的なエラー: システム停止", component="DB接続", error_detail="接続タイムアウト")

    try:
        1 / 0
    except ZeroDivisionError:
        logger_example.exception("例外発生: ゼロ除算") #  exception() で例外情報を出力 (トレースバック)

    print("logs/app.log を確認してください (ログファイル出力)") #  追記