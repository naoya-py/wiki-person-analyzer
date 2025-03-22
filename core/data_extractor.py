import re
from datetime import datetime
from core.data_normalizer import DataNormalizer
from utils.logger import get_logger
from typing import Dict, Optional, List

logger = get_logger(__name__)


class DataExtractor:
    """
    生年月日および没年月日を抽出してフォーマットするクラス。
    """

    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """
        テキストを句点（。）、終端文字（？、！）で分割する。

        Args:
            text (str): 対象のテキスト。

        Returns:
            List[str]: 分割された文のリスト。
        """
        sentence_endings = re.compile(r'(?<=[。？！])\s*')
        sentences = sentence_endings.split(text)
        logger.debug(f"Split text into sentences: {sentences}")
        return sentences

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

        # 文単位に分割
        sentences = DataExtractor.split_into_sentences(text)

        father_pattern = re.compile(r'(父\s*(?P<father1>[^\s、。]+))|(?P<father2>[\w・ー]+)\s*を父')
        mother_pattern = re.compile(r'(母\s*(?P<mother1>[^\s、。]+))|(?P<mother2>[\w・ー]+)\s*を母')

        father_name = None
        mother_name = None

        for sentence in sentences:
            logger.debug(f"Processing sentence: {sentence}")
            if not father_name:
                father_match = father_pattern.search(sentence)
                if father_match:
                    father_name = father_match.group('father1') if father_match.group(
                        'father1') else father_match.group('father2')

            if not mother_name:
                mother_match = mother_pattern.search(sentence)
                if mother_match:
                    mother_name = mother_match.group('mother1') if mother_match.group(
                        'mother1') else mother_match.group('mother2')
                    # Remove any trailing text after the mother's name
                    mother_name = re.sub(r'も.*$', '', mother_name)

            if father_name and mother_name:
                break

        return {
            '父': father_name,
            '母': mother_name
        }


# テスト例
if __name__ == "__main__":
    example_text = "生誕時の名前はマリア・サロメア・スクウォドフスカスクロドフスカ 、 Maria Salomea Skłodowska 。 父 ヴワディスワフ・スクウォドフスキ 。母ブロニスワヴァ・ボグスカも下級貴族階級出身で、..."
    result = DataExtractor.extract_parents_info(example_text)
    print(result)  # {'父': 'ヴワディスワフ・スクウォドフスキ', '母': 'ブロニスワヴァ・ボグスカ'}

    example_text2 = "アインシュタインは1879年3月14日、 ヘルマン・アインシュタイン を父、 パウリーネ・コッホ を母とし、その長男としてドイツ南西部の..."
    result2 = DataExtractor.extract_parents_info(example_text2)
    print(result2)  # {'父': 'ヘルマン・アインシュタイン', '母': 'パウリーネ・コッホ'}