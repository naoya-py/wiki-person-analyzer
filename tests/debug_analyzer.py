from analyzer import Analyzer
import pandas as pd
import json
from logger import configure_logging, get_logger, print_exception
import logging
import sys

configure_logging(level=logging.INFO, stream=sys.stdout) # debug_analyzerはINFO
logger = get_logger(__name__)
logger.info("debug_analyzer.py の実行を開始します。")

def convert_numpy_int(obj):
    if isinstance(obj, pd.Series) or isinstance(obj, pd.DataFrame):
        return obj.to_dict()
    if isinstance(obj, (int, str, list, dict, float, bool)):
        return obj
    if hasattr(obj, 'tolist'):
        return obj.tolist()
    return str(obj)

def display_tfidf_results(tfidf_results): # TF-IDF 結果表示関数 (修正版)
    """
    TF-IDF 分析結果を見やすく整形して表示する。
    年ごとの結果を整形して表示するように修正。

    Args:
        tfidf_results (dict): analyze_text_features() の結果 (dict: {"tfidf_scores": {year: {term: tfidf_score, ...}, ...}})
    """
    print("\n--- TF-IDF 分析結果 ---")
    if not tfidf_results or not tfidf_results["tfidf_scores"]: #  結果が空の場合 # 追記
        print("TF-IDF 分析結果は空です。") # 追記
        return # 追記

    tfidf_scores = tfidf_results["tfidf_scores"] # TF-IDF スコアを取得 # 追記

    for year, term_scores in tfidf_scores.items(): # 年ごとにループ # 変更
        print(f"\n**{year}年のTF-IDF上位ワード:**") # 年の見出しを表示 # 変更
        if not term_scores: #  年ごとの結果が空の場合 # 追記
            print("  (該当する単語はありません)") # 追記
            continue # 追記

        sorted_terms = sorted(term_scores.items(), key=lambda item: item[1], reverse=True) # TF-IDF スコアで降順ソート
        for term, score in sorted_terms[:10]:  # 上位10ワードを表示
            print(f"  - {term}: {score:.4f}") #  スコアを小数点以下4桁で表示

if __name__ == "__main__":
    # logger設定 (logger.py が必要)
    # logger.basicConfig(level=logger.DEBUG) #  basicConfig は logger.py で行う

    configure_logging(level=logging.INFO, stream=sys.stdout) #  ロギングレベルを INFO に設定
    logger = get_logger(__name__)

    #  基本情報データフレーム (例)
    basic_info_data = {
        "name": ["アルベルト・アインシュタイン"],
        "birth_date": ["1879年3月14日"],  # 日付文字列
        "death_date": ["1955年4月18日"],  # 日付文字列
        "nationality": ["ドイツ、スイス、アメリカ"],
        "field": ["理論物理学"]
    }
    df_basic = pd.DataFrame(basic_info_data)

    # 年表データフレーム (例)
    timeline_data = {
        "year": [1905, 1915, 1921, 1933, 1955, 1905, 1905, 1905, 1905, 1915],  # 年 (数値)
        "date": ["1905年", "1915年", "1921年", "1933年", "1955年", "3月", "5月", "6月", "9月", "11月"],  # 日付
        "event": [
            "奇跡の年",  # イベント内容
            "一般相対性理論発表",
            "ノーベル物理学賞受賞",
            "プリンストン高等研究所へ",
            "死去",
            "光量子仮説",
            "ブラウン運動の理論",
            "特殊相対性理論",
            "質量とエネルギーの等価性",  # E=mc^2
            "一般相対性理論",
        ],
    }
    df_timeline = pd.DataFrame(timeline_data)

    # 関係ネットワークデータフレーム (例)
    network_data = {
        "source": ["アルベルト・アインシュタイン", "アルベルト・アインシュタイン", "アルベルト・アインシュタイン", "マリー・キュリー", "ニールス・ボーア"],  # source
        "target": ["エルザ・アインシュタイン", "ミレヴァ・マリッチ", "ハンス・アルベルト・アインシュタイン", "アルベルト・アインシュタイン", "アルベルト_アインシュタイン"],  # target
        "relation": ["配偶者", "元配偶者", "息子", "友人", "友人"],  # 関係性
    }
    df_network = pd.DataFrame(network_data)

    analyzer = Analyzer(df_basic, df_timeline, df_network)

    # 基本情報分析
    try:  # try-except ブロックを追加
        basic_analysis_result = analyzer.analyze_basic_info()
        print("\n--- 基本情報分析結果 ---")
        print(json.dumps(basic_analysis_result, ensure_ascii=False, indent=2, default=convert_numpy_int))
    except Exception as e:  # 例外処理
        logger.error(f"基本情報分析でエラーが発生しました: {e}")

        # 年表分析 (全期間)
    try: #  try-except ブロックを追加
        timeline_analysis_result_full = analyzer.analyze_timeline()
        print("\n--- 年表分析結果 (全期間) ---")
        print(json.dumps(timeline_analysis_result_full, ensure_ascii=False, indent=2, default=convert_numpy_int))
    except Exception as e: #  例外処理
        logger.error(f"年表分析 (全期間) でエラーが発生しました: {e}") #  エラーログ出力


    # 年表分析 (1900年〜1920年)
    try: #  try-except ブロックを追加
        timeline_analysis_result_period = analyzer.analyze_timeline(start_year=1900, end_year=1920)
        print("\n--- 年表分析結果 (1900年〜1920年) ---")
        print(json.dumps(timeline_analysis_result_period, ensure_ascii=False, indent=2, default=convert_numpy_int))
    except Exception as e: #  例外処理
        logger.error(f"年表分析 (1900年〜1920年) でエラーが発生しました: {e}") #  エラーログ出力

    # 関係ネットワーク分析 (全体)
    try: #  try-except ブロックを追加
        network_analysis_result = analyzer.analyze_network()
        print("\n--- 関係ネットワーク分析結果 (全体) ---")
        print(json.dumps(network_analysis_result, ensure_ascii=False, indent=2, default=convert_numpy_int))  # グラフオブジェクトはstrに変換してJSON出力
    except Exception as e: #  例外処理
        logger.error(f"関係ネットワーク分析 (全体) でエラーが発生しました: {e}") #  エラーログ出力

    # 関係ネットワーク分析 (特定の人物: アルベルト・アインシュタイン)
    try: #  try-except ブロックを追加
        network_analysis_result_person = analyzer.analyze_network(target_person="アルベルト・アインシュタイン")
        print("\n--- 関係ネットワーク分析結果 (特定の人物: アルベルト・アインシュタイン) ---")
        print(json.dumps(network_analysis_result_person, ensure_ascii=False, indent=2, default=convert_numpy_int))
    except Exception as e: #  例外処理
        logger.error(f"関係ネットワーク分析 (特定の人物: アルベルト・アインシュタイン) でエラーが発生しました: {e}") #  エラーログ出力

    # テキスト特徴量分析 (TF-IDF)
    try: #  try-except ブロックを追加
        text_features_analysis_result = analyzer.analyze_text_features()  # テキスト特徴量分析を実行
        display_tfidf_results(text_features_analysis_result) #  TF-IDF 結果表示関数を実行
    except Exception as e: #  例外処理
        logger.error(f"テキスト特徴量分析でエラーが発生しました: {e}") #  エラーログ出力