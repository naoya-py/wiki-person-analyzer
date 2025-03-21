import re
from datetime import datetime
from core.data_normalizer import DataNormalizer
from utils.logger import get_logger

logger = get_logger(__name__)


class DateExtractor:
    """
    生年月日および没年月日を抽出してフォーマットするクラス。
    """

    @staticmethod
    def extract_and_format_birth_date(value: str) -> dict:
        """
        生年月日を抽出してフォーマットする。
        """
        logger.debug(f"Original birth date value: {value}")
        date_regex = r"(\d{4}年\s*\d{1,2}月\s*\d{1,2}日)"
        match = re.search(date_regex, value)
        if match:
            date_str = match.group(1)
            normalized_date = DataNormalizer.normalize_date(date_str)
            logger.debug(f"Normalized birth date: {normalized_date}")
            if normalized_date:
                year, month, day = normalized_date.split('-')
                return {
                    "生年月日": {
                        "年": year,
                        "月": month,
                        "日": day,
                        "全体": normalized_date
                    }
                }
        return {
            "生年月日": {
                "年": "不明",
                "月": "不明",
                "日": "不明",
                "全体": "不明"
            }
        }

    @staticmethod
    def extract_and_format_death_date(value: str) -> dict:
        """
        没年月日を抽出してフォーマットする。
        """
        logger.debug(f"Original death date value: {value}")
        date_regex = r"(\d{4}年\s*\d{1,2}月\s*\d{1,2}日)"
        match = re.search(date_regex, value)
        if match:
            date_str = match.group(1)
            normalized_date = DataNormalizer.normalize_date(date_str)
            logger.debug(f"Normalized death date: {normalized_date}")
            if normalized_date:
                year, month, day = normalized_date.split('-')
                return {
                    "没年月日": {
                        "年": year,
                        "月": month,
                        "日": day,
                        "全体": normalized_date
                    }
                }
        return {
            "没年月日": {
                "年": "不明",
                "月": "不明",
                "日": "不明",
                "全体": "不明"
            }
        }

    @staticmethod
    def calculate_age_at_death(birth_date: str, death_date: str) -> str:
        """
        生年月日と没年月日から死亡年齢を計算する。
        """
        logger.debug(f"Calculating age at death with birth_date: {birth_date} and death_date: {death_date}")
        if birth_date == "不明" or death_date == "不明":
            return "不明"

        birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d")
        death_date_obj = datetime.strptime(death_date, "%Y-%m-%d")

        age_at_death = death_date_obj.year - birth_date_obj.year - (
                    (death_date_obj.month, death_date_obj.day) < (birth_date_obj.month, birth_date_obj.day))

        logger.debug(f"Calculated age at death: {age_at_death}")
        return str(age_at_death)