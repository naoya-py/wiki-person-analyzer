import re

class NameExtractor:
    """
    偉人情報から日本語の名前を抽出するクラス。
    """

    @staticmethod
    def extract_japanese_name(name: str) -> str:
        """
        日本語の名前を抽出するメソッド。
        """
        if name:
            # 日本語の名前を正規表現で抽出
            japanese_name = re.findall(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uff66-\uff9f]+', name)
            if japanese_name:
                return ''.join(japanese_name)
        return "不明"