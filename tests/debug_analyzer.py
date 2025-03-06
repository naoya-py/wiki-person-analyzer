from core.data_processor import DataProcessor
from core.scraper import Scraper
from utils.logger import configure_logging, get_logger
import logging
import sys
import json
import os
from pathlib import Path
import importlib
import core.data_processor

importlib.reload(core.data_processor)
configure_logging(level=logging.DEBUG, stream=sys.stdout)
logger = get_logger(__name__)

# データ保存用ディレクトリ
DATA_DIR = "data"

def create_data_directory():
    """データ保存用ディレクトリを作成する。"""
    data_dir_path = Path(DATA_DIR)
    if not data_dir_path.exists():
        data_dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"データディレクトリを作成しました: {DATA_DIR}")
    else:
        logger.info(f"データディレクトリは既に存在します: {DATA_DIR}")


def debug_analyze_persona(page_title):
    """
    人物像分析のデバッグ用関数。
    指定されたページタイトルの人物像分析を行い、結果をログとJSONファイルに出力する。

    Args:
        page_title (str): Wikipediaのページタイトル
    """
    logger.info(f"人物像分析デバッグ開始: {page_title}")

    try:
        # DataProcessorの初期化 (page_titleのみを渡す)  # 修正:  page_title のみ
        processor = DataProcessor(page_title=page_title)

        # データ取得と処理を実行
        processor.fetch_data() #  fetch_data() を実行 # 修正
        processor.process_data()

        # 分析結果を取得
        analysis_results = processor.analyze_persona()
        formatted_results = processor.format_analysis_results(analysis_results)

        logger.info(f"人物像分析結果:\n{formatted_results}")

        # JSONファイルに結果を保存
        output_file = Path(DATA_DIR) / f"persona_analysis_{page_title}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False)
        logger.info(f"分析結果をJSONファイルに保存しました: {output_file}")

    except ValueError as ve:
        logger.error(f"ValueError: {ve}")
        logger.error(f"人物像分析デバッグ中にエラーが発生しました: {ve}") #  エラーメッセージを修正
    except Exception as e:
        logger.exception(f"予期せぬエラーが発生しました: {e}")
        logger.error(f"人物像分析デバッグ中にエラーが発生しました: {e}") #  エラーメッセージを修正
    finally:
        logger.info(f"人物像分析デバッグ終了: {page_title}")


def debug_create_basic_info_dataframe(page_title):
    """
    基本情報DataFrame作成デバッグ用関数。

    Args:
        page_title (str): Wikipediaのページタイトル
    """
    logger.info(f"基本情報DataFrame作成デバッグ開始: {page_title}")
    try:
        scraper = Scraper(page_title=page_title)
        scraper.fetch_page_data()
        infobox_data = scraper.extract_infobox_data()
        image_data = scraper.extract_image_data()
        categories = scraper.extract_categories()
        text_data = scraper.extract_text() #  text_data を取得 # 追記

        # DataProcessor を初期化 (page_title のみ) # 修正: page_title のみ
        processor = DataProcessor(page_title=page_title)
        processor.infobox_data = infobox_data #  データ属性に値を設定 # 追記
        processor.image_data = image_data #  データ属性に値を設定 # 追記
        processor.categories = categories #  データ属性に値を設定 # 追記
        processor.text_data = text_data #  データ属性に値を設定 # 追記


        df_basic = processor.create_basic_info_dataframe()

        logger.info(f"基本情報DataFrame:\n{df_basic.to_string()}")

        # JSONファイルにDataFrameを保存
        output_file = Path(DATA_DIR) / f"basic_info_dataframe_{page_title}.json"
        df_basic.to_json(output_file, orient="records", indent=2, force_ascii=False)
        logger.info(f"基本情報DataFrameをJSONファイルに保存しました: {output_file}")

    except Exception as e:
        logger.exception(f"基本情報DataFrame作成中にエラーが発生しました: {e}")
    finally:
        logger.info(f"基本情報DataFrame作成デバッグ終了: {page_title}")


def debug_extract_timeline(page_title):
    """
    年表抽出デバッグ用関数 (headings_and_text 出力)。

    Args:
        page_title (str): Wikipediaのページタイトル
    """
    logger.info(f"年表抽出デバッグ開始 (headings_and_text 出力): {page_title}") #  ログメッセージを修正
    try:
        scraper = Scraper(page_title=page_title)
        scraper.fetch_page_data()
        text_data = scraper.extract_text(normalize_text=True, remove_exclude_words=True)

        # DataProcessor を初期化 (scraper オブジェクトを渡す)
        processor = DataProcessor(page_title=page_title)
        processor.text_data = text_data #  text_data を設定 # 追記
        processor.process_data() # process_data() を実行して headings_and_text を生成

        #  headings_and_text の内容をログ出力 # 追記
        logger.info("headings_and_text の内容:") # 追記
        for heading, text in processor.headings_and_text.items(): # 追記
            logger.info(f"見出し: {heading}") # 追記
            logger.info(f"テキスト: {text[:200]}...") #  先頭 200 文字だけ出力 # 追記

        df_timeline = processor.extract_timeline() #  年表抽出関数は一旦コメントアウト

        logger.info(f"年表DataFrame:\n{df_timeline.to_string()}") #  年表 DataFrame のログ出力も一旦コメントアウト

        # JSONファイルにDataFrameを保存 (一旦コメントアウト)
        # output_file = Path(DATA_DIR) / f"timeline_dataframe_{page_title}.json"
        # df_timeline.to_json(output_file, orient="records", indent=2, force_ascii=False)
        # logger.info(f"年表DataFrameをJSONファイルに保存しました: {output_file}")

    except Exception as e:
        logger.exception(f"年表抽出中にエラーが発生しました: {e}")
    finally:
        logger.info(f"年表抽出デバッグ終了 (headings_and_text 出力): {page_title}") #  ログメッセージを修正


def debug_extract_entities(page_title):
    """
    固有表現抽出デバッグ用関数。

    Args:
        page_title (str): Wikipediaのページタイトル
    """
    logger.info(f"固有表現抽出デバッグ開始: {page_title}")
    try:
        scraper = Scraper(page_title=page_title)
        scraper.fetch_page_data()
        text_data = scraper.extract_text(normalize_text=True, remove_exclude_words=True)

        # DataProcessor を初期化 (page_title のみ) # 修正: page_title のみ
        processor = DataProcessor(page_title=page_title)
        processor.text_data = text_data #  text_data を設定 # 追記


        entities = processor.extract_entities()

        logger.info(f"固有表現抽出結果:\n{json.dumps(entities, ensure_ascii=False, indent=2)}")

        # JSONファイルに結果を保存
        output_file = Path(DATA_DIR) / f"entities_{page_title}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(entities, f, indent=2, ensure_ascii=False)
        logger.info(f"固有表現抽出結果をJSONファイルに保存しました: {output_file}")


    except Exception as e:
        logger.exception(f"固有表現抽出中にエラーが発生しました: {e}")
    finally:
        logger.info(f"固有表現抽出デバッグ終了: {page_title}")


def debug_extract_relations(page_title):
    """
    人物関係抽出デバッグ用関数。

    Args:
        page_title (str): Wikipediaのページタイトル
    """
    logger.info(f"人物関係抽出デバッグ開始: {page_title}")
    try:
        scraper = Scraper(page_title=page_title)
        scraper.fetch_page_data()
        text_data = scraper.extract_text(normalize_text=True, remove_exclude_words=True)
        infobox_data = scraper.extract_infobox_data() #  infobox_data を取得 # 追記
        image_data = scraper.extract_image_data() #  image_data を取得 # 追記
        categories = scraper.extract_categories() #  categories を取得 # 追記

        # DataProcessor を初期化 (page_title のみ) # 修正: page_title のみ
        processor = DataProcessor(page_title=page_title)
        processor.text_data = text_data #  text_data を設定 # 追記
        processor.infobox_data = infobox_data #  infobox_data を設定 # 追記
        processor.image_data = image_data #  image_data を設定 # 追記
        processor.categories = categories #  categories を設定 # 追記
        processor.process_data() #  process_data() を実行 # 追記


        relations = processor.extract_relations()

        logger.info(f"人物関係抽出結果:\n{relations}") #  JSON 形式ではなくそのまま表示

        # JSONファイルに結果を保存
        output_file = Path(DATA_DIR) / f"relations_{page_title}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(relations, f, indent=2, ensure_ascii=False)
        logger.info(f"人物関係抽出結果をJSONファイルに保存しました: {output_file}")

    except Exception as e:
        logger.exception(f"人物関係抽出中にエラーが発生しました: {e}")
    finally:
        logger.info(f"人物関係抽出デバッグ終了: {page_title}")


if __name__ == "__main__":
    page_title = "スティーブ・ジョブズ"

    create_data_directory()

    # debug_analyze_persona(page_title)  # debug_analyze_persona 関数を実行 # 追記
    # debug_create_basic_info_dataframe(page_title) # debug_create_basic_info_dataframe 関数を実行 # 追記
    debug_extract_timeline(page_title) # debug_extract_timeline 関数を実行 # 追記
    # debug_extract_entities(page_title) # debug_extract_entities 関数を実行 # 追記
    # debug_extract_relations(page_title) # debug_extract_relations 関数を実行 # 追記