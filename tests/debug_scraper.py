import sys
import os

# 親ディレクトリへのパスを取得
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path に親ディレクトリを追加
sys.path.append(parent_dir)

from core.data_processor import DataProcessor
import pandas as pd
import logging
from utils.logger import configure_logging, get_logger
# configure_logging(level=logging.DEBUG, stream=sys.stdout)
# logger = get_logger(__name__)

# configure_logging(level=logging.INFO, stream=sys.stdout) #loggingの設定を追加

# テスト対象の Wikipedia ページタイトル
page_title = "アルベルト・アインシュタイン"  # 例としてアインシュタインを使用

# DataProcessor オブジェクトを作成
processor = DataProcessor(page_title=page_title)

# データの取得と処理
processor.fetch_data() #データを取得する。
# processor.process_data() #process_data()でtextデータから固有表現を抽出する場合は実行する。

# 基本情報 DataFrame を作成
basic_info_df = processor.create_basic_info_dataframe()

# DataFrame の内容を表示
if not basic_info_df.empty:
    print("----- 基本情報 DataFrame -----")
    print(basic_info_df.to_string())  # to_string() で整形して表示
else:
    print("基本情報 DataFrame は空です。")

# DataFrame の列名を確認
print("\n----- DataFrame の列名 -----")
print(basic_info_df.columns)

# DataFrame のデータ型を確認
print("\n----- DataFrame のデータ型 -----")
print(basic_info_df.dtypes)

# DataFrame の先頭数行を確認
print("\n----- DataFrame の先頭5行 -----")
print(basic_info_df.head())

#DataFrame の統計量を確認
print("\n----- DataFrame の統計量 -----")
print(basic_info_df.describe(include='all'))