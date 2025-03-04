from core.scraper import Scraper
import json
from utils.logger import configure_logging, get_logger, print_exception
import logging
import sys
from core.analyzer import wakati_text

def debug_scraper(page_title):
    """
    Scraperクラスのデバッグ用スクリプト。
    指定されたWikipediaページから各種データを抽出し、JSON形式で出力する。
    基本情報、本文と見出し（正規化ON/OFF）、画像データ、カテゴリを抽出。

    Args:
        page_title (str): デバッグ対象のWikipediaページタイトル
    """
    configure_logging(level=logging.DEBUG, stream=sys.stdout)
    logger = get_logger(__name__)
    logger.info(f"デバッグ開始: ページタイトル = {page_title}")

    try:
        scraper = Scraper(page_title=page_title)
        scraper.fetch_page_data()

        print(f"\n--- ページタイトル: {page_title} ---")

        # 基本情報抽出
        print("\n--- 基本情報 (Infobox) ---")
        infobox_data = scraper.extract_infobox_data()
        print(json.dumps(infobox_data, ensure_ascii=False, indent=2))

        # 本文と見出し抽出 (キーワード抽出・頻度分析用 前処理 + 分かち書き + 正規化ON, 不要ワード削除ON) #  見出し変更
        print("\n--- 本文と見出し (キーワード抽出・頻度分析用 前処理 + 分かち書き + 正規化ON, 不要ワード削除ON) ---") #  見出し変更
        text_data_keyword = scraper.extract_text(normalize_text=True, remove_exclude_words=True, lowercase=True, remove_punctuation=True, remove_numbers=True, stopwords=stopwords_list) #  オプション引数、ストップワードリスト を指定

        # 分かち書き処理を適用
        wakati_headings_and_text = []
        for section in text_data_keyword["headings_and_text"]:
            wakati_headings_and_text.append({
                "heading_level": section["heading_level"],
                "heading_text": wakati_text(section["heading_text"]), #  見出しを分かち書き
                "text_content": wakati_text(section["text_content"]), #  本文を分かち書き
                "sub_sections": [{
                    "heading_level": sub_section["heading_level"],
                    "heading_text": wakati_text(sub_section["heading_text"]), #  sub_section の見出しを分かち書き
                    "text_content": wakati_text(sub_section["text_content"]), #  sub_section の本文を分かち書き
                    "sub_sections": [] #  h4 より下層の sub_sections はないため空リスト
                } for sub_section in section["sub_sections"]] #  sub_sections に対しても分かち書き処理を適用
            })
        text_data_keyword["headings_and_text"] = wakati_headings_and_text #  分かち書き後のリストで更新

        print(json.dumps(text_data_keyword, ensure_ascii=False, indent=2))

        # 本文と見出し抽出 (正規化OFF, 不要ワード削除OFF)
        print("\n--- 本文と見出し (正規化OFF, 不要ワード削除OFF) ---")
        text_data_raw = scraper.extract_text(normalize_text=False, remove_exclude_words=False)
        print(json.dumps(text_data_raw, ensure_ascii=False, indent=2))

        # 画像データ抽出
        print("\n--- 画像データ (URL, altテキスト) ---")
        image_data = scraper.extract_image_data()
        print(json.dumps(image_data, ensure_ascii=False, indent=2))

        # カテゴリ抽出
        print("\n--- カテゴリ ---")
        categories = scraper.extract_categories()
        print(json.dumps(categories, ensure_ascii=False, indent=2))

        logger.info(f"デバッグ完了: ページタイトル = {page_title}")


    except ValueError as e:
        print_exception(e)
    except TypeError as e:
        print_exception(e)
    except Exception as e:
        print_exception(e)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python debug_scraper.py <Wikipediaページタイトル>")
        sys.exit(1)

    page_title = sys.argv[1]

    # ストップワードリスト (例: 日本語 Wikipedia 用) # ストップワードリストを定義
    stopwords_list = [
        "の", "に", "は", "へ", "と", "て", "で", "も", "が", "や", "ください", "こと", "です", "ます", "でしょう", "ください", "する", "なる", "ある", "いる", "れる", "られる", "言う", "こと", "もの", "http", "https", "co", "jp", "www" #  例:  汎用的なストップワード、URL関連のワードを追加
    ]  #  必要に応じてリストを調整

    debug_scraper(page_title, stopwords_list) # ストップワードリストを debug_scraper に渡す