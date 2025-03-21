import json
import os
from datetime import datetime

class DataSaver:
    """
    データをファイルに保存するためのクラス。
    """

    @staticmethod
    def save_data(data: dict, data_type: str, directory: str = "C:/Users/pearj/Desktop/Pycharm/biography_analyzer/data/raw"):
        """
        データをjsonファイルで保存する。

        Args:
            data (dict): 保存するデータ。
            data_type (str): データの種類（例: infobox, text）。
            directory (str): 保存先ディレクトリ。
        """
        if not os.path.exists(directory):
            os.makedirs(directory)
        filename = os.path.join(directory, f"dataset_{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"データセットを {filename} に保存しました。")