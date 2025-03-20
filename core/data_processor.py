import json
from scraper import Scraper
from datetime import datetime
import re
import dateparser
from utils.logger import configure_logging, get_logger
from config import Config

# ログ設定を初期化
configure_logging(level=Config.DEFAULT_LOG_LEVEL)
logger = get_logger(__name__)

class DataProcessor:
    def __init__(self, page_titles):
        self.page_titles = page_titles

    def extract_information(self, page_title: str):
        logger.info(f"開始: {page_title} の情報を抽出")
        scraper = Scraper(page_title=page_title)
        try:
            scraper.fetch_page_data()
        except ValueError as e:
            logger.error(f"スクレイピング中にエラーが発生しました: {e}")
            return None

        raw_infobox_data = scraper.extract_infobox_data()
        infobox_data = self.extract_infobox_data(raw_infobox_data)
        text_data = scraper.extract_text()
        sections = text_data.get("sections", [])

        death_year = infobox_data.get("死没", {}).get("年", None)
        information = {
            "氏名": infobox_data.get("氏名", page_title),
            "本名": infobox_data.get("本名", ""),
            "生年月日": infobox_data.get("生年月日", {}),
            "出身地": infobox_data.get("出身地", ""),
            "死没": infobox_data.get("死没", {}),
            "業績": self.extract_achievements(sections, infobox_data.get("生年月日", {}).get("生年月日", ""), death_year)
        }

        logger.info(f"完了: {page_title} の情報を抽出")
        return information

    def extract_infobox_data(self, raw_infobox_data: dict) -> dict:
        """
        Infoboxデータを詳細に分類し、辞書形式で返します。

        Args:
            raw_infobox_data (dict): 生のInfoboxデータ。

        Returns:
            dict: 詳細に分類されたInfoboxデータ。
        """
        birth_date_info = self.extract_birth_date(raw_infobox_data)
        death_date_info = self.extract_death_date(raw_infobox_data, birth_date_info.get("年", None))

        infobox_data = {
            "氏名": self.extract_name(raw_infobox_data.get("名前", "")),
            "本名": self.extract_full_name(raw_infobox_data.get("名前", "")),
            "生年月日": birth_date_info,
            "出身地": self.extract_birth_place(raw_infobox_data),
            "死没": death_date_info,
            "居住": raw_infobox_data.get("居住", "").split(),
            "国籍": raw_infobox_data.get("国籍", "").split(),
            "研究分野": raw_infobox_data.get("研究分野", "").split(),
            "研究機関": raw_infobox_data.get("研究機関", "").split(),
            "出身校": raw_infobox_data.get("出身校", "").split(),
            "博士論文": raw_infobox_data.get("博士論文", ""),
            "博士課程指導教員": raw_infobox_data.get("博士課程指導教員", ""),
            "他の指導教員": raw_infobox_data.get("他の指導教員", ""),
            "主な業績": raw_infobox_data.get("主な業績", "").split(),
            "影響を与えた人物": raw_infobox_data.get("影響を与えた人物", "").split(),
            "主な受賞歴": raw_infobox_data.get("主な受賞歴", "").split(),
            "配偶者": raw_infobox_data.get("配偶者", "").split(),
            "子供": raw_infobox_data.get("子供", "").split(),
        }
        logger.debug(f"Infoboxデータを抽出: {infobox_data}")
        return infobox_data

    def extract_name(self, name_field: str) -> str:
        """
        名前フィールドから名前を抽出します。

        Args:
            name_field (str): 名前フィールド。

        Returns:
            str: 抽出された名前。
        """
        # 英語名と日本語名を分割する
        name_parts = re.split(r'[A-Za-z]', name_field)
        return name_parts[-1].strip() if name_parts else name_field.strip()

    def extract_full_name(self, name_field: str) -> str:
        """
        名前フィールドから本名を抽出します。

        Args:
            name_field (str): 名前フィールド。

        Returns:
            str: 抽出された本名。
        """
        # 英語名と日本語名を分割する
        name_parts = re.split(r'[A-Za-z]', name_field)
        full_name = name_field.replace(name_parts[-1], "").strip() if name_parts else name_field.strip()
        return full_name

    def extract_birth_date(self, infobox_data: dict) -> dict:
        """
        Infoboxデータから生年月日を抽出し、年、月、日に分けて返します。

        Args:
            infobox_data (dict): Infoboxデータ。

        Returns:
            dict: 抽出された生年月日を年、月、日に分けた辞書。
        """
        birth_date_pattern = re.compile(r"(\d{4})年\s*(\d{1,2})月(\d{1,2})日")
        birth_fields = ["生誕", "誕生日", "誕生"]
        for field in birth_fields:
            birth_field = infobox_data.get(field, "")
            match = birth_date_pattern.search(birth_field)
            if match:
                # 空白を削除して正規化
                birth_date = match.group(0).replace(" ", "")
                return {
                    "生年月日": birth_date,
                    "年": int(match.group(1)),
                    "月": int(match.group(2)),
                    "日": int(match.group(3))
                }
        return {}

    def extract_birth_place(self, infobox_data: dict) -> str:
        """
        Infoboxデータから出身地を抽出します。

        Args:
            infobox_data (dict): Infoboxデータ。

        Returns:
            str: 抽出された出身地。
        """
        birth_place_pattern = re.compile(r"\d{4}年\s*\d{1,2}月\s*\d{1,2}日\s*(.+)")
        birth_fields = ["生誕", "誕生日", "誕生"]
        for field in birth_fields:
            birth_field = infobox_data.get(field, "")
            match = birth_place_pattern.search(birth_field)
            if match:
                birth_place = match.group(1).replace("  ", ", ").strip()  # "ドイツ帝国, ヴュルテンベルク王国, ウルム"
                return birth_place
        return ""

    def extract_death_date(self, infobox_data: dict, birth_year: int = None) -> dict:
        """
        Infoboxデータから死没日を抽出し、年、月、日に分けて返します。

        Args:
            infobox_data (dict): Infoboxデータ。
            birth_year (int, optional): 生年。享年を計算するために使用。

        Returns:
            dict: 抽出された死没日を年、月、日に分けた辞書と享年が含まれます。
        """
        death_date_pattern = re.compile(r"(\d{4})年\s*(\d{1,2})月(\d{1,2})日")
        death_fields = ["死没", "死亡"]
        for field in death_fields:
            death_field = infobox_data.get(field, "")
            match = death_date_pattern.search(death_field)
            if match:
                # 空白を削除して正規化
                death_date = match.group(0).replace(" ", "")
                death_year = int(match.group(1))
                death_month = int(match.group(2))
                death_day = int(match.group(3))

                age_at_death = None
                if birth_year is not None:
                    age_at_death = death_year - birth_year
                    birth_month = infobox_data.get("生年月日", {}).get("月", 1)
                    birth_day = infobox_data.get("生年月日", {}).get("日", 1)
                    if (death_month, death_day) < (birth_month, birth_day):
                        age_at_death -= 1

                return {
                    "死没日": death_date,
                    "年": death_year,
                    "月": death_month,
                    "日": death_day,
                    "享年": age_at_death
                }
        return {}

    def preprocess_text(self, text: str) -> str:
        """
        テキストデータを前処理して不要な文字や記号を削除し、日付形式を統一します。

        Args:
            text (str): 前処理するテキストデータ。

        Returns:
            str: 前処理されたテキストデータ。
        """
        # 不要な文字や記号を削除
        text = re.sub(r'[^\w\s年月日]', '', text)

        # 日付形式を統一
        text = re.sub(r'(\d{4})[^\d](\d{1,2})[^\d](\d{1,2})', r'\1年\2月\3日', text)

        # 「3月14日日」のように日が2回続いているのを修正
        text = re.sub(r'(\d{1,2})月(\d{1,2})日日', r'\1月\2日', text)

        # 業績の達成時期が曖昧な場合の処理
        text = re.sub(r'頃', '', text)  # 例えば「〇〇頃」を削除

        return text

    def extract_achievements(self, sections: list, birth_date: str, death_year: int = None) -> list:
        """
        テキストセクションから業績を抽出し、達成年齢を計算します。

        Args:
            sections (list): テキストセクションのリスト。
            birth_date (str): 生年月日。
            death_year (int, optional): 死没年。これを超える達成時期の業績は含まない。

        Returns:
            list: 業績のリスト。
        """
        achievements = []
        achievement_patterns = [
            re.compile(r"(\d{4}年)(.*?)(達成|発表|受賞|設立)"),
            re.compile(r"(\d{1,2}歳)(.*?)(達成|発表|受賞|設立)")
        ]

        for section in sections:
            text = section.get("text", "")
            text = self.preprocess_text(text)  # 前処理を適用
            for pattern in achievement_patterns:
                matches = pattern.findall(text)
                for match in matches:
                    year_or_age, content, keyword = match
                    content += keyword  # キーワードを内容に追加
                    achievement_year = int(year_or_age.replace("年", "")) if "年" in year_or_age else None
                    if death_year is None or (achievement_year is not None and achievement_year <= death_year):
                        achievements.append({
                            "内容": content.strip(),
                            "達成時期": year_or_age,
                            "達成年齢": self.calculate_age(year_or_age, birth_date) if "年" in year_or_age else int(
                                year_or_age.replace("歳", ""))
                        })

        # "達成年齢" で並び替え
        achievements.sort(key=lambda x: x["達成年齢"])
        logger.debug(f"業績データを抽出: {achievements}")
        return achievements

    def calculate_age(self, year_or_age: str, birth_date: str) -> int:
        """
        業績達成時の年齢を計算します。

        Args:
            year_or_age (str): 達成時期。
            birth_date (str): 生年月日。

        Returns:
            int: 達成年齢。
        """
        birth_date_parsed = dateparser.parse(birth_date)
        if birth_date_parsed is None:
            logger.error(f"生年月日の解析に失敗しました: {birth_date}")
            return -1  # 無効な年齢を示すために-1を返す

        birth_year = birth_date_parsed.year
        achievement_year = int(year_or_age.replace("年", ""))
        return achievement_year - birth_year

    def process_data(self):
        """
        各ページタイトルから情報を抽出し、JSONファイルに保存します。
        """
        all_information = []

        for title in self.page_titles:
            logger.info(f"{title} の情報を処理中")
            info = self.extract_information(title)
            if info:
                all_information.append(info)

        with open("processed_data.json", "w", encoding="utf-8") as f:
            json.dump(all_information, f, ensure_ascii=False, indent=2)
        logger.info("全てのデータが処理され、processed_data.json に保存されました")

def main():
    page_titles = ["夏目漱石", "アルベルト・アインシュタイン"]
    processor = DataProcessor(page_titles)
    processor.process_data()

if __name__ == "__main__":
    main()