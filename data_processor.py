import pandas as pd
import re
from datetime import datetime

class DataProcessor:
    """
    スクレイピングしたデータを整形・加工するクラス。
    """

    def __init__(self, basic_info, text):
        """
        コンストラクタ。

        Args:
            basic_info (dict): Scraper.extract_basic_info() からの出力 (基本情報)。
            text (str): Scraper.extract_text() からの出力 (本文テキスト)。
        """
        self.basic_info = basic_info
        self.text = text
        self.df_basic = None  # 基本情報データフレーム
        self.df_timeline = None  # 年表データフレーム
        self.df_network = None # 関係ネットワークデータフレーム

    def create_basic_info_dataframe(self):
        """
        基本情報辞書をPandas DataFrameに変換する。
        """
        self.df_basic = pd.DataFrame([self.basic_info])
        return self.df_basic


    def clean_text(self):
        """
        本文テキストのクリーニングを行う。
        """
        # 不要な文字の削除 (ここでは例として、HTMLタグの残骸や特殊文字を削除)
        self.text = re.sub(r"\[.*?\]", "", self.text)  # 脚注 [1] などを削除
        self.text = re.sub(r"\(.*?\)", "", self.text) #丸かっこを削除
        self.text = re.sub(r"\s+", " ", self.text)    # 連続する空白を1つに
        self.text = self.text.strip()
        return self.text

    def extract_timeline(self):
        """
        本文テキストから年表データを抽出する。
        """
        # 日付と出来事を抽出する正規表現 (日本語の年号、西暦に対応)
        pattern = r"((?:[1-9]\d{3}|[元|明治|大正|昭和|平成|令和]\d{1,2}|\d{1,4})年)\s?([\d{1,2}月\d{1,2}日]*)\s?([^。]+?[。．])"

        matches = re.findall(pattern, self.text)

        timeline_data = []
        for match in matches:
            year_str = match[0]
            date_str = match[1].strip()
            event = match[2].strip()

            # 年を西暦に統一
            year = self.convert_to_ce(year_str)
            if year is None:
                continue

            # 月日が取得できなかった場合は空文字列にしておく
            if len(date_str) == 0:
                date_str = ""

            timeline_data.append({"year": year, "date": date_str, "event": event})

        self.df_timeline = pd.DataFrame(timeline_data)
        return self.df_timeline


    def convert_to_ce(self, year_str):
        """
        年号を西暦に変換
        """
        if '年' not in year_str:
            return None
        try:
            # 西暦の場合
            if year_str[:4].isdigit():
                return int(year_str[:4])

            # 元号の場合
            era = year_str[0]
            year_num = int(re.search(r'\d+', year_str).group())

            if era == "元":  # 元年を1年として扱う
                year_num = 1
            if era == "明治":
                return 1867 + year_num
            if era == "大正":
                return 1911 + year_num
            if era == "昭和":
                return 1925 + year_num
            if era == "平成":
                return 1988 + year_num
            if era == "令和":
                return 2018 + year_num
            return None  # 解析できない場合はNoneを返す

        except Exception:
            return None

    def extract_network(self):
        """
        本文から関係ネットワークデータを抽出する。(簡易版)
        """

        # パターン1: 「AはBのCである」
        pattern1 = r"([\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]{2,}?)は([\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]{2,}?)の([\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]{2,}?)である"
        # パターン2: 「AとB」
        pattern2 = r"([\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]{2,}?)と([\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]{2,}?)"

        matches = []
        matches.extend(re.findall(pattern1, self.text))
        matches.extend(re.findall(pattern2, self.text))

        network_data = []
        for match in matches:
            if len(match) == 3: # 「AはBのCである」
                source = match[0]
                target = match[1]
                relation = match[2]
                network_data.append({"source": source, "target": target, "relation": relation})
            elif len(match) == 2: # 「AとB」
                source = match[0]
                target = match[1]
                relation = "関係" # 仮
                network_data.append({"source": source, "target": target, "relation": relation})

        self.df_network = pd.DataFrame(network_data)
        return self.df_network