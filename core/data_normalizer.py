import re
import dateparser
from utils.logger import get_logger

logger = get_logger(__name__)

class DataNormalizer:
    """
    和暦から西暦への変換、地名の表記統一、職業・分野のカテゴリ統一、および欠損値の取り扱いを行うクラス。
    """

    @staticmethod
    def normalize_date(date_str: str) -> str:
        """
        日付を標準形式 (YYYY-MM-DD) に変換する。
        """
        if not date_str or date_str == "不明":
            return "不明"

        # 和暦から西暦への変換
        date_str = DataNormalizer.convert_japanese_era_to_gregorian(date_str)

        # 日付形式の正規化
        parsed_date = dateparser.parse(date_str, settings={'DATE_ORDER': 'YMD'})
        if parsed_date:
            return parsed_date.strftime("%Y-%m-%d")

        return "不明"

    @staticmethod
    def convert_japanese_era_to_gregorian(date_str: str) -> str:
        """
        和暦を西暦に変換する。
        """
        eras = {
            "令和": 2019,
            "平成": 1989,
            "昭和": 1926,
            "大正": 1912,
            "明治": 1868
        }
        for era, start_year in eras.items():
            match = re.match(rf"{era}(\d+)年(\d+)?月?(\d+)?日?", date_str)
            if match:
                year, month, day = match.groups()
                year = start_year + int(year) - 1
                month = month if month else "01"
                day = day if day else "01"
                return f"{year}年{month}月{day}日"
        return date_str

    @staticmethod
    def standardize_location(location_str: str) -> str:
        """
        地名の表記を統一する。
        """
        location_mapping = {
            "東京": "東京都",
            "大阪": "大阪府",
            # 他の地名のマッピングをここに追加
        }
        return location_mapping.get(location_str, location_str)

    @staticmethod
    def standardize_field(field_str: str) -> str:
        """
        職業・分野のカテゴリを統一する。
        """
        field_mapping = {
            "物理学": "科学",
            "化学": "科学",
            "文学": "人文科学",
            # 他の分野のマッピングをここに追加
        }
        return field_mapping.get(field_str, field_str)

    @staticmethod
    def handle_missing_value(value: str) -> str:
        """
        欠損値を「不明」に統一する。
        """
        return value if value else "不明"

    @staticmethod
    def extract_country_from_birth_info(birth_info: str) -> str:
        """
        生誕情報から国名を抽出するメソッド。
        """
        logger.debug(f"生誕情報: {birth_info}")

        # 国名リスト（必要に応じて追加）
        country_list = [
            "ドイツ帝国", "フランス共和国", "アメリカ合衆国", "日本", "イギリス", "カナダ", "中国",
            "ロシア", "インド", "ブラジル", "オーストラリア", "イタリア", "スペイン", "韓国",
            "ポーランド立憲王国", "ヴュルテンベルク王国"
        ]

        for country in country_list:
            if country in birth_info:
                logger.debug(f"抽出された国名: {country}")
                return country

        logger.debug("国名が見つかりませんでした。")
        return "不明"

    @staticmethod
    def normalize_nationality_info(nationality_info: str) -> list:
        """
        国籍情報を期間ごとに分割し、適切な形式に整えるメソッド。
        """
        logger.debug(f"国籍情報: {nationality_info}")

        # 正規表現を使用して国籍情報を抽出
        pattern_with_period = re.compile(r"((?:[^\d\s]+(?:\s[^\d\s]+)*)+?)\s(\d{4})-(\d{2,4})")
        pattern_without_period = re.compile(r"([^\d\s]+(?:\s[^\d\s]+)*)")

        matches_with_period = pattern_with_period.findall(nationality_info)
        matches_without_period = pattern_without_period.findall(nationality_info)

        normalized_nationality = []

        for match in matches_with_period:
            countries, start_year, end_year = match
            countries_list = countries.split()
            if len(end_year) == 2:
                end_year = str(int(start_year[:2]) * 100 + int(end_year))
            normalized_nationality.append({
                "国籍": countries_list,
                "開始年": int(start_year),
                "終了年": int(end_year)
            })

        # 期間情報がない場合の処理
        if not matches_with_period:
            countries_list = [country for country in matches_without_period]
            normalized_nationality.append({
                "国籍": countries_list
            })

        logger.debug(f"整形された国籍情報: {normalized_nationality}")
        return normalized_nationality