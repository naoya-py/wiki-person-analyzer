import sys
import os
from loguru import logger
from config import Config
import pandas as pd
from tabulate import tabulate

def create_directory_if_not_exists(directory):
    """指定されたディレクトリが存在しない場合に作成する関数。"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"ディレクトリ '{directory}' を作成しました。")


def configure_logging(
        level=None,
        stream=sys.stdout,
        rotation=None,
        retention=None,
        compression=None,
        log_directory=None,
        log_file_format=None,
        console_log_format=None,
):
    """
    loguru を設定する関数。
    コンソール出力とファイル出力を設定し、ログフォーマットとログレベルを定義。
    ファイルローテーション設定 (サイズ上限) を追加。

    Args:
        level (str, optional): ロギングレベル (例: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"). Defaults to None (Config.DEFAULT_LOG_LEVEL を使用).
        stream (io.TextIOBase, optional): コンソールログ出力先ストリーム (例: sys.stdout, sys.stderr). Defaults to sys.stdout.
        rotation (str, optional): ログローテーション設定 (例: "10 MB", "1 day"). Defaults to None (Config.LOG_ROTATION を使用).
        retention (int, optional): 保持するログファイル数. Defaults to None (Config.LOG_RETENTION を使用).
        compression (str, optional): ローテーション時のファイル圧縮形式. Defaults to None (Config.LOG_COMPRESSION を使用).
        log_directory (str, optional): ログファイル出力先ディレクトリ. Defaults to None (Config.LOG_DIRECTORY を使用).
        log_file_format (str, optional): ログファイルフォーマット. Defaults to None (Config.LOG_FILE_FORMAT を使用).
        console_log_format (str, optional): コンソールログフォーマット. Defaults to None (Config.CONSOLE_LOG_FORMAT を使用).
    """
    logger.configure(handlers=[])

    log_level = level if level is not None else Config.DEFAULT_LOG_LEVEL
    log_dir = log_directory if log_directory is not None else Config.LOG_DIRECTORY
    file_log_format = log_file_format if log_file_format is not None else Config.LOG_FILE_FORMAT
    console_format = console_log_format if console_log_format is not None else Config.CONSOLE_LOG_FORMAT
    log_rotation = rotation if rotation is not None else Config.LOG_ROTATION
    log_retention = retention if retention is not None else Config.LOG_RETENTION
    log_compression = compression if compression is not None else Config.LOG_COMPRESSION

    create_directory_if_not_exists(log_dir)

    log_file_path = os.path.join(log_dir, "app.log")
    logger.add(
        log_file_path,
        level=log_level,
        format=file_log_format,
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        diagnose=True,
        rotation=log_rotation,
        retention=log_retention,
        compression=log_compression,
    )

    logger.add(
        stream,
        level=log_level,
        format=console_format,
        colorize=True,
        enqueue=True,
    )


def get_logger(name):
    """
    loguru ロガーを取得する関数。

    Args:
        name (str): ロガー名

    Returns:
        loguru.Logger: loguru ロガーオブジェクト
    """
    return logger.bind(name=name)


# pandas の表示設定を変更
pd.set_option("display.max_rows", 20)  # 最大表示行数
pd.set_option("display.max_columns", 20)  # 最大表示列数
pd.set_option("display.width", 100)  # コンソールの表示幅
pd.set_option("display.colheader_justify", "center")  # カラムヘッダの配置
pd.set_option("display.precision", 3)  # 小数点以下の桁数
pd.set_option('display.unicode.east_asian_width', True)  # 文字幅の調整


def log_dataframe(logger_instance, df, level="info", max_col_width=20):
    """
    pandas DataFrame を tabulate を使ってコンソールに整形して出力する関数。
    長いテキストや多くのカラムに対応するため、表示を調整します。
    Jupyter Notebook のようにデータ型も表示するように変更。

    Args:
        logger_instance: loguru のロガーインスタンス
        df: 表示する pandas DataFrame
        level: ログレベル ("debug", "info", "warning", "error", "critical")
        max_col_width (int, optional): 各カラムの最大幅。これを超えるテキストは切り捨てられます。Defaults to 20.
    """
    headers = []
    for col in df.columns:
        dtype_str = str(df[col].dtype)
        headers.append(f"{col}\n({dtype_str})")

    formatted_rows = []
    for index, row in df.iterrows():
        formatted_row = []
        for x in row:
            if isinstance(x, str) and len(x) > max_col_width:
                formatted_row.append(x[:max_col_width] + "...")
            else:
                formatted_row.append(str(x))
        formatted_rows.append(formatted_row)

    table = tabulate(formatted_rows, headers=headers, tablefmt="grid")  # tablefmt を "grid" に設定

    # ログレベルに応じてコンソールに出力
    if level == "debug":
        logger_instance.debug(f"\n{table}")
    elif level == "info":
        logger_instance.info(f"\n{table}")
    elif level == "warning":
        logger_instance.warning(f"\n{table}")
    elif level == "error":
        logger_instance.error(f"\n{table}")
    elif level == "critical":
        logger_instance.critical(f"\n{table}")
    else:
        logger_instance.info(f"\n{table}")



def log_dataframe_pprint(logger_instance, df, level="info"):
    """
    pprint を使って DataFrame をコンソールに出力する関数。
    """
    logger_instance.info(f"DataFrame:\n{df.to_string()}")


if __name__ == "__main__":
    # ログ設定 (Config クラスは適切に設定されているものとします)
    configure_logging(level=Config.DEFAULT_LOG_LEVEL)
    logger_example = get_logger(__name__)

    # DataFrame のサンプルデータ (横幅が広く、長いテキストを含むもの)
    data = {
        "ID": range(1, 6),
        "Name": ["Alice Smith", "Bob Johnson", "Charlie Brown", "David Williams", "Eve Davis"],
        "Age": [25, 30, 35, 40, 28],
        "City": ["New York City, USA", "London, United Kingdom", "Paris, France", "Tokyo, Japan", "Sydney, Australia"],
        "Description": [
            "This is a very long description about Alice that might exceed the console width.",
            "Bob's description is also quite lengthy and should be handled appropriately.",
            "Charlie's description is shorter.",
            "David's description is moderately long.",
            "Eve's description is also on the longer side.",
        ],
        "Feature1": [True, False, True, True, False],
        "Feature2": [1.23456789, 2.34567890, 3.45678901, 4.56789012, 5.67890123],
        "Category": ["A", "B", "A", "C", "B"],
    }
    df_wide = pd.DataFrame(data)

    # DataFrame をログに出力 (デフォルトの最大カラム幅)
    logger_example.info("デフォルト設定での DataFrame 表示")
    log_dataframe(logger_example, df_wide, level="info")

    # DataFrame をログに出力 (最大カラム幅を 10 に設定)
    logger_example.info("最大カラム幅を 10 に設定した DataFrame 表示")
    log_dataframe(logger_example, df_wide, level="info", max_col_width=10)

    # DataFrame をログに出力 (最大カラム幅を 30 に設定)
    logger_example.info("最大カラム幅を 30 に設定した DataFrame 表示")
    log_dataframe(logger_example, df_wide, level="info", max_col_width=30)

    # DataFrameをpprintを使って表示
    logger_example.info("log_dataframe_pprint を使った DataFrame 表示")
    log_dataframe_pprint(logger_example, df_wide, level="info")

    # 通常のログメッセージも出力
    logger_example.debug("デバッグログ: 変数の値", variable_name="example", value=123)
    logger_example.info("情報ログ: 処理開始", process_name="データ収集")
    logger_example.warning("警告ログ: ディスク容量", free_space="10GB")
    logger_example.error("エラーログ: ファイル読み込み失敗", filename="data.csv", exc_info=True)
    logger_example.critical(
        "致命的なエラー: システム停止", component="DB接続", error_detail="接続タイムアウト"
    )

    try:
        1 / 0
    except ZeroDivisionError:
        logger_example.exception("例外発生: ゼロ除算")

    print("logs/app.log を確認してください (ログファイル出力)")