import requests
from bs4 import BeautifulSoup

class Scraper:
    """
    Wikipediaのページから情報をスクレイピングするクラス。
    """
    BASE_URL = "https://ja.wikipedia.org/w/api.php"  # 日本語版WikipediaのAPIエンドポイント

    def __init__(self, page_title):
        """
        コンストラクタ。

        Args:
            page_title (str): スクレイピング対象のWikipediaページタイトル。
        """
        self.page_title = page_title
        self.page_id = None  # ページID (後で取得)
        self.html_content = None  # HTMLコンテンツ (後で取得)

    def fetch_page_data(self):
        """
        Wikipedia APIを使ってページ情報を取得する。
        """
        params = {
            "action": "query",
            "page": self.page_title,
            "format": "json",
            "prop": "text|pageid",  # HTMLコンテンツとページIDを取得
            "redirects": "true" # リダイレクトを解決
        }

        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()  # HTTPエラーをチェック
            data = response.json()

            if "error" in data:
                raise ValueError(f"Wikipedia APIエラー: {data['error']['info']}")

            if "parse" not in data:
                raise ValueError(f"ページが見つかりません: {self.page_title}")

            self.page_id = data["parse"]["pageid"]
            self.html_content = data["parse"]["text"]["*"]

        except requests.exceptions.RequestException as e:
            raise ValueError(f"リクエストエラー: {e}") from e

    def extract_basic_info(self):
        """
        Beautiful Soupを使ってHTMLコンテンツから基本情報を抽出する。
        """
        if not self.html_content:
            raise ValueError("fetch_page_data()を先に実行してください。")

        soup = BeautifulSoup(self.html_content, "html.parser")
        infobox = soup.find("table", class_="infobox") # 基礎情報テーブルを検索

        basic_info = {}
        if infobox:
            rows = infobox.find_all("tr")
            for row in rows:
                header = row.find("th")
                if header:
                    key = header.text.strip()
                    value_cell = row.find("td")
                    if value_cell:
                        # リンクや特殊文字を除去
                        for tag in value_cell.find_all(['a','span','sup']):
                            tag.decompose()
                        value = value_cell.text.strip()
                        basic_info[key] = value
        return basic_info

    def extract_text(self):
        """
        Beautiful Soupを使ってHTMLコンテンツから本文テキストを抽出する。
        """
        if not self.html_content:
            raise ValueError("fetch_page_data() を先に実行してください。")

        soup = BeautifulSoup(self.html_content, 'html.parser')

        # 不要な要素を削除
        for tag in soup.find_all(["table", "style", "script", "noscript","sup","span",'ul']):
            tag.decompose()
        # 見出し(h1,h2...)を抽出
        for tag in soup.find_all(["h1","h2","h3","h4","h5","h6"]):
            tag.extract()
        text = soup.get_text(separator='\n', strip=True) # 改行で区切り、前後の空白を除去
        return text