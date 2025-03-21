import json
import requests
from bs4 import BeautifulSoup, Comment, Tag
import re
import unicodedata
import sys
from datetime import timedelta
import requests_cache
from config import Config
from utils.logger import configure_logging, get_logger
from typing import Any, List, Dict, Union, Optional
from utils.full_width_converter import FullWidthConverter
from core.data_saver import DataSaver

configure_logging(level=Config.DEFAULT_LOG_LEVEL)
logger = get_logger(__name__)

class Scraper:
    """
    Wikipedia ページから情報をスクレイピングするクラス。

    属性:
        page_title (str): Wikipedia ページのタイトル。
        wikipedia_url (str, optional): Wikipedia ページの URL。指定されない場合は、page_title から自動生成される。
    """

    def __init__(self, page_title: str, wikipedia_url: Optional[str] = None):
        """
        Scraper クラスのコンストラクタ。

        Args:
            page_title (str): Wikipedia ページのタイトル。
            wikipedia_url (str, optional): Wikipedia ページの URL。指定されない場合は、page_title から自動生成される。
        """
        self.page_id: Optional[int] = None
        self.soup: Optional[BeautifulSoup] = None
        self.page_title = page_title
        self.wikipedia_url = wikipedia_url or f"https://ja.wikipedia.org/wiki/{page_title}"

        cache_name = 'wiki_cache'
        expire_after = timedelta(days=7)
        requests_cache.install_cache(
            cache_name,
            backend='mongodb',
            expire_after=expire_after,
            connection=None
        )
        self.session = requests.Session()
        self.cache_headers: Dict[str, Dict[str, str]] = {}

        self.page_content: Optional[str] = None
        self.infobox_data: Dict[str, str] = {}
        self.text_data: Dict[str, List[str]] = {}
        self.image_data: List[Dict[str, Optional[str]]] = []
        self.categories: List[str] = []
        self.site_url = Config.BASE_URL
        self.exclude_words: List[str] = Config.EXCLUDE_WORDS
        self.excluded_section_keywords: List[str] = Config.EXCLUDED_SECTION_KEYWORDS

    # ----------------------- データ取得とキャッシュ処理 -----------------------
    def fetch_page_data(self):
        """
        Wikipedia API からページデータを取得し、レスポンスヘッダーを処理する。

        条件付きリクエストヘッダー (If-None-Match, If-Modified-Since) を使用して、キャッシュの効率を向上させる。
        API レスポンスが 304 Not Modified の場合、キャッシュされたデータが最新であることを意味し、処理を中断する。

        Raises:
            ValueError: リクエストエラーまたは API エラーが発生した場合。
        """
        logger.info(f"ページデータ取得開始: {self.page_title}")
        headers = {}
        self._set_cache_headers(headers)

        params = {
            "action": "parse",
            "format": "json",
            "page": self.page_title,
            "prop": "text",
            "redirects": "true"
        }

        try:
            response = self.session.get(self.site_url, params=params, headers=headers)

            if response.from_cache:
                logger.info(f"キャッシュからデータを取得: {self.page_title}")
            else:
                logger.info(f"API から新規にデータを取得: {self.page_title}")

            logger.debug(f"API リクエスト URL: {response.request.url}")
            logger.debug(f"API リクエストパラメータ: {response.request.path_url}")
            logger.debug(f"API リクエストヘッダー: {response.request.headers}")

            response.raise_for_status()

            if self._process_response_headers(response):
                return

            data = response.json()
            logger.debug(f"API レスポンス: {json.dumps(data, indent=2, ensure_ascii=False)}")

            if "error" in data:
                error_info = data["error"]["info"]
                logger.error(f"Wikipedia API エラー: {error_info}")
                raise ValueError(f"Wikipedia API エラー: {error_info}")

            if "parse" not in data:
                logger.error(f"ページが見つかりません: {self.page_title}")
                raise ValueError(f"ページが見つかりません: {self.page_title}")

            self.page_id = data["parse"]["pageid"]
            self.page_content = data["parse"]["text"]["*"]
            logger.info(f"ページデータを取得しました: page_id={self.page_id}")

        except requests.exceptions.RequestException as e:
            logger.error(f"リクエストエラー: {e}")
            self.page_id = None
            raise ValueError(f"リクエストエラー: {e}") from e
        except ValueError as e:
            logger.error(f"ValueError: {e}")
            self.page_id = None
            raise

    def _set_cache_headers(self, headers: Dict[str, str]):
        """
        キャッシュヘッダー (If-None-Match, If-Modified-Since) を設定する。

        Args:
            headers (Dict[str, str]): リクエストヘッダー辞書。
        """
        cached_info = self.cache_headers.get(self.page_title)
        if cached_info:
            if 'etag' in cached_info:
                headers['If-None-Match'] = cached_info['etag']
            if 'last-modified' in cached_info:
                headers['If-Modified-Since'] = cached_info['last-modified']

    def _process_response_headers(self, response: requests.Response) -> bool:
        """
        レスポンスヘッダーを処理し、キャッシュ情報を更新する。

        Args:
            response (requests.Response): requests レスポンスオブジェクト。

        Returns:
            bool: 304 Not Modified だった場合は True, それ以外は False。
        """
        if response.status_code == 304:
            logger.info(f"304 Not Modified: キャッシュデータを使用: {self.page_title}")
            return True

        logger.debug(f"API レスポンスステータスコード: {response.status_code}")
        logger.debug(f"API レスポンスヘッダー: {response.headers}")

        etag = response.headers.get('ETag')
        last_modified = response.headers.get('Last-Modified')
        if etag or last_modified:
            self.cache_headers[self.page_title] = {}
            if etag:
                self.cache_headers[self.page_title]['etag'] = etag
            if last_modified:
                self.cache_headers[self.page_title]['last-modified'] = last_modified
            logger.debug(f"ETag と Last-Modified ヘッダーを保存: {self.cache_headers[self.page_title]}")
        return False

    # ----------------------- Infobox データ抽出 -----------------------
    def extract_infobox_data(self) -> Dict[str, str]:
        """
        Wikipedia ページの Infobox (右上の基本情報テーブル) のデータを抽出する。

        Returns:
            Dict[str, str]: Infobox データを格納した辞書。

        Raises:
            ValueError: HTMLコンテンツが存在しない場合。
        """
        logger.info("Infobox データ抽出開始")
        if not self.page_content:
            logger.error(Config._FETCH_PAGE_DATA_ERROR_MESSAGE)
            raise ValueError(Config._FETCH_PAGE_DATA_ERROR_MESSAGE)

        self.soup = BeautifulSoup(self.page_content, "lxml")
        infobox = self.soup.find("table", class_=["infobox", "infobox vcard", "infobox biography vcard"])

        infobox_data: Dict[str, str] = {}

        if infobox:
            infobox_data["名前"] = self._extract_infobox_header(infobox)
            infobox_data.update(self._extract_infobox_rows_data(infobox))
        else:
            infobox_data["名前"] = self.page_title

        logger.info("Infobox データ抽出完了")
        return infobox_data

    def _extract_infobox_header(self, infobox: BeautifulSoup) -> str:
        """
        Infobox からヘッダー (名前) を抽出する。

        Args:
            infobox (BeautifulSoup): Infobox の BeautifulSoup オブジェクト。

        Returns:
            str: Infobox ヘッダーテキスト、抽出できない場合はページタイトル。
        """
        first_row: Optional[Tag] = infobox.find("tr")
        if first_row:
            header: Optional[Tag] = first_row.find("th")
            return header.get_text(strip=True) if header else self.page_title
        return self.page_title

    def _extract_infobox_rows_data(self, infobox: BeautifulSoup) -> Dict[str, str]:
        """
        Infobox の行データ (キーと値) を抽出する。

        Args:
            infobox (BeautifulSoup): Infobox の BeautifulSoup オブジェクト。

        Returns:
            Dict[str, str]: Infobox 行データを格納した辞書。
        """
        rows_data: Dict[str, str] = {}
        rows = infobox.find_all("tr")
        for row in rows:
            header: Optional[Tag] = row.find("th")
            value_cell: Optional[Tag] = row.find("td")
            if header and value_cell:
                key = header.get_text(strip=True) if header and header.get_text(strip=True) else None
                if key:
                    value: str = self._extract_text_from_cell(value_cell)
                    rows_data[key] = value
        return rows_data

    def _extract_text_from_cell(self, cell: BeautifulSoup) -> str:
        """
        Infobox のセル (td) からテキストを抽出する。

        Args:
            cell (BeautifulSoup): BeautifulSoup のセルオブジェクト。

        Returns:
            str: 処理後のテキスト。
        """
        logger.debug("_extract_text_from_cell メソッド開始")

        for tag in cell.find_all(Config.UNNECESSARY_TAGS):
            tag.decompose()

        extracted_texts: List[str] = []
        cell_text = cell.get_text(separator=" ", strip=True)
        if cell_text:
            extracted_texts.append(cell_text)

        text = ", ".join(extracted_texts)

        text = unicodedata.normalize("NFKC", text)
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        text = re.sub(Config.FULL_WIDTH_SPACE, " ", text)
        pattern = r"[^\w\s\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff.,?!-]"
        text = re.sub(pattern, "", text)
        text = FullWidthConverter.convert_to_fullwidth(text)  # 全角に統一

        logger.debug(f"_extract_text_from_cell メソッド完了: 処理後のテキスト: {text}")
        return text

    # ----------------------- 画像データ抽出 -----------------------
    def extract_image_data(self) -> List[Dict[str, Optional[str]]]:
        """
        Wikipedia ページの画像データを抽出する。

        Returns:
            List[Dict[str, Optional[str]]]: 画像データを格納したリスト (辞書のリスト)。

        Raises:
            ValueError: HTMLコンテンツが存在しない場合。
        """
        logger.info("画像データ抽出開始")
        if not self.page_content:
            logger.error(Config._FETCH_PAGE_DATA_ERROR_MESSAGE)
            raise ValueError(Config._FETCH_PAGE_DATA_ERROR_MESSAGE)

        if self.soup is None:
            self.soup = BeautifulSoup(self.page_content, "lxml")
        images = self.soup.find_all("img")
        image_data_list: List[Dict[str, Optional[str]]] = []

        for img in images:
            image_url = img.get("src")
            alt_text = img.get("alt")
            if image_url:
                image_data_list.append({"image_url": image_url, "alt_text": alt_text})

        logger.info(f"画像データ抽出完了: 取得画像数={len(image_data_list)}")
        return image_data_list

    # ----------------------- カテゴリデータ抽出 -----------------------
    def extract_categories(self) -> List[str]:
        """
        Wikipedia API を使用して、Wikipedia ページのカテゴリデータを抽出する。

        Returns:
            List[str]: カテゴリ名のリスト。
        """
        logger.info(f"カテゴリデータ抽出開始: {self.page_title}")
        params = {
            "action": "query",
            "format": "json",
            "titles": self.page_title,
            "prop": "categories",
            "cllimit": "max"
        }

        try:
            response = self.session.get(self.site_url, params=params)
            response.raise_for_status()
            data = response.json()
            logger.debug(f"カテゴリ取得 API レスポンス: {data}")

            categories: List[str] = []
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if "categories" in page_data:
                    for category in page_data["categories"]:
                        category_title = category["title"]
                        if not self._contains_article_text(category_title):
                            categories.append(category_title)

            logger.info(f"カテゴリデータ抽出完了: {self.page_title} - {len(categories)} 件のカテゴリを取得")
            return categories

        except requests.exceptions.RequestException as e:
            logger.error(f"リクエストエラー: {e}")
            raise ValueError(f"リクエストエラー: {e}") from e
        except KeyError as e:
            logger.error(f"カテゴリデータの解析エラー (KeyError): {e}")
            raise ValueError(f"カテゴリデータの解析エラー (KeyError): {e}") from e
        except ValueError as e:
            logger.error(f"カテゴリデータの解析エラー (ValueError): {e}")
            raise e

    def _contains_article_text(self, text: str) -> bool:
        """
        カテゴリ名に記事のテキストが含まれているかどうかを判定する。

        Args:
            text (str): 判定対象のテキスト。

        Returns:
            bool: 記事のテキストが含まれている場合は True、含まれていない場合は False。
        """
        # 記事のテキストに関連するキーワードリスト
        article_keywords = ["記事", "テキスト"]
        return any(keyword in text for keyword in article_keywords)

    # ----------------------- 本文と見出しの抽出 -----------------------
    def extract_text(self, normalize_text: bool = True, remove_exclude_words: bool = True) -> Dict[str, List[Dict[str, Union[str, List[str]]]]]:
        """
        Wikipedia ページの本文と見出しを抽出する。

        Args:
            normalize_text (bool, optional): テキストを正規化するかどうか。デフォルトは True。
            remove_exclude_words (bool, optional): 除外ワードを削除するかどうか。デフォルトは True。

        Returns:
            Dict[str, List[Dict[str, Union[str, List[str]]]]]: 見出しと本文を格納した辞書。

        Raises:
            ValueError: HTMLコンテンツが存在しない場合。
        """
        logger.info("本文と見出し抽出開始")
        if not self.page_content:
            logger.error(Config._FETCH_PAGE_DATA_ERROR_MESSAGE)
            raise ValueError(Config._FETCH_PAGE_DATA_ERROR_MESSAGE)

        if self.soup is None:
            self.soup = BeautifulSoup(self.page_content, 'lxml')

        self._remove_unnecessary_elements(self.soup)
        sections = self._extract_headings_and_body(self.soup)
        sections = self._remove_excluded_sections(sections)

        if normalize_text:
            processed_sections = self._post_process_text_for_category(sections)
        else:
            processed_sections = sections

        if remove_exclude_words:
            processed_sections = self._remove_exclude_words_for_category(processed_sections)

        logger.info("本文と見出し抽出完了")
        return {"sections": processed_sections}

    def _remove_unnecessary_elements(self, soup: BeautifulSoup):
        """
        BeautifulSoup オブジェクトから不要な HTML 要素を削除する。

        Args:
            soup (BeautifulSoup): BeautifulSoup オブジェクト。
        """
        logger.debug("不要要素削除開始")

        # 指定されたタグを削除
        for tag_name in Config.UNNECESSARY_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # コメントを削除
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # 無視するクラスを持つ要素を削除
        for class_name in Config.IGNORE_CLASSES:
            for tag in soup.find_all(class_=class_name):
                tag.decompose()

        logger.debug("不要要素削除完了")

    def _extract_headings_and_body(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        BeautifulSoup オブジェクトから階層的な見出し (h2, h3, h4) と本文を抽出する。
        テキスト分析しやすいフラットなリスト構造で出力する。
        """
        logger.debug("フラットなリスト構造での見出しと本文抽出開始 (カテゴリテキスト対応)")
        sections: List[Dict[str, Any]] = []
        h2_heading_divs = soup.find_all('div', class_='mw-heading mw-heading2')

        for h2_heading_div in h2_heading_divs:
            section_data_h2 = self._extract_section_content_with_category(h2_heading_div, [])
            if section_data_h2:
                sections.append(section_data_h2)
                h3_sections = self._extract_h3_sections(h2_heading_div)
                if h3_sections:
                    sections.extend(h3_sections)

        logger.debug("フラットなリスト構造での見出しと本文抽出完了 (カテゴリテキスト対応)")
        return sections

    def _extract_h3_sections(self, h2_heading_div: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        h2 見出しの次の h3 および h4 見出しまでのセクションを抽出する。

        Args:
            h2_heading_div (BeautifulSoup): h2 見出しの div 要素。

        Returns:
            List[Dict[str, Any]]: h3 および h4 見出しのセクションデータのリスト。
        """
        sections: List[Dict[str, Any]] = []
        next_sibling = h2_heading_div.find_next_sibling()
        current_category_path = [h2_heading_div.get_text(strip=True)]

        while next_sibling and not self._is_h2_heading(next_sibling):
            if self._is_h3_heading(next_sibling):
                section_data_h3 = self._extract_section_content_with_category(next_sibling, current_category_path)
                if section_data_h3:
                    sections.append(section_data_h3)
                    h4_sections = self._extract_h4_sections(next_sibling,
                                                            current_category_path + [next_sibling.get_text(strip=True)])
                    if h4_sections:
                        sections.extend(h4_sections)
            next_sibling = next_sibling.find_next_sibling()

        return sections

    def _extract_h4_sections(self, h3_heading_div: BeautifulSoup, current_category_path: List[str]) -> List[
        Dict[str, Any]]:
        """
        h3 見出しの次の h4 見出しまでのセクションを抽出する。

        Args:
            h3_heading_div (BeautifulSoup): h3 見出しの div 要素。
            current_category_path (List[str]): 現在のカテゴリパス。

        Returns:
            List[Dict[str, Any]]: h4 見出しのセクションデータのリスト。
        """
        sections: List[Dict[str, Any]] = []
        next_sibling = h3_heading_div.find_next_sibling()

        while next_sibling and not self._is_h3_heading(next_sibling):
            if self._is_h4_heading(next_sibling):
                section_data_h4 = self._extract_section_content_with_category(next_sibling, current_category_path)
                if section_data_h4:
                    sections.append(section_data_h4)
            next_sibling = next_sibling.find_next_sibling()

        return sections

    def _is_h2_heading(self, sibling: BeautifulSoup) -> bool:
        """
        sibling が h2 見出しの div 要素であるかを判定する。
        """
        return sibling.name == 'div' and 'mw-heading' in sibling.get('class', []) and 'mw-heading2' in sibling.get(
            'class', [])

    def _is_h3_heading(self, sibling: BeautifulSoup) -> bool:
        """
        sibling が h3 見出しの div 要素であるかを判定する。
        """
        return sibling.name == 'div' and 'mw-heading' in sibling.get('class', []) and 'mw-heading3' in sibling.get(
            'class', [])

    def _is_h4_heading(self, sibling: BeautifulSoup) -> bool:
        """
        sibling が h4 見出しの div 要素であるかを判定する。
        """
        return sibling.name == 'div' and 'mw-heading' in sibling.get('class', []) and 'mw-heading4' in sibling.get(
            'class', [])

    def _extract_section_content_with_category(self, heading_div_h: BeautifulSoup, category_path: List[str]) -> Dict[
        str, Any]:
        """
        セクション (h2, h3, h4) の内容を抽出する共通メソッド (カテゴリテキスト対応)。
        フラットなリスト構造のセクションデータを作成する。

        Args:
            heading_div_h (BeautifulSoup): 見出しの div 要素。
            category_path (List[str]): カテゴリパス。

        Returns:
            Dict[str, Any]: 抽出されたセクションデータ。
        """
        text_content_list: List[str] = []
        sibling = heading_div_h.find_next_sibling()
        next_heading_levels = Config.HEADING_LEVELS
        current_heading_level_class = self.get_heading_level_class(heading_div_h)
        current_heading_level = heading_div_h.find('h2') or heading_div_h.find('h3') or heading_div_h.find('h4')
        heading_level_tag = current_heading_level.name if current_heading_level else 'h2'
        heading_text = self._extract_heading_text(heading_div_h, heading_level_tag)

        # Clean category text
        cleaned_category_path = [self._clean_text(text) for text in category_path + [heading_text]]
        heading_level = int(heading_level_tag[1]) if heading_level_tag else 2

        sibling_processors = {
            '_is_h3_heading': self._process_h3_section_with_category,
            '_is_h4_heading': self._process_h4_section_with_category,
        }
        sections: List[Dict[str, Any]] = []

        current_content_siblings = []
        temp_sibling = heading_div_h.find_next_sibling()
        while temp_sibling:
            if self._is_next_heading_level(temp_sibling, next_heading_levels, current_heading_level_class):
                break
            current_content_siblings.append(temp_sibling)
            temp_sibling = temp_sibling.find_next_sibling()

        for current_content_sibling in current_content_siblings:
            sub_section_data = self._process_sibling_element_with_category(current_content_sibling, sibling_processors,
                                                                           cleaned_category_path)
            if sub_section_data:
                sections.append(sub_section_data)
            elif self._is_paragraph_element(current_content_sibling):
                paragraph_text = self._extract_paragraph_text(current_content_sibling)
                if paragraph_text:
                    section_data = {
                        "category_texts": cleaned_category_path,
                        "heading_level": heading_level + 1,
                        "heading_text": None,
                        "text": paragraph_text
                    }
                    sections.append(section_data)
            elif current_content_sibling.name == 'figure':
                figure_text = str(current_content_sibling)
                section_data = {
                    "category_texts": cleaned_category_path,
                    "heading_level": heading_level + 1,
                    "heading_text": "Figure",
                    "text": figure_text
                }
                sections.append(section_data)
            else:
                other_text = current_content_sibling.get_text(separator=" ", strip=True)
                if other_text:
                    section_data = {
                        "category_texts": cleaned_category_path,
                        "heading_level": heading_level + 1,
                        "heading_text": None,
                        "text": other_text
                    }
                    sections.append(section_data)

        section_text_content_list = []
        for section_item in sections:
            if section_item["heading_text"] is None and section_item["text"]:
                section_text_content_list.append(section_item["text"])
        text_content = "\n".join(section_text_content_list).strip()

        section_data = {
            "category_texts": cleaned_category_path[:-1],
            "heading_level": heading_level,
            "heading_text": heading_text,
            "text": text_content
        }
        logger.debug(f"デバッグ type of section_data before return: {type(section_data)}")
        return section_data

    def _clean_text(self, text: str) -> str:
        """
        テキストを正規化し不要な記号・文字列を削除する。

        Args:
            text (str): 正規化対象のテキスト。

        Returns:
            str: 正規化されたテキスト。
        """
        text = self._normalize_text(text)
        text = self._remove_unnecessary_chars(text)
        text = self._normalize_spacing(text)
        text = FullWidthConverter.convert_to_fullwidth(text)  # 全角に統一
        return text

    def _process_sibling_element_with_category(self, sibling: BeautifulSoup, sibling_processors: Dict[str, Any],
                                               category_path: List[str]) -> Optional[Dict[str, Any]]:
        """
        sibling 要素の種類を判定し、対応する処理を行う (カテゴリテキスト対応)。

        Args:
            sibling (BeautifulSoup): sibling 要素。
            sibling_processors (Dict[str, Any]): sibling 要素の処理関数の辞書。
            category_path (List[str]): 親セクションまでのカテゴリテキストのリスト。

        Returns:
            Optional[Dict[str, Any]]: サブセクションデータ (h3, h4) または None。
        """
        for check_func_name, process_func in sibling_processors.items():
            if getattr(self, check_func_name)(sibling):
                return process_func(sibling, category_path)
        return None

    def _is_paragraph_element(self, sibling: BeautifulSoup) -> bool:
        """
        sibling が 本文要素 (p, ul, div, blockquote, table, dl, ol) であるかを判定する。

        Args:
            sibling (BeautifulSoup): sibling 要素。

        Returns:
            bool: sibling が本文要素である場合は True、そうでない場合は False。
        """
        return sibling.name in ['p', 'ul', 'div', 'blockquote', 'table', 'dl', 'ol'] or (
                    sibling.name == 'div' and 'mw-parser-output' in sibling.get('class', []))

    def _extract_paragraph_text(self, sibling: BeautifulSoup) -> str:
        """
        sibling 要素から本文テキストを抽出する。

        Args:
            sibling (BeautifulSoup): sibling 要素。

        Returns:
            str: 抽出された本文テキスト。
        """
        return sibling.get_text(separator=" ", strip=True)

    def _is_next_heading_level(self, sibling: BeautifulSoup, next_heading_levels: List[str],
                               current_heading_level_class: Optional[str]) -> bool:
        """
        sibling が次の見出しレベルの div 要素であるかを判定する。

        Args:
            sibling (BeautifulSoup): sibling 要素。
            next_heading_levels (List[str]): 次の見出しレベルのリスト。
            current_heading_level_class (Optional[str]): 現在の見出しレベルクラス。

        Returns:
            bool: sibling が次の見出しレベルの div 要素である場合は True、そうでない場合は False。
        """
        sibling_heading_level_class = self.get_heading_level_class(sibling)
        if sibling_heading_level_class is None:
            return False
        if current_heading_level_class is None:
            return False

        current_level_index = Config.HEADING_LEVELS.index(current_heading_level_class)
        sibling_level_index = Config.HEADING_LEVELS.index(sibling_heading_level_class)

        return sibling_level_index <= current_level_index

    def get_heading_level_class(self, heading_div: BeautifulSoup) -> Optional[str]:
        """
        見出し div 要素から見出しレベルクラス (例: 'mw-heading2') を取得する。

        Args:
            heading_div (BeautifulSoup): 見出しの div 要素。

        Returns:
            Optional[str]: 見出しレベルクラス、見出しレベルクラスが見つからない場合は None。
        """
        for level_class in Config.HEADING_LEVELS:
            if level_class in heading_div.get('class', []):
                return level_class
        return None

    def _process_h3_section_with_category(self, sibling: BeautifulSoup, category_path: List[str]) -> Dict[str, Any]:
        """
        h3 セクションの抽出処理を行う (カテゴリテキスト対応)。

        Args:
            sibling (BeautifulSoup): h3 セクションの div 要素。
            category_path (List[str]): カテゴリパス。

        Returns:
            Dict[str, Any]: 抽出された h3 セクションデータ。
        """
        return self._extract_section_content_with_category(sibling, category_path)

    def _process_h4_section_with_category(self, sibling: BeautifulSoup, category_path: List[str]) -> Dict[str, Any]:
        """
        h4 セクションの抽出処理を行う (カテゴリテキスト対応)。

        Args:
            sibling (BeautifulSoup): h4 セクションの div 要素。
            category_path (List[str]): カテゴリパス。

        Returns:
            Dict[str, Any]: 抽出された h4 セクションデータ。
        """
        return self._extract_section_content_with_category(sibling, category_path)

    def _extract_heading_text(self, heading_div: BeautifulSoup, heading_level_tag: str) -> str:
        """
        見出し div 要素から見出しテキストを抽出する。

        Args:
            heading_div (BeautifulSoup): 見出しの div 要素。
            heading_level_tag (str): 見出しタグ ('h2', 'h3', 'h4')。

        Returns:
            str: 見出しテキスト、見出しタグが見つからない場合は空文字列。
        """
        heading_tag: Optional[Tag] = heading_div.find(heading_level_tag)
        return heading_tag.get_text(strip=True) if heading_tag else ""

    def _remove_excluded_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        指定されたキーワードを含むセクションを抽出結果から削除する。

        Args:
            sections (List[Dict[str, Any]]): 抽出されたセクションデータのリスト。

        Returns:
            List[Dict[str, Any]]: 指定されたキーワードを含まないセクションデータのリスト。
        """
        logger.debug("不要セクション削除開始")
        excluded_section_keywords = self.excluded_section_keywords
        processed_sections: List[Dict[str, Any]] = []

        for section in sections:
            logger.debug(f"デバッグ section data in _remove_excluded_sections: {section}")
            logger.debug(f"デバッグ type of section['category_texts']: {type(section['category_texts'])}")
            heading_text_list = section["category_texts"][-1:] if section["category_texts"] else [
                section["heading_text"]]
            heading_text = heading_text_list[0] if heading_text_list else ""

            if any(keyword in heading_text for keyword in excluded_section_keywords):
                logger.debug(f"セクション '{heading_text}' を排除")
                continue

            processed_sections.append(section)

        logger.debug("不要セクション削除完了")
        return processed_sections

    # ----------------------- テキストの後処理 -----------------------

    def _post_process_text_for_category(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        抽出されたテキストに対して、正規化や不要な記号の削除などの後処理を行う (カテゴリテキスト対応)。

        Args:
            sections (List[Dict[str, Any]]): 処理前のセクションデータのリスト。

        Returns:
            List[Dict[str, Any]]: 後処理済みのセクションデータのリスト。
        """
        logger.debug("テキスト後処理開始 (カテゴリテキスト対応)")
        processed_sections: List[Dict[str, Any]] = []
        for section in sections:
            processed_section = self._process_section_text_for_category(section)
            processed_sections.append(processed_section)
        logger.debug("テキスト後処理完了 (カテゴリテキスト対応)")
        return processed_sections

    def _process_section_text_for_category(self, section: Dict[str, Any]) -> Dict[str, Any]:
        """
        セクションテキストの後処理 (正規化、不要記号削除、空白処理) を行う (カテゴリテキスト対応)。

        Args:
            section (Dict[str, Any]): 処理対象のセクションデータ。

        Returns:
            Dict[str, Any]: 後処理済みのセクションデータ。
        """
        heading_text: str = section["heading_text"]
        text_content: str = section["text"]

        heading_text = self._normalize_text(heading_text)
        text_content = self._normalize_text(text_content)

        heading_text = self._remove_unnecessary_chars(heading_text)
        text_content = self._remove_unnecessary_chars(text_content)

        heading_text = self._normalize_spacing(heading_text)
        text_content = self._normalize_spacing(text_content)

        heading_text = FullWidthConverter.convert_to_fullwidth(heading_text)  # 全角に統一
        text_content = FullWidthConverter.convert_to_fullwidth(text_content)  # 全角に統一

        return {
            "category_texts": section["category_texts"],
            "heading_level": section["heading_level"],
            "heading_text": heading_text,
            "text": text_content,
        }

    def _normalize_text(self, text: str) -> str:
        """
        テキストを正規化する (NFKC 形式)。

        Args:
            text (str): 正規化対象のテキスト。

        Returns:
            str: 正規化されたテキスト。
        """
        return unicodedata.normalize("NFKC", text)

    def _remove_unnecessary_chars(self, text: str) -> str:
        """
        テキストから不要な記号・文字列 (セクション編集リンク、脚注・出典記号) を削除する。

        Args:
            text (str): 不要記号削除対象のテキスト。

        Returns:
            str: 不要記号が削除されたテキスト。
        """
        text = re.sub(r"\[編集\]", "", text)
        text = re.sub(r"\[\d+\]|\[要出典\]", "", text)
        pattern = r"[!\"#$%&'()*+,\-./:;<=>?@[\\\]^_`{|}~！”＃＄％＆’（）＊＋，－．／：；＜＝＞？＠「￥」＾＿‘｜’｛｝～©®…—–]"
        text = re.sub(pattern, "", text)
        return text

    def _normalize_spacing(self, text: str) -> str:
        text = re.sub(Config.FULL_WIDTH_SPACE, " ", text).strip()
        text = re.sub(r'\s+', ' ', text)  # 連続する空白文字（タブ、改行含む）を一つの半角スペースに置換
        return text

        # ----------------------- 不要ワードの削除 -----------------------

    def _remove_exclude_words_for_category(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        抽出されたテキストから不要な単語を削除する (カテゴリテキスト対応)。

        Args:
            sections (List[Dict[str, Any]]): 処理前のセクションデータのリスト。

        Returns:
            List[Dict[str, Any]]: 不要な単語が削除されたセクションデータのリスト。
        """
        logger.debug("不要ワード削除開始 (カテゴリテキスト対応)")
        processed_sections: List[Dict[str, Any]] = []
        for section in sections:
            processed_section = self._process_exclude_words_in_section_for_category(section)
            processed_sections.append(processed_section)
        logger.debug("不要ワード削除完了 (カテゴリテキスト対応)")
        return processed_sections

    def _process_exclude_words_in_section_for_category(self, section: Dict[str, Any]) -> Dict[str, Any]:
        """
        セクション内のテキストから不要な単語を削除する (カテゴリテキスト対応)。

        Args:
            section (Dict[str, Any]): 処理対象のセクションデータ。

        Returns:
            Dict[str, Any]: 不要な単語が削除されたセクションデータ。
        """
        heading_text: str = section["heading_text"]
        text_content: str = section["text"]

        heading_text = self._remove_words(heading_text, self.exclude_words)
        text_content = self._remove_words(text_content, self.exclude_words)

        return {
            "category_texts": section["category_texts"],
            "heading_level": section["heading_level"],
            "heading_text": heading_text,
            "text": text_content,
        }

    def _remove_words(self, text: str, words_to_remove: List[str]) -> str:
        """
        テキストから指定された単語リストに含まれる単語を削除する。

        Args:
            text (str): 処理対象のテキスト。
            words_to_remove (List[str]): 削除する単語のリスト。

        Returns:
            str: 不要な単語が削除されたテキスト。
        """
        combined_pattern = "|".join(re.escape(word) for word in words_to_remove)
        text = re.sub(combined_pattern, "", text)
        return text

    # ----------------------- JSON保存 -----------------------

    def save_infobox_data(self):
        """
        Infobox データを保存するメソッド。
        """
        infobox_data = self.extract_infobox_data()
        DataSaver.save_data(infobox_data, "s_infobox")

    def save_text_data(self):
        """
        テキストデータを保存するメソッド。
        """
        text_data = self.extract_text()
        DataSaver.save_data(text_data, "text")

# ----------------------- メイン処理 (Example Usage) -----------------------
if __name__ == "__main__":
    page_titles = [
        "アルベルト・アインシュタイン",
        "マリ・キュリー",
        "スティーブ・ジョブズ"
    ]

    for page_title in page_titles:
        scraper = Scraper(page_title=page_title)

        try:
            scraper.fetch_page_data()

            scraper.save_infobox_data()
            scraper.save_text_data()

            image_data = scraper.extract_image_data()
            print("Image Data:")
            print(f"取得した画像数: {len(image_data)}")
            print(json.dumps(image_data, indent=2, ensure_ascii=False))
            print("\n" + "=" * 50 + "\n")

            categories = scraper.extract_categories()
            print("Categories:")
            print(json.dumps(categories, indent=2, ensure_ascii=False))
            print("\n" + "=" * 50 + "\n")

        except ValueError as e:
            print(f"スクレイピング中にエラーが発生しました: {e}")