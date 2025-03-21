import json
import os
from datetime import datetime
from core.scraper import Scraper
from utils.logger import configure_logging, get_logger
from config import Config
from core.data_normalizer import DataNormalizer
from core.name_extractor import NameExtractor
from core.data_saver import DataSaver
from core.date_extractor import DateExtractor

configure_logging(level=Config.DEFAULT_LOG_LEVEL)
logger = get_logger(__name__)

class DataProcessor:
    """
    偉人情報のデータセットを作成するクラス。
    """

    def __init__(self):
        self.data = []
        self.logger = get_logger(__name__)

    def process_data(self, page_titles):
        """
        ページタイトルリストに基づいてデータを処理し、偉人情報のデータセットを作成する。
        """
        for page_title in page_titles:
            scraper = Scraper(page_title=page_title)
            try:
                scraper.fetch_page_data()
                infobox_data = scraper.extract_infobox_data()
                logger.debug(f"Extracted infobox data: {infobox_data}")
                processed_item = self._extract_and_format_data(infobox_data)
                logger.debug(f"Processed item: {processed_item}")
                self.data.append(processed_item)
                self.logger.info(f"Processed data for {page_title}")
            except ValueError as e:
                self.logger.error(f"Error processing {page_title}: {e}")

        DataSaver.save_data(self.data, "infobox")

    def _extract_and_format_data(self, item):
        """
        生データから必要な情報を抽出し、形式を整える。
        """
        processed_item = {}
        birth_date_info = {}
        death_date_info = {}

        for key in Config.GENERAL_KEYS:
            mapped_keys = Config.key_map.get(key, [key])
            value = "不明"
            for mapped_key in mapped_keys:
                if mapped_key in item:
                    value = item[mapped_key]
                    break

            if key == "氏名":
                value = NameExtractor.extract_japanese_name(value)
            elif key == "生年月日":
                birth_date_info = DateExtractor.extract_and_format_birth_date(value)
                logger.debug(f"Extracted birth date info: {birth_date_info}")
                processed_item.update(birth_date_info)
                value = birth_date_info["生年月日"]["全体"]
            elif key == "没年月日":
                death_date_info = DateExtractor.extract_and_format_death_date(value)
                logger.debug(f"Extracted death date info: {death_date_info}")
                processed_item.update(death_date_info)
                value = death_date_info["没年月日"]["全体"]
            elif key == "出生地":
                logger.debug(f"生誕情報: {value}")
                birth_place = DataNormalizer.extract_country_from_birth_info(value)
                processed_item["出生地"] = birth_place
                logger.debug(f"出生地: {birth_place}")
                value = birth_place
            elif key == "国籍":
                logger.debug(f"国籍情報: {value}")
                nationality_info = DataNormalizer.normalize_nationality_info(value)
                processed_item["国籍"] = nationality_info
                logger.debug(f"整形された国籍情報: {nationality_info}")
            elif key in ["出生地", "出身地"]:
                value = DataNormalizer.standardize_location(value)
            elif key == "分野":
                value = DataNormalizer.standardize_field(value)
            else:
                value = DataNormalizer.handle_missing_value(value)
            processed_item[key] = value

        # Calculate age at death
        if "生年月日" in birth_date_info and "没年月日" in death_date_info:
            birth_date = birth_date_info["生年月日"]["全体"]
            death_date = death_date_info["没年月日"]["全体"]
            processed_item["死亡年齢"] = DateExtractor.calculate_age_at_death(birth_date, death_date)
            logger.debug(f"Calculated age at death: {processed_item['死亡年齢']}")

        # Ensure detailed date information is included in the final processed item
        if birth_date_info:
            processed_item.update(birth_date_info)
        if death_date_info:
            processed_item.update(death_date_info)

        return processed_item

# 使用例
if __name__ == "__main__":
    processor = DataProcessor()
    page_titles = [
        "アルベルト・アインシュタイン",
        "マリ・キュリー",
        # 他のページタイトルを追加
    ]
    processor.process_data(page_titles)