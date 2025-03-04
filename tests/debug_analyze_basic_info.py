from core.analyzer import Analyzer
import pandas as pd
from utils.logger import configure_logging, get_logger, print_exception, print_separator
import logging
import sys
import json

# ロギング設定
configure_logging(level=logging.DEBUG, stream=sys.stdout)  # デバッグ用にDEBUGレベルで設定
logger = get_logger(__name__)


def debug_analyze_basic_info(df_basic):
    """
    analyze_basic_info メソッドをデバッグする関数。

    Args:
        df_basic (pd.DataFrame): 基本情報データフレーム。
    """
    print_separator(title="analyze_basic_info デバッグ開始")

    try:
        # Analyzer クラスのインスタンス化
        analyzer = Analyzer(df_basic, None, None)  # 年表、ネットワークはデバッグに不要なのでNone

        # analyze_basic_info メソッドの呼び出し
        print_separator(title="analyze_basic_info メソッド呼び出し")
        analysis_result = analyzer.analyze_basic_info()

        # 結果の確認
        print_separator(title="分析結果")
        print(json.dumps(analysis_result, ensure_ascii=False, indent=2))
        print_separator()

    except Exception as e:
        # エラー発生時の処理
        logger.error(f"analyze_basic_info デバッグ中にエラーが発生しました: {e}")
        print_exception(e)  # 例外情報を出力
        print_separator()


if __name__ == "__main__":
    # 正常なデータフレームのテスト
    print_separator(title="正常なデータフレームでのテスト")
    basic_info_data_ok = {
        "name": ["アルベルト・アインシュタイン"],
        "birth_date": ["1879年3月14日"],
        "death_date": ["1955年4月18日"],
        "nationality": ["ドイツ、スイス、アメリカ"],
        "field": ["理論物理学"],
    }
    df_basic_ok = pd.DataFrame(basic_info_data_ok)
    debug_analyze_basic_info(df_basic_ok)

    # 異常なデータフレーム（日付形式が不正）のテスト
    print_separator(title="異常なデータフレーム（日付形式が不正）でのテスト")
    basic_info_data_bad_date = {
        "name": ["マリー・キュリー"],
        "birth_date": ["1867年11月7日bad"],  # 不正な日付形式
        "death_date": ["1934年7月4日bad"],  # 不正な日付形式
        "nationality": ["ポーランド、フランス"],
        "field": ["物理学、化学"]
    }
    df_basic_bad_date = pd.DataFrame(basic_info_data_bad_date)
    debug_analyze_basic_info(df_basic_bad_date)

    # 異常なデータフレーム（欠損）のテスト
    print_separator(title="異常なデータフレーム（欠損）でのテスト")
    basic_info_data_missing = {
        "name": ["ニュートン"],
        "birth_date": [None],  # None
        "death_date": ["1727年3月31日"],
        "nationality": ["イギリス"],
        "field": ["物理学、数学"]
    }
    df_basic_missing = pd.DataFrame(basic_info_data_missing)
    debug_analyze_basic_info(df_basic_missing)

    # 異常なデータフレーム（空）のテスト
    print_separator(title="異常なデータフレーム（空）でのテスト")
    basic_info_data_empty = {}
    df_basic_empty = pd.DataFrame(basic_info_data_empty)
    debug_analyze_basic_info(df_basic_empty)

    # 異常なデータフレーム（型が不正）のテスト
    print_separator(title="異常なデータフレーム（型が不正）でのテスト")
    basic_info_data_bad_type = {
        "name": [123],  # int
        "birth_date": [18790314],  # int
        "death_date": [19550418],  # int
        "nationality": ["ドイツ、スイス、アメリカ"],
        "field": ["理論物理学"]
    }
    df_basic_bad_type = pd.DataFrame(basic_info_data_bad_type)
    debug_analyze_basic_info(df_basic_bad_type)

    print_separator(title="analyze_basic_info デバッグ完了")