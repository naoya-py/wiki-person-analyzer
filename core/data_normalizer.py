import re
import dateparser
from typing import Optional, List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class DataNormalizer:
    """
    和暦から西暦への変換、地名の表記統一、職業・分野のカテゴリ統一、および欠損値の取り扱いを行うクラス。
    """

    @staticmethod
    def normalize_date(date_str: str) -> Optional[str]:
        """
        日付を標準形式 (YYYY-MM-DD) に変換する。
        """
        if not date_str or date_str == "不明":
            return None

        # 和暦から西暦への変換
        date_str = DataNormalizer.convert_japanese_era_to_gregorian(date_str)

        # 日付形式の正規化
        parsed_date = dateparser.parse(date_str, settings={'DATE_ORDER': 'YMD'})
        if parsed_date:
            return parsed_date.strftime("%Y-%m-%d")

        return None

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
    def handle_missing_value(value: Optional[str]) -> Optional[str]:
        """
        欠損値を`null`に統一する。
        """
        return value if value else None

    @staticmethod
    def extract_country_from_birth_info(birth_info: str) -> Dict[str, Optional[str]]:
        """
        生誕情報から国名、州/王国、都市名を抽出するメソッド。
        """
        logger.debug(f"生誕情報: {birth_info}")

        # 国名のリスト（必要に応じて追加）
        known_countries = [
            "アメリカ合衆国", "ドイツ帝国", "ポーランド立憲王国", "フランス共和国", "日本", "イギリス", "カナダ",
            "中国", "ロシア", "インド", "ブラジル", "オーストラリア", "イタリア", "スペイン", "韓国"
        ]

        # 国名を抽出する正規表現パターン
        country_pattern = re.compile(r"(" + "|".join(known_countries) + r")")

        country_match = country_pattern.search(birth_info)
        result: Dict[str, Optional[str]] = {
            "出身地_国": None,
            "出身地_州/王国": None,
            "出身地_都市": None
        }

        if country_match:
            country = country_match.group(0)
            remaining_info = birth_info[country_match.end():].strip()

            # 不要な記号を削除
            remaining_info = re.sub(r"^[・、]", "", remaining_info)

            # 州/王国と都市を抽出するための正規表現パターン
            if "アメリカ合衆国" in country:
                state_city_pattern = re.compile(r"([^\d\s]+州)\s*([^\d\s]+)$")
            else:
                state_city_pattern = re.compile(r"([^\d\s]+王国)?\s*([^\d\s]+)$")

            state_city_match = state_city_pattern.search(remaining_info)

            if state_city_match:
                state_or_kingdom = state_city_match.group(1) if state_city_match.group(1) else None
                city = state_city_match.group(2)

                result["出身地_国"] = country
                result["出身地_州/王国"] = state_or_kingdom
                result["出身地_都市"] = city

        logger.debug(f"抽出された国名、州/王国、および都市名: {result}")
        return result

    @staticmethod
    def normalize_nationality_info(nationality_info: str) -> List[Dict[str, Any]]:
        """
        国籍情報を期間ごとに分割し、適切な形式に整えるメソッド。
        """
        logger.debug(f"国籍情報: {nationality_info}")

        # 正規表現を使用して国籍情報を抽出
        pattern_with_period = re.compile(r"((?:[^\d\s]+(?:\s[^\d\s]+)*)+?)\s(\d{4})-(\d{2,4})")
        pattern_without_period = re.compile(r"([^\d\s]+(?:\s[^\d\s]+)*)")

        matches_with_period = pattern_with_period.findall(nationality_info)
        matches_without_period = pattern_without_period.findall(nationality_info)

        normalized_nationality: List[Dict[str, Any]] = []

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

    @staticmethod
    def normalize_children_info(children_info: str) -> List[Dict[str, Optional[Any]]]:
        """
        子供情報を分割し、名前と年号を抽出するメソッド。
        """
        logger.debug(f"子供情報: {children_info}")

        children_entries = re.split(r'\s+(?=\D)', children_info)
        normalized_children: List[Dict[str, Optional[Any]]] = []

        for entry in children_entries:
            child_name = re.search(r'^[^\d\s]+', entry)
            birth_death_years = re.findall(r'\d{4}', entry)
            death_year_uncertain = '?' in entry

            child_dict = {
                '子供名': child_name.group(0) if child_name else None,
                '出生年': int(birth_death_years[0]) if birth_death_years else None,
                '死亡年': int(birth_death_years[1]) if len(birth_death_years) > 1 else None,
                '死亡年不確か': death_year_uncertain
            }
            normalized_children.append(child_dict)

        logger.debug(f"整形された子供情報: {normalized_children}")
        return normalized_children

    @staticmethod
    def normalize_field_info(field_info: str) -> List[str]:
        """
        分野情報をリスト形式に変換する。

        Args:
            field_info (str): 分野情報の文字列。

        Returns:
            List[str]: リスト形式に変換された分野情報。
        """
        # "・"や空白で区切られた分野情報をリストに変換
        fields = re.split(r'[・\s]+', field_info)
        return [field.strip() for field in fields if field.strip()]

    @staticmethod
    def normalize_achievements_info(achievements_info: str) -> List[Dict[str, Any]]:
        """
        主な業績情報をリスト形式に変換する。

        Args:
            achievements_info (str): 主な業績情報の文字列。

        Returns:
            List[Dict[str, Any]]: リスト形式に変換された主な業績情報。
        """
        # 正規表現を使用して賞と年を抽出
        pattern = re.compile(r"(\D+?)\s+(\d{4})年?")
        achievements_list = [{"賞": match[0].strip(), "年": int(match[1])} for match in pattern.findall(achievements_info)]
        return achievements_list


# テストコード
if __name__ == "__main__":
    test_cases = [
        "アメリカ合衆国カリフォルニア州パロアルト",
        "ポーランド立憲王国・ワルシャワ",
        "ドイツ帝国ヴュルテンベルク王国ウルム"
    ]
    for birth_info in test_cases:
        result = DataNormalizer.extract_country_from_birth_info(birth_info)
        print(result)

    spouse_test_cases = [
        "ミレヴァ・マリッチ 1903-1919 エルザ・レーベンタール 1919-1936",
        "ピエール・キュリー 1895年結婚"
    ]
    for spouse_info in spouse_test_cases:
        result = DataNormalizer.normalize_spouse_info(spouse_info)  # type: ignore
        print(result)

    children_test_cases = [
        "リーゼル 1902-1903? ハンス・アルベルト 1904-1973 エドゥアルト 1910-1965",
        "イレーヌ・ジョリオキュリー エーヴ・キュリー"
    ]
    for children_info in children_test_cases:
        result = DataNormalizer.normalize_children_info(children_info)  # type: ignore
        print(result)

    achievements_test_case_1 = "放射能 の研究 ラジウム の発見 ポロニウム の発見"
    achievements_test_case_2 = "一般相対性理論 特殊相対性理論 光電効果 ブラウン運動 質量とエネルギーの等価性 アインシュタイン方程式 ボース分布 ノーベル物理学賞 1903年 ノーベル化学賞 1911年"

    result_1 = DataNormalizer.normalize_achievements_info(achievements_test_case_1)
    result_2 = DataNormalizer.normalize_achievements_info(achievements_test_case_2)
    print(result_1)
    print(result_2)