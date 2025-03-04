from jinja2 import Environment, FileSystemLoader
import os

class ReportGenerator:
    """
    分析結果をHTMLレポートとして出力するクラス。
    """

    def __init__(self, template_dir="templates"):
        """
        コンストラクタ。

        Args:
            template_dir (str): Jinja2テンプレートが配置されているディレクトリ。
        """
        self.template_dir = template_dir
        self.env = Environment(loader=FileSystemLoader(self.template_dir))

    def generate_report(self, data, output_path="report.html"):
        """
        HTMLレポートを生成する。

        Args:
            data (dict): レポートに埋め込むデータ。
            output_path (str): 出力するHTMLファイルのパス。
        """
        template = self.env.get_template("report.html")  # テンプレートファイル名を指定

        # レポートのファイルパスからディレクトリ部分を抽出
        output_dir = os.path.dirname(output_path)
        # ディレクトリが存在しない場合は作成
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(template.render(data=data)) # キーワード引数としてdataを渡す


# 使用例 (main.pyから呼び出されることを想定)
if __name__ == "__main__":
    # テスト用のダミーデータ
    test_data = {
        "person_name": "テスト太郎",
        "basic_info": {"名前": "テスト太郎", "生年月日": "1900年1月1日"},
        "timeline": [
            {"year": 1900, "event": "誕生"},
            {"year": 1920, "event": "大学卒業"},
        ],
        "network": {
            "related_persons": ["Aさん","Bさん"],
            "relations_by_type":{"関係1":["Aさん"],"関係2":["Bさん"]}
        },
        "wordcloud_image": "wordcloud.png",  # ダミーの画像ファイル名
    }

    generator = ReportGenerator()
    generator.generate_report(test_data, output_path="../data/output/report.html")
    print("レポートを data/output/report.html に出力しました。")