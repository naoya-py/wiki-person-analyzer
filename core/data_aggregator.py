import json
import os
from typing import List
from utils.logger import get_logger

logger = get_logger(__name__)


class DataAggregator:
    @staticmethod
    def save_combined_data(page_titles: List[str], output_filename: str = "combined_data.json",
                            directory: str = "C:/Users/pearj/Desktop/Pycharm/biography_analyzer/data/raw"):
        """
        複数のWikipediaページから抽出したデータを1つのJSONファイルにまとめて保存する。

        Args:
            page_titles (List[str]): Wikipediaページのタイトルのリスト。
            output_filename (str): 出力するJSONファイルの名前。デフォルトは "combined_data.json"。
            directory (str): データを保存するディレクトリのパス。デフォルトは指定されたパス。
        """
        combined_data = []
        # Scraperクラスを動的にインポート
        from core.scraper import Scraper

        for page_title in page_titles:
            scraper = Scraper(page_title=page_title)
            try:
                scraper.fetch_page_data()

                infobox_data = scraper.extract_infobox_data()
                text_data = scraper.extract_text()
                image_data = scraper.extract_image_data()
                categories = scraper.extract_categories()
                additional_table_data = scraper.extract_additional_table_data()

                person_data = {
                    "infobox_data": infobox_data,
                    "text_data": text_data,
                    "image_data": image_data,
                    "categories": categories,
                    "additional_table_data": additional_table_data,
                }

                combined_data.append(person_data)
                logger.info(f"データ収集完了: {page_title}")
            except ValueError as e:
                logger.error(f"{page_title}のデータ収集中にエラーが発生しました: {e}")

        # ディレクトリが存在しない場合は作成
        os.makedirs(directory, exist_ok=True)
        output_path = os.path.join(directory, output_filename)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=2)
        logger.info(f"全データを{output_path}に保存しました")