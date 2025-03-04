from core.scraper import Scraper
from core.data_processor import DataProcessor
# from core.analyzer import Analyzer
import json
from utils.logger import configure_logging, get_logger #  logger.py (loguru 版) の import に変更
import logging
import sys

configure_logging(level="DEBUG", stream=sys.stdout) #  logger.py (loguru 版) の configure_logging を使用
logger = get_logger(__name__) #  logger.py (loguru 版) の get_logger を使用


def debug_analyze_persona(page_title):  # 関数化 # 追記
    """
    analyzer.py の人物像分析機能 (analyze_persona) をデバッグする関数 (debug_analyzer.py).

    Args:
        page_title (str): Wikipedia ページタイトル
    """
    logger.info(f"人物像分析デバッグ開始: ページタイトル = {page_title}") #  loguru の logger を使用 # 修正

    try:
        # 1. スクレイピング
        scraper = Scraper(page_title=page_title)
        scraper.fetch_page_data()
        infobox_data = scraper.extract_infobox_data()
        text_data = scraper.extract_text(
            normalize_text=True, remove_exclude_words=True
        )  # テキスト整形 + 除外ワード除去あり
        image_data = scraper.extract_image_data()
        categories = scraper.extract_categories()

        logger.debug("スクレイピングデータ:") #  loguru の logger を使用 # 修正
        logger.debug(f"infobox_data: {infobox_data}") #  loguru の logger を使用 # 修正
        logger.debug(
            f"text_data: [first section heading] {text_data['headings_and_text'][0].get('heading_text', '見出しなし')}, [first section text (一部)] {text_data['headings_and_text'][0]['text_content'][:100]}..."
        ) #  loguru の logger を使用 # 修正
        logger.debug(f"image_data: {image_data}") #  loguru の logger を使用 # 修正
        logger.debug(f"categories: {categories}") #  loguru の logger を使用 # 修正

        # 2. データプロセッサー
        processor = DataProcessor(
            infobox_data=infobox_data,
            text_data=text_data,
            image_data=image_data,
            categories=categories,
            page_title=page_title,
        )
        logger.debug(f"image_dataの内容 (process_data() 呼び出し前): {image_data}") #  loguru logger を使用 # 追加
        processor.process_data()

        logger.debug("データプロセッサー処理後データ:") #  loguru の logger を使用 # 修正
        logger.debug(
            f"df_basic: {processor.df_basic.to_json(orient='records', indent=2, force_ascii=False)}"
        ) #  loguru の logger を使用 # 修正
        logger.debug(
            f"entities: {json.dumps(processor.entities, ensure_ascii=False, indent=2)}"
        ) #  loguru の logger を使用 # 修正
        logger.debug(
            f"relations: {processor.extract_relations()}"
        ) #  loguru の logger を使用 # 修正
        logger.debug(
            f"df_timeline: {processor.df_timeline.to_json(orient='records', indent=2, force_ascii=False)}"
        ) #  loguru の logger を使用 # 修正

        # 3. Analyzer (analyzer.py 実装後に uncomment) # 修正
        # analyzer = Analyzer(wikipedia_url=scraper.wikipedia_url) #  Analyzer オブジェクト作成
        # combined_text_data = processor.concatenate_text_data() # テキストデータ結合
        # ranking = analyzer.analyze_word_frequency(combined_text_data) # 頻度分析
        # persona_keywords = analyzer.extract_persona_keywords(ranking) # 人物像キーワード抽出
        # persona_description = "、".join(persona_keywords)

        # logger.info("\n--- 頻度分析ランキング ---") #  info ログ出力 # 追記
        # for i, (word, count) in enumerate(ranking[:10]): # 上位10件を表示
        #     logger.info(f"{i+1}位: {word} ({count}回)") #  info ログ出力 # 追記

        # logger.info("\n--- 人物像キーワード ---") #  info ログ出力 # 追記
        # logger.info(persona_description) #  info ログ出力 # 追記

        logger.info("\n--- 基本情報 DataFrame (JSON) ---") #  info ログ出力 # 追記
        logger.info(
            processor.df_basic.to_json(
                orient="records", indent=2, force_ascii=False
            )
        ) #  info ログ出力 # 追記

        logger.info("\n--- 固有表現抽出結果 (JSON) ---") #  info ログ出力 # 追記
        logger.info(
            json.dumps(processor.entities, ensure_ascii=False, indent=2)
        ) #  info ログ出力 # 追記

        logger.info("\n--- 人物関係抽出結果 ---") #  info ログ出力 # 追記
        logger.info(processor.extract_relations()) #  info ログ出力 # 追記

        logger.info("\n--- 年表抽出結果 (JSON) ---") #  info ログ出力 # 追記
        logger.info(
            processor.df_timeline.to_json(
                orient="records", indent=2, force_ascii=False
            )
        ) #  info ログ出力 # 追記

        logger.info(f"人物像分析デバッグ完了: ページタイトル = {page_title}") #  loguru の logger を使用 # 修正

    except Exception as e:
        logger.exception(f"人物像分析デバッグ中にエラーが発生しました: {e}") #  loguru の exception() で例外情報を出力 # 修正


if __name__ == "__main__":
    page_title = "アルベルト・アインシュタイン"  # 例: アルベルト・アインシュタイン
    debug_analyze_persona(page_title)  # debug_analyze_persona 関数を実行 # 追記