import json
import os
from datetime import datetime
import re
from core.scraper import Scraper
from utils.logger import configure_logging, get_logger
from config import Config
from core.data_normalizer import DataNormalizer
from core.name_extractor import NameExtractor
from core.data_saver import DataSaver
from core.date_extractor import DateExtractor
from core.data_extractor import DataExtractor

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

                # 追加テーブルデータを抽出
                additional_table_data = scraper.extract_additional_table_data()
                family_info = []
                if "家族" in additional_table_data:
                    family_members = additional_table_data["家族"]
                    for member in family_members:
                        match = re.match(r"(.+)\((.+)\)", member)
                        if match:
                            name, relation = match.groups()
                            family_info.append({
                                '関係': relation,
                                '氏名': name
                            })
                    if '家族構成' not in processed_item or processed_item['家族構成'] is None:
                        processed_item['家族構成'] = []
                    processed_item['家族構成'].extend(family_info)

                # 家族情報がない場合のみテキストを取得して両親の情報を抽出
                if not family_info:
                    sections_data = scraper.extract_text()
                    sections = sections_data.get("sections", [])
                    for section in sections:
                        if isinstance(section, dict):
                            # "category_texts"に"生涯"を含むものと、"heading_text"が"生い立ち"または"幼少時"のものを選択
                            if "生涯" in section.get("category_texts", []) and section.get("heading_text") in ["生い立ち", "幼少時"]:
                                text = section.get("text", "")
                                if text:
                                    parents_info = DataExtractor.extract_parents_info(text)
                                    logger.debug(f"Extracted parents info: {parents_info}")

                                    # 家族構成に両親の情報を追加
                                    if '家族構成' not in processed_item or processed_item['家族構成'] is None:
                                        processed_item['家族構成'] = []

                                    if parents_info['父']:
                                        processed_item['家族構成'].append({
                                            '関係': '父',
                                            '氏名': parents_info['父']
                                        })

                                    if parents_info['母']:
                                        processed_item['家族構成'].append({
                                            '関係': '母',
                                            '氏名': parents_info['母']
                                        })

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
            value = None
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
            elif key == "出身地":
                logger.debug(f"生誕情報: {value}")
                birth_place_info = DataNormalizer.extract_country_from_birth_info(value)
                logger.debug(f"出身地: {birth_place_info}")
                # 出身地情報を辞書としてまとめる
                processed_item["出身地"] = {
                    "出身地_国": birth_place_info["出身地_国"],
                    "出身地_州/王国": birth_place_info["出身地_州/王国"],
                    "出身地_都市": birth_place_info["出身地_都市"]
                }
                continue  # '出身地' キー自体を追加しないようにする
            elif key == "子供":
                logger.debug(f"子供情報: {value}")
                children_info = DataNormalizer.normalize_children_info(value)
                processed_item["子供"] = children_info
                logger.debug(f"整形された子供情報: {children_info}")
                continue  # '子供' キー自体を追加しないようにする
            elif key == "国籍":
                logger.debug(f"国籍情報: {value}")
                nationality_info = DataNormalizer.normalize_nationality_info(value)
                processed_item["国籍"] = nationality_info
                logger.debug(f"整形された国籍情報: {nationality_info}")
                value = nationality_info
            elif key == "分野":
                logger.debug(f"分野情報: {value}")
                field_info = DataNormalizer.normalize_field_info(value)
                processed_item["分野"] = field_info
                logger.debug(f"整形された分野情報: {field_info}")
                continue  # '分野' キー自体を追加しないようにする
            elif key == "主な業績":
                logger.debug(f"主な業績情報: {value}")
                achievements_info = DataNormalizer.normalize_achievements_info(value)
                processed_item["主な業績"] = achievements_info
                logger.debug(f"整形された主な業績情報: {achievements_info}")
                continue  # '主な業績' キー自体を追加しないようにする
            elif key == "受賞歴":
                logger.debug(f"主な受賞歴情報: {value}")
                awards_info = DataNormalizer.normalize_achievements_info(value)
                processed_item["受賞歴"] = awards_info
                logger.debug(f"整形された受賞歴情報: {awards_info}")
                continue  # '主な受賞歴' キー自体を追加しないようにする
            processed_item[key] = value

        # 配偶者情報から家族構成の氏名に一致する場合に結婚年と離婚年を追加
        spouse_info = DataNormalizer.normalize_spouse_info(item.get("配偶者", ""))
        for spouse in spouse_info:
            for family_member in processed_item.get("家族構成", []):
                if family_member["配偶者名"] == spouse["氏名"]:
                    family_member["結婚年"] = spouse["結婚年"]
                    family_member["離婚年"] = spouse["離婚年"]

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