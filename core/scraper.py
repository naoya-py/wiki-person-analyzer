import requests
from bs4 import BeautifulSoup, Comment
import re
import unicodedata
from utils.logger import configure_logging, get_logger
import logging
import sys

configure_logging(level=logging.INFO, stream=sys.stdout)
logger = get_logger(__name__)

class Scraper:
    """
    Wikipediaのページから情報をスクレイピングするクラス。

    BASE_URL: str
        日本語版WikipediaのAPIエンドポイント
    unnecessary_tags: list[str]
        HTML本文抽出時に削除する不要なタグのリスト。
        可読性、テキスト整形、ノイズ除去を目的として削除するタグを定義する。
        例:
            - 構造系:  span, div, section, aside, footer, header, nav
            - 装飾系:  b, i, strong, em, sup, sub, cite, code, pre, mark, small, s, u, br, hr, wbr
            - リスト・表: ul, ol, li, dl, dt, dd, table, caption, thead, tbody, tfoot, tr, th, td
            - メディア: img, audio, video, canvas, embed, object, picture, source, track
            - スクリプト・スタイル: script, noscript, style
            - フォーム: form, input, textarea, select, button, label, fieldset, legend, option, optgroup, datalist, keygen, output, progress, meter
            - フレーム: iframe, frame, frameset
            - その他:  annotation, annotation-xml, applet, area, base, basefont, bgsound, blink, body, button, dir, embed, font, frame, frameset, head, html, isindex, keygen, link, map, marquee, menu, menuitem, meta, nobr, noembed, noframes, object, param, portal, rb, rtc, shadow, slot, spacer, strike, style, tt, u, var, template, xml, xmp
        exclude_words: list[str]
            本文から削除する不要なキーワードのリスト。
            例:  "編集" (Wikipediaの編集リンク) など
    """

    BASE_URL = "https://ja.wikipedia.org/w/api.php"  # 日本語版WikipediaのAPIエンドポイント

    unnecessary_tags = [
        "sup", "style", "scope", "typeof", "strong",
    ]  #  必要に応じてリストを調整 (docstringで説明追加)
    exclude_words = ["編集"]  #  必要に応じてリストに追加


    def __init__(self, page_title: str):
        """
        Scraperのコンストラクタ。

        Args:
            page_title (str): スクレイピング対象のWikipediaページタイトル
        """
        self.page_title = page_title
        self.page_id = None  # ページID (後で取得)
        self.html_content = None  # HTMLコンテンツ (後で取得)
        logger.debug(f"Scraperオブジェクトを初期化しました。対象ページ: {page_title}")

    def fetch_page_data(self):
        """
        Wikipedia APIを使ってページ情報を取得し、
        page_id, html_content 属性に格納する。

        Raises:
            ValueError: Wikipedia APIエラー、ページが見つからない場合、
                            またはリクエストエラーが発生した場合。
        """
        logger.info(f"ページデータ取得開始: {self.page_title}")
        params = {
            "action": "parse", #parseに変更
            "format": "json",
            "page": self.page_title,
            "prop": "text",  # textのみ取得
            "redirects": "true"
        }

        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            logger.debug(f"APIレスポンス: {data}")

            if "error" in data:
                error_info = data["error"]["info"]
                logger.error(f"Wikipedia APIエラー: {error_info}")
                raise ValueError(f"Wikipedia APIエラー: {error_info}") # エラーメッセージ簡略化

            if "parse" not in data:
                logger.error(f"ページが見つかりません: {self.page_title}")
                raise ValueError(f"ページが見つかりません: {self.page_title}") # エラーメッセージ簡略化

            self.page_id = data["parse"]["pageid"]
            self.html_content = data["parse"]["text"]["*"]
            logger.info(f"ページデータを取得しました。ページID: {self.page_id}")

        except requests.exceptions.RequestException as e:
            logger.error(f"リクエストエラー: {e}")
            self.page_id = None  # エラー時にも page_id を初期化
            raise ValueError(f"リクエストエラー: {e}") from e
        except ValueError as e: #追加
            logger.error(f"ValueError: {e}")
            self.page_id = None
            raise

    def _extract_text_from_cell(self, cell: BeautifulSoup) -> str:
        """
        <td>タグ内のテキストを抽出するヘルパー関数。
        不要なタグを削除し、テキストを正規化する。
        **セクション編集リンク、脚注・出典記号、全角スペースの処理を追加**
        **td > div > ul > li > a のテキスト抽出に対応**

        Args:
            cell (BeautifulSoup): <td>タグのBeautifulSoupオブジェクト

        Returns:
            str: 抽出・正規化後のテキスト
        """
        # 不要なタグを削除
        for tag in cell.find_all(
            ["style", "scope", "typeof", "strong", "href"]
        ):  # styleタグも削除
            tag.decompose()

        extracted_texts = [] # 抽出したテキストをリストで保持

        # td 直下のテキストを取得
        cell_text = cell.get_text(separator=" ", strip=True)
        if cell_text:
            extracted_texts.append(cell_text)

        # 抽出したテキストを結合 (", " 区切り)
        text = ", ".join(extracted_texts)

        # テキストを正規化 (以前と同様)
        text = unicodedata.normalize("NFKC", text)
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        text = re.sub(r"\u3000", " ", text)

        # 不要な文字を削除 (以前と同様)
        pattern = r"[^\w\s\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff,*-]"
        text = re.sub(pattern, "", text)

        return text

    def extract_infobox_data(self) -> dict:
        """
        Beautiful SoupでHTMLから基本情報(infobox)を抽出する。

        Returns:
            dict: 抽出した基本情報 (辞書形式)
                   キー: infoboxの項目名、値: 項目に対応するテキストデータ (辞書形式)
                   "名前" キーは特別に、{"名前": "記事タイトル名"} の形式で格納される。
                   infobox が存在しない場合は空の辞書を返す。

        Raises:
            ValueError: HTMLコンテンツが取得できていない場合。
                        fetch_page_data() を実行する必要がある。
        """
        logger.info("基本情報抽出開始")
        if not self.html_content:
            logger.error("HTMLコンテンツがありません。fetch_page_data()を先に実行してください。")
            raise ValueError("fetch_page_data()を先に実行してください。")

        soup = BeautifulSoup(self.html_content, "lxml")  # lxml
        infobox = soup.find("table", class_="infobox vcard")

        data = {}

        if infobox:
            first_row = infobox.find("tr")
            if first_row:
                header = first_row.find("th")
                if header:
                    data["名前"] = {"名前": header.get_text(strip=True)}  # keyを名前で統一
                else:
                    data["名前"] = {"名前": self.page_title}

            # infobox内の他の情報
            rows = infobox.find_all("tr")
            for row in rows:
                header = row.find("th")
                value_cell = row.find("td")
                # thがない場合
                if not header and value_cell:
                    key = "未分類"  # または適切なデフォルトのキー
                    value = self._extract_text_from_cell(value_cell)
                    if key not in data:  # キーが存在しない場合
                        data[key] = value
                    else:
                        # 既存のキーに追加
                        if isinstance(data[key], list):
                            data[key].extend(
                                value if isinstance(value, list) else [value]
                            )
                        else:
                            data[key] = [data[key]] + (
                                value if isinstance(value, list) else [value]
                            )
                    continue  # 次の行
                # th, tdがある場合
                if header and value_cell:
                    key = header.get_text(strip=True)
                    value = self._extract_text_from_cell(value_cell)
                    if key:
                        data[key] = {key: value}  # keyとvalueを辞書で登録
        else:
            # infoboxがない場合、ページタイトルを名前に設定
            data["名前"] = {"名前": self.page_title}
        logger.info("基本情報抽出完了")
        return data

    def extract_image_data(self) -> list:
        """
        Beautiful SoupでHTMLから画像データ (URL, altテキスト) を抽出する。

        Returns:
            list: 抽出した画像データのリスト (辞書形式)
                   [
                       {"image_url": "画像のURL", "alt_text": "画像のaltテキスト"},
                       ...
                   ]

        Raises:
            ValueError: HTMLコンテンツが取得できていない場合。
                        fetch_page_data() を実行する必要がある。
        """
        logger.info("画像データ抽出開始")
        if not self.html_content:
            logger.error("HTMLコンテンツがありません。fetch_page_data()を先に実行してください。")
            raise ValueError("fetch_page_data()を先に実行してください。")

        soup = BeautifulSoup(self.html_content, "lxml")
        images = soup.find_all("img")

        image_data_list = []
        for img in images:
            image_url = img.get("src")
            alt_text = img.get("alt")
            image_data_list.append({"image_url": image_url, "alt_text": alt_text})

        logger.info("画像データ抽出完了")
        return image_data_list

    def extract_categories(self) -> list:
        """
        Beautiful SoupでHTMLからカテゴリデータを抽出する。

        Returns:
            list: 抽出したカテゴリデータのリスト (文字列形式)
                   例: ["カテゴリ1", "カテゴリ2", ...]
                   カテゴリが存在しない場合は空のリストを返す。

        Raises:
            ValueError: HTMLコンテンツが取得できていない場合。
                        fetch_page_data() を実行する必要がある。
        """
        logger.info("カテゴリデータ抽出開始")
        if not self.html_content:
            logger.error("HTMLコンテンツがありません。fetch_page_data()を先に実行してください。")
            raise ValueError("fetch_page_data()を先に実行してください。")

        soup = BeautifulSoup(self.html_content, "lxml")
        category_links = soup.select(".mw-normal-catlinks ul li a") #  カテゴリリンクを取得

        categories = []
        for link in category_links:
            category_text = link.get_text(strip=True)
            if category_text:
                categories.append(category_text)

        logger.info("カテゴリデータ抽出完了")
        return categories


    def extract_text(self, normalize_text: bool = True, remove_exclude_words: bool = True) -> dict:
        """
        Beautiful SoupでHTMLから本文と見出しを抽出する (改良版)。
        **セクション編集リンク、脚注・出典記号、全角スペースの処理を_post_process_textに追加**

        Args:
            normalize_text (bool): テキスト正規化処理を行うかどうか (デフォルト: True)。
            remove_exclude_words (bool): 不要ワード削除処理を行うかどうか (デフォルト: True)。

        Returns:
            dict: 見出しと本文を格納した辞書。
                   キー: "headings_and_text"
                   値: 見出しと本文テキストのペアを格納したリスト (辞書形式)。
                        [
                            {"heading": "見出し1", "text": "本文1"},
                            {"heading": "見出し2", "text": "本文2"},
                            ...
                        ]

        Raises:
            ValueError: HTMLコンテンツが取得できていない場合。
                        fetch_page_data() を実行する必要がある。
        """
        logger.info("本文と見出し抽出開始 (改良版)")
        if not self.html_content:
            raise ValueError("fetch_page_data() を先に実行してください。")

        soup = BeautifulSoup(self.html_content, 'lxml')

        # 不要な要素を削除
        self._remove_unnecessary_elements(soup)

        # 見出しと本文を抽出
        headings_and_text = self._extract_headings_and_body(soup)

        #  テキスト後処理 (正規化、セクション編集リンク削除、脚注・出典記号削除、全角スペース変換)
        if normalize_text: # オプションで正規化処理をON/OFF
            full_text_content_list = self._post_process_text(headings_and_text)
        else:
            full_text_content_list = headings_and_text # 正規化しない場合はそのまま代入

        # 不要なワードを削除 (例: 編集)
        if remove_exclude_words: # オプションで不要ワード削除処理をON/OFF
            full_text_content_list = self._remove_exclude_words(full_text_content_list)

        logger.info("本文と見出し抽出完了 (改良版)")
        return {"headings_and_text": full_text_content_list} #  リスト形式でheadings_and_textを返す


    def _remove_unnecessary_elements(self, soup: BeautifulSoup):
        """HTMLから不要な要素を削除 (private method)

        Args:
            soup (BeautifulSoup): HTMLのBeautifulSoupオブジェクト
        """
        unnecessary_tags = Scraper.unnecessary_tags # クラス変数として定義
        logger.debug("不要要素削除開始") #  debugログ追加
        for tag_name in unnecessary_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        for element in soup.find_all(string=lambda text: isinstance(text, Comment)):
            element.extract()
        logger.debug("不要要素削除完了")

    def _extract_headings_and_body(self, soup: BeautifulSoup) -> list:
        """HTMLから見出しと本文を階層的に抽出 (h2, h3, h4対応)

        Args:
            soup (BeautifulSoup): HTMLのBeautifulSoupオブジェクト

        Returns:
            list: 見出しと本文テキストのペアを階層的に格納したリスト (辞書形式)
                  [
                      {
                          "heading_level": "h2",
                          "heading_text": "h2 見出し1",
                          "text_content": "h2 本文1",
                          "sub_sections": [
                              {
                                  "heading_level": "h3",
                                  "heading_text": "h3 見出し1-1",
                                  "text_content": "h3 本文1-1",
                                  "sub_sections": [
                                      {
                                          "heading_level": "h4",
                                          "heading_text": "h4 見出し1-1-1",
                                          "text_content": "h4 本文1-1-1",
                                          "sub_sections": []
                                      },
                                      ...
                                  ]
                              },
                              ...
                          ]
                      },
                      ...
              ]
        """
        logger.debug("階層的な見出しと本文抽出開始 (h2, h3, h4対応)")
        headings_and_text = []
        heading_divs_h2 = soup.find_all('div', class_='mw-heading mw-heading2') # h2レベルの div.mw-heading を取得

        for heading_div_h2 in heading_divs_h2: # h2レベルの div.mw-heading を処理
            h2_tag = heading_div_h2.find('h2')
            if h2_tag:
                h2_heading_text = h2_tag.get_text(strip=True)
                if not h2_heading_text: # 空の見出しはスキップ
                    continue

            h2_paragraphs = []
            sub_sections_h3 = []
            sibling = heading_div_h2.find_next_sibling() #  h2見出しdivの兄弟要素から処理開始
            while sibling:
                if sibling.name == 'div' and 'mw-heading' in sibling.get('class', []) and 'mw-heading2' in sibling.get('class', []):
                    # 次の h2 レベルの見出しdiv が出現したら、h2セクションの処理を終了
                    break

                if sibling.name == 'div' and 'mw-heading' in sibling.get('class', []) and 'mw-heading3' in sibling.get('class', []):
                    # h3レベルの見出し div が出現した場合、h3セクションとして再帰的に抽出
                    sub_section_h3_data = self._extract_subsection_h3(sibling) #  _extract_subsection_h3 で h3 セクションを抽出
                    if sub_section_h3_data: #  抽出データがあれば追加
                        sub_sections_h3.extend(sub_section_h3_data) #  extendでリストを結合
                    sibling = sibling.find_next_sibling() #  次の兄弟要素へ
                    continue #  h3 セクションを処理したので、pタグ抽出処理はスキップ

                if sibling.name == 'p' or sibling.name == 'ul': # pタグとliタグを本文として抽出
                    paragraph_text = sibling.get_text(strip=True)
                    if paragraph_text: # 空の段落はスキップ
                        h2_paragraphs.append(paragraph_text)

                sibling = sibling.find_next_sibling() #  次の兄弟要素へ

            h2_text_content = "\n".join(h2_paragraphs)
            headings_and_text.append({
                "heading_level": "h2",
                "heading_text": h2_heading_text,
                "text_content": h2_text_content,
                "sub_sections": sub_sections_h3 #  抽出した h3 セクションを格納
            })

        logger.debug("階層的な見出しと本文抽出完了 (h2, h3, h4対応)")
        return headings_and_text


    def _extract_subsection_h3(self, heading_div_h3: BeautifulSoup) -> list:
        """h3レベルのセクションを見出しと本文を抽出 (再帰関数)

        Args:
            heading_div_h3 (BeautifulSoup): h3レベルの見出し div (div.mw-heading mw-heading3)

        Returns:
            list: h3レベルの見出しと本文テキストのペアを階層的に格納したリスト (辞書形式)
                  [
                      {
                          "heading_level": "h3",
                          "heading_text": "h3 見出し1-1",
                          "text_content": "h3 本文1-1",
                          "sub_sections": [ # h4 セクション
                              {
                                  "heading_level": "h4",
                                  "heading_text": "h4 見出し1-1-1",
                                  "text_content": "h4 本文1-1-1",
                                  "sub_sections": []
                              },
                              ...
                          ]
                      },
                      ...
                  ]
            """
        sub_sections_h3_data = []
        h3_tag = heading_div_h3.find('h3')
        if h3_tag:
            h3_heading_text = h3_tag.get_text(strip=True)
            if not h3_heading_text: # 空の見出しはスキップ
                return [] #  空リストを返す

        h3_paragraphs = []
        sub_sections_h4 = []
        sibling = heading_div_h3.find_next_sibling() #  h3見出しdivの兄弟要素から処理開始
        while sibling:
            if sibling.name == 'div' and 'mw-heading' in sibling.get('class', []) and ('mw-heading2' in sibling.get('class', []) or 'mw-heading3' in sibling.get('class', [])):
                # 次の h2 or h3 レベルの見出しdiv が出現したら、h3セクションの処理を終了
                #  h2, h3 レベルで処理を終了 (h4 は h3 の sub_sections として処理される)
                break

            if sibling.name == 'div' and 'mw-heading' in sibling.get('class', []) and 'mw-heading4' in sibling.get('class', []):
                # h4レベルの見出し div が出現した場合、h4セクションとして抽出 (再帰不要)
                sub_section_h4_data = self._extract_subsection_h4(sibling) #  _extract_subsection_h4 で h4 セクションを抽出
                if sub_section_h4_data: #  データがあれば追加
                    sub_sections_h4.append(sub_section_h4_data) #  appendで辞書を追加
                sibling = sibling.find_next_sibling() #  次の兄弟要素へ
                continue #  h4 セクションを処理したので、pタグ抽出処理はスキップ


            if sibling.name == 'p' or sibling.name == 'ul': # p タグを本文として抽出
                paragraph_text = sibling.get_text(strip=True)
                if paragraph_text: # 空の段落はスキップ
                    h3_paragraphs.append(paragraph_text)

            sibling = sibling.find_next_sibling() #  次の兄弟要素へ

        h3_text_content = "\n".join(h3_paragraphs)
        sub_sections_h3_data.append({
            "heading_level": "h3",
            "heading_text": h3_heading_text,
            "text_content": h3_text_content,
            "sub_sections": sub_sections_h4 #  抽出した h4 セクションを格納
        })
        return sub_sections_h3_data #  リストを返す


    def _extract_subsection_h4(self, heading_div_h4: BeautifulSoup) -> dict:
        """h4レベルのセクションを見出しと本文を抽出 (再帰終端)

        Args:
            heading_div_h4 (BeautifulSoup): h4レベルの見出し div (div.mw-heading mw-heading4)

        Returns:
            dict: h4レベルの見出しと本文テキストのペアを格納した辞書 (辞書形式)
              {
                  "heading_level": "h4",
                  "heading_text": "h4 見出し1-1-1",
                  "text_content": "h4 本文1-1-1",
                  "sub_sections": [] # h4 より深い階層はないので空リスト
              }
    """
        sub_section_h4_data = {} #  辞書型で初期化
        h4_tag = heading_div_h4.find('h4')
        if h4_tag:
            h4_heading_text = h4_tag.get_text(strip=True)
            if not h4_heading_text: # 空の見出しはスキップ
                return {} #  空辞書を返す

        h4_paragraphs = []
        sibling = heading_div_h4.find_next_sibling() #  h4見出しdivの兄弟要素から処理開始
        while sibling:
            if sibling.name == 'div' and 'mw-heading' in sibling.get('class', []) and ('mw-heading2' in sibling.get('class', []) or 'mw-heading3' in sibling.get('class', []) or 'mw-heading4' in sibling.get('class', [])):
                # 次の h2, h3, h4 レベルの見出しdiv が出現したら、h4セクションの処理を終了
                #  h2, h3, h4 レベルで処理を終了 (h4 が最下層)
                break
            if sibling.name == 'p' or sibling.name == 'ul': # pタグとliタグを本文として抽出
                paragraph_text = sibling.get_text(strip=True)
                if paragraph_text: # 空の段落はスキップ
                    h4_paragraphs.append(paragraph_text)
            sibling = sibling.find_next_sibling() #  次の兄弟要素へ

        h4_text_content = "\n".join(h4_paragraphs)
        sub_section_h4_data = {
            "heading_level": "h4",
            "heading_text": h4_heading_text,
            "text_content": h4_text_content,
            "sub_sections": [] # h4 は最下層なので常に空リスト
        }
        return sub_section_h4_data #  辞書を返す


    def _post_process_text(self, headings_and_text: list) -> list:
        """
        抽出したテキストに対して、正規化、不要な記号・文字列の削除など、
        後処理を行う (private method)。
        **セクション編集リンク、脚注・出典記号、全角スペースの処理を追加**

        Args:
            headings_and_text (list): 見出しと本文テキストのペアを格納したリスト

        Returns:
            list: 後処理後の見出しと本文テキストのペアを格納したリスト
        """
        logger.debug("テキスト後処理開始") #  debugログ追加
        processed_headings_and_text = []
        for section in headings_and_text:
            heading_text = section["heading_text"] #  キーを "heading_text" に修正
            text_content = section["text_content"] #  キーを "text_content" に修正

            # テキスト正規化
            heading_text = unicodedata.normalize("NFKC", heading_text)
            text_content = unicodedata.normalize("NFKC", text_content)

            # 不要な記号・文字列を削除 (セクション編集リンク、脚注・出典記号)
            heading_text = re.sub(r"\[編集\]", "", heading_text) #  re.sub() で処理
            text_content = re.sub(r"\[編集\]", "", text_content) #  re.sub() で処理
            heading_text = re.sub(r"\[\d+\]|\[要出典\]", "", heading_text) #  re.sub() で処理
            text_content = re.sub(r"\[\d+\]|\[要出典\]", "", text_content) #  re.sub() で処理

            # 全角スペースを半角スペースに置換
            heading_text = re.sub(r"\u3000", " ", heading_text) #  re.sub() で処理
            text_content = re.sub(r"\u3000", " ", text_content) #  re.sub() で処理

            #  行頭・行末の空白、連続する空白を削除
            heading_text = heading_text.strip()
            text_content = text_content.strip()
            heading_text = re.sub(r"\s+", " ", heading_text)
            text_content = re.sub(r"\s+", " ", text_content)

            processed_headings_and_text.append({
                "heading_level": section["heading_level"], #  見出しレベルも引き継ぐ
                "heading_text": heading_text, #  キーを "heading_text" に修正
                "text_content": text_content, #  キーを "text_content" に修正
                "sub_sections": self._post_process_text(section["sub_sections"]) if section.get("sub_sections") else [] #  sub_sectionsに対しても再帰的に後処理
            })
        logger.debug("テキスト後処理完了") #  debugログ追加
        return processed_headings_and_text


    def _remove_exclude_words(self, headings_and_text: list) -> list:
        """
        抽出したテキストから不要なキーワードを削除する (private method)。

        Args:
            headings_and_text (list): 見出しと本文テキストのペアを格納したリスト

        Returns:
            list: 不要なキーワード削除後の見出しと本文テキストのペアを格納したリスト
        """
        logger.debug("不要ワード削除開始") #  debugログ追加
        exclude_words = Scraper.exclude_words # クラス変数として定義
        processed_headings_and_text = []
        for section in headings_and_text:
            heading_text = section["heading_text"] #  キーを "heading_text" に修正
            text_content = section["text_content"] #  キーを "text_content" に修正

            #  見出しと本文から不要ワードを削除
            for word in exclude_words:
                heading_text = heading_text.replace(word, "")
                text_content = text_content.replace(word, "")

            processed_headings_and_text.append({
                "heading_level": section["heading_level"], #  見出しレベルも引き継ぐ
                "heading_text": heading_text, #  キーを "heading_text" に修正
                "text_content": text_content, #  キーを "text_content" に修正
                "sub_sections": self._remove_exclude_words(section["sub_sections"]) if section.get("sub_sections") else [] #  sub_sectionsに対しても再帰的に不要ワード削除
            })
        logger.debug("不要ワード削除完了") #  debugログ追加
        return processed_headings_and_text

if __name__ == "__main__":
    from utils.logger import logger  # logger設定 (logger.py が必要)
    import json

    # logger設定 (ファイルとコンソールに出力)
    logger.basicConfig(level=logger.DEBUG) #  logger設定は main 側で行う

    scraper = Scraper(page_title="アルベルト・アインシュタイン") #  例: アルベルト・アインシュタイン
    scraper.fetch_page_data()

    # 改良版のextract_text()を実行 (正規化ON, 不要ワード削除ON)
    extracted_data_improved = scraper.extract_text(normalize_text=True, remove_exclude_words=True)
    print("--- 本文と見出し (pタグとliタグ, 正規化ON, 不要ワード削除ON) ---") #  表示変更
    print(json.dumps(extracted_data_improved, ensure_ascii=False, indent=2))

    # 改良版のextract_text()を実行 (正規化OFF, 不要ワード削除OFF)
    extracted_data_raw = scraper.extract_text(normalize_text=False, remove_exclude_words=False)
    print("\n--- 本文と見出し (pタグとliタグ, 正規化OFF, 不要ワード削除OFF) ---") #  表示変更
    print(json.dumps(extracted_data_raw, ensure_ascii=False, indent=2))

    # 画像データ抽出処理を追加
    extracted_image_data = scraper.extract_image_data()
    print("\n--- 画像データ (URL, altテキスト) ---")
    print(json.dumps(extracted_image_data, ensure_ascii=False, indent=2))

    # カテゴリ抽出
    extracted_categories = scraper.extract_categories()
    print("\n--- カテゴリ ---")
    print(json.dumps(extracted_categories, ensure_ascii=False, indent=2))