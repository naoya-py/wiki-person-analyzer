import pandas as pd

class DataProcessor:
    def __init__(self):
        pass  # コンストラクタはここでは特に何もしません

    def _format_infobox_value(self, value):
        """
        infobox の値がリストだった場合、カンマ区切りの文字列に変換する。
        リストでない場合はそのまま返す。
        """
        print(f"\n--- _format_infobox_value メソッドが呼び出されました ---")
        print(f"入力値のタイプ: {type(value)}")
        print(f"入力値: {value}")

        if isinstance(value, list):
            print("ステップ1: 入力値はリストです。")
            formatted_value = ", ".join(value)
            print("ステップ2: リストの要素をカンマとスペースで結合します。")
            print(f"結合後の文字列: {formatted_value}")
            print("ステップ3: 結合された文字列を返します。")
            return formatted_value
        else:
            print("ステップ1: 入力値はリストではありません。")
            print("ステップ2: 入力値をそのまま返します。")
            return value


# テストデータの作成
data_processor = DataProcessor()

# テストケース1: リストが入力された場合
list_input = ["要素1", "要素2", "要素3"]
result1 = data_processor._format_infobox_value(list_input)
print(f"テストケース1の結果: {result1}")

# テストケース2: 文字列が入力された場合
string_input = "これは文字列です"
result2 = data_processor._format_infobox_value(string_input)
print(f"テストケース2の結果: {result2}")

# テストケース3: 整数が入力された場合
integer_input = 123
result3 = data_processor._format_infobox_value(integer_input)
print(f"テストケース3の結果: {result3}")

# テストケース4: 辞書が入力された場合
dict_input = {"key": "value"}
result4 = data_processor._format_infobox_value(dict_input)
print(f"テストケース4の結果: {result4}")

# テストケース5: 空のリストが入力された場合
empty_list_input = []
result5 = data_processor._format_infobox_value(empty_list_input)
print(f"テストケース5の結果: {result5}")

# テストケース6: Noneが入力された場合
none_input = None
result6 = data_processor._format_infobox_value(none_input)
print(f"テストケース6の結果: {result6}")