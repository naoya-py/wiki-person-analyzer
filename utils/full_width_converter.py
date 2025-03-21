import jaconv
import re

class FullWidthConverter:
    """
    カタカナは全角に、英字、数字、空白は半角に変換するユーティリティクラス。
    """

    @staticmethod
    def convert_to_fullwidth(text: str) -> str:
        """
        カタカナは全角に、英字、数字、空白は半角に変換する。

        Args:
            text (str): 変換対象のテキスト。

        Returns:
            str: 変換後のテキスト。
        """
        # 半角カタカナを全角カタカナに変換
        text = jaconv.h2z(text, kana=True, ascii=False, digit=False)
        # 全角英字、数字、空白を半角に変換
        text = jaconv.z2h(text, kana=False, ascii=True, digit=True)
        # 連続する全角スペース、半角スペース、タブ、改行を半角スペースに置換
        text = re.sub(r'[ \u3000\t\n]+', ' ', text).strip()
        return text