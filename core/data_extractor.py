import re
from datetime import datetime
from core.data_normalizer import DataNormalizer
from utils.logger import get_logger
from typing import Dict, Optional

logger = get_logger(__name__)


class DataExtractor:
    """
    生年月日および没年月日を抽出してフォーマットするクラス。
    """

    @staticmethod
    def extract_parents_info(text: str) -> Dict[str, Optional[str]]:
        """
        テキストから父と母の情報を抽出する。

        Args:
            text (str): 対象のテキスト。

        Returns:
            Dict[str, Optional[str]]: 抽出された父と母の情報。
        """
        logger.debug(f"Extracting parents info from text: {text}")
        father_pattern = re.compile(r'(?P<father>[\w・ー]+)\s*を父')
        mother_pattern = re.compile(r'(?P<mother>[\w・ー]+)\s*を母')

        father_match = father_pattern.search(text)
        mother_match = mother_pattern.search(text)

        father_name = father_match.group('father') if father_match else None
        mother_name = mother_match.group('mother') if mother_match else None

        return {
            '父': father_name,
            '母': mother_name
        }


# テスト例
if __name__ == "__main__":
    example_text = "アインシュタインは1879年3月14日、 ヘルマン・アインシュタイン を父、 パウリーネ・コッホ を母とし、その長男としてドイツ南西部の..."
    result = DataExtractor.extract_parents_info(example_text)
    print(result)