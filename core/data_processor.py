import pandas as pd
import spacy
from core.scraper import Scraper
from typing import List, Dict, Tuple
from collections import defaultdict
from utils.logger import configure_logging, get_logger
import logging
import sys
import re
import dateparser
from fuzzywuzzy import fuzz
import MeCab

spacy.prefer_gpu()
configure_logging(level=logging.DEBUG, stream=sys.stdout)
logger = get_logger(__name__)

mecab = MeCab.Tagger("-Owakati") # MeCab の初期化をグローバルスコープに移動 (extract_rule_based_entities_dict でも使用するため)

class DataProcessor:
    """
    人物データ処理クラス。

    scraper: Scraper
        Scraperオブジェクト
    nlp: spacy.lang.ja.Japanese
        spaCy日本語モデル
    name: str
        人物名
    text_data: dict
        スクレイピングしたテキストデータ
    image_data: list
        スクレイピングした画像データ
    infobox_data: dict
        スクレイピングしたinfoboxデータ
    categories: list
        スクレイピングしたカテゴリデータ
    headings_and_text: list
        テキストデータから抽出した見出しと本文のリスト
    entities: Dict[str, DefaultDict[str, int]]
        抽出されたエンティティ (名詞、固有表現)
    """

    def __init__(self, page_title: str):
        """
        DataProcessor オブジェクトの初期化。

        Args:
            page_title (str): Wikipedia ページタイトル
        """
        self.scraper = Scraper(page_title=page_title)
        self.nlp = spacy.load("ja_ginza_bert_large")
        self.name = page_title
        self.text_data = None
        self.image_data = None
        self.infobox_data = None
        self.categories = None
        self.headings_and_text = None #  初期化
        self.entities = defaultdict(lambda: defaultdict(int))  #  初期化と defaultdict の defaultdict に変更 # 修正
        logger.info("DataProcessorオブジェクトを初期化しました。", page_title=page_title)

        # MeCab-IPADIC-NEologd を使用する MeCab Tagger を初期化 **←  MeCab-IPADIC-NEologd 用 Tagger を初期化**
        try:
            self.mecab_neologd = MeCab.Tagger(
                "-Owakati -d //wsl.localhost/Ubuntu/usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd"  #  辞書パスは環境に合わせて調整
            )
            logger.info("MeCab-IPADIC-NEologd の初期化に成功しました。") #  ログ出力
        except RuntimeError as e:
            logger.error(f"MeCab-IPADIC-NEologd の初期化に失敗しました: {e}") #  エラーログ出力
            logger.error("ルールベース NER (辞書検索) はスキップされます。") #  エラーログ出力
            self.mecab_neologd = None #  初期化失敗時は None を設定


    def fetch_data(self):
        """
        Scraper を使用して Wikipedia ページからデータを取得し、
        各属性に格納する。
        """
        logger.info("データ取得開始", page_title=self.name)
        self.scraper.fetch_page_data()  # ページデータを取得
        self.text_data = self.scraper.extract_text()
        self.image_data = self.scraper.extract_image_data()
        self.infobox_data = self.scraper.extract_infobox_data()
        self.categories = self.scraper.extract_categories()
        self.headings_and_text = self.text_data["headings_and_text"] #  取得
        logger.info("データ取得完了", page_title=self.name)

    def process_data(self):
        """
        取得したデータを処理し、エンティティを抽出する。
        """
        logger.info("データ処理開始", page_title=self.name)
        if self.text_data is None:
            self.fetch_data()  # データがまだ取得されていない場合は取得

        #  headings_and_text を生成・設定 # 追記
        self.headings_and_text = self.scraper.extract_text()  # scraper.extract_text() を呼び出し headings_and_text を取得

        self.entities = self.extract_entities()  # エンティティ抽出処理を実行 # 修正
        logger.info("データ処理完了", page_title=self.name)

    def _format_value(self, value):
        """
        値を整形するヘルパー関数。
        リストの場合は文字列に結合する。

        Args:
            value: 整形対象の値 (str, list, etc.)

        Returns:
            str: 整形後の値
        """
        if isinstance(value, list):
            return ", ".join(value)
        return value

    def create_basic_info_dataframe(self):
        """
        基本情報辞書をPandas DataFrameに変換 & 整形する。

        Returns:
            pandas.DataFrame: 基本情報 DataFrame
        """
        logger.info("基本情報DataFrame作成開始")
        # keyと表示名の対応 (必要に応じて追加・変更)
        key_map = {
            "名前": "name",
            "生誕": "birth_date",
            "死没": "death_date",
            "出生": "birth_place",
            "死没地": "death_place",
            "居住": "residence",
            "国籍": "nationality",
            "出身校": "alma_mater",
            "学位": "degree",
            "研究分野": "field",
            "研究機関": "institutions",
            "主な業績": "notable_works",
            "主な受賞歴": "awards",
            "配偶者": "spouse",
            "子供": "children",
            "博士論文": "doctoral_thesis",
            "博士課程指導教員": "doctoral_advisor",
            "署名": "signature",
            "他の指導教員": "other_advisors",  # 追加
            "影響を与えた人物": "influenced"  # 追加
        }
        logger.debug(f"key_map: {key_map}")  # key_map の内容を出力

        formatted_basic_info = {}

        # infobox データの処理
        if self.infobox_data:
            for key, value in self.infobox_data.items():
                logger.debug(f"  infobox key: {key}")  # infobox_data のキーを出力
                if key == "image_url":
                    formatted_basic_info["image_url"] = value
                elif key == "名前":
                    formatted_basic_info["name"] = self._format_value(value.get("名前"))
                elif key in key_map:
                    new_key = key_map[key]
                    # 辞書型ならそのvalue
                    if isinstance(value, dict):
                        formatted_basic_info[new_key] = self._format_value(list(value.values())[0])  # ヘルパー関数を使用
                    # リスト型ならそのまま
                    else:
                        formatted_basic_info[new_key] = self._format_value(value)
                else:
                    logger.warning(f"基本情報に不明なキーがあります: {key}")  # 警告レベルに変更

        # 画像データの追加
        if self.image_data:  # image_data が空リストでないか確認
            if "image_url" in self.image_data[0]:  # image_url キーが存在するか確認
                formatted_basic_info["image_url"] = self.image_data[0]["image_url"]
            else:
                formatted_basic_info["image_url"] = None  # キーが存在しない場合は None を設定

            if "alt_text" in self.image_data[0]:  # alt_text キーが存在するか確認
                formatted_basic_info["image_caption"] = self.image_data[0]["alt_text"]
            else:
                formatted_basic_info["image_caption"] = None  # キーが存在しない場合は None を設定
        else:
            formatted_basic_info["image_url"] = None  # image_data が空リストの場合は None を設定
            formatted_basic_info["image_caption"] = None  # image_data が空リストの場合は None を設定

        # カテゴリ
        formatted_basic_info["categories"] = self.categories

        # 名前の整形
        if "name" in formatted_basic_info:
            formatted_basic_info["name"] = self._format_name(formatted_basic_info["name"])

        df = pd.DataFrame([formatted_basic_info])
        logger.info("基本情報DataFrame作成完了")
        return df

    def extract_timeline(self):
        """
        年表を抽出する (順序付きリスト形式の年表を想定)。

        Returns:
            pandas.DataFrame: 年表データフレーム (年、出来事)
        """
        logger.info("年表抽出開始 (順序付きリスト形式)") #  ログメッセージを修正
        df_timeline = pd.DataFrame(columns=["年", "出来事"]) #  年表データフレームを初期化

        timeline_section = self.scraper.soup.find("h2", id="年譜") #  id="年譜" の h2 要素 (年譜セクション見出し) をfind
        if timeline_section: #  年譜セクション見出しが存在する場合のみ処理
            timeline_ol = timeline_section.find_next_sibling("div", class_="mw-parser-output").find("ol") #  年譜セクション見出しの次の div.mw-parser-output 内の ol 要素 (年表リスト) をfind
            if timeline_ol: #  年表リスト ol が存在する場合のみ処理
                li_elements = timeline_ol.find_all("li") #  年表リスト ol 内の li 要素 (各年と出来事) をfind_all
                for li_element in li_elements: #  年表リスト li 要素をループ処理
                    b_element = li_element.find("b") #  li 要素内の b 要素 (年) をfind
                    if b_element: #  b 要素 (年) が存在する場合のみ処理
                        year = b_element.text.strip() #  b 要素から年を取得し、strip() で空白除去
                        event = "" #  出来事を初期化
                        #  b 要素 (年) の次の要素から出来事をテキストとして取得 (兄弟要素をnext_siblingsでループ)
                        for sibling in b_element.next_siblings:
                            if sibling.name is None: #  NavigableString (テキスト) の場合
                                event += sibling.strip() #  テキストをstrip() で空白除去して追加
                            elif sibling.name == "br": #  <br> タグの場合 (改行)
                                event += "\n" #  改行文字を追加
                            #  必要に応じて他の要素 (例: <a>, <span> など) の処理を追加

                        if year and event: #  年と出来事が取得できた場合のみデータフレームに追加
                            df_timeline = pd.concat([df_timeline, pd.DataFrame([{"年": year, "出来事": event}])], ignore_index=True) #  データフレームに追加

        logger.info("年表抽出完了 (順序付きリスト形式)") #  ログメッセージを修正
        return df_timeline

    def extract_relations(self):
        """
        本文から人物間の関係を抽出する。
        **係り受け解析を利用**

        Returns:
            list: 人物関係リスト (tuple)
                (人物1, 人物2, 関係の種類) の形式
        """
        logger.info("人物関係抽出開始")
        if not self.entities:
            logger.warning("固有表現が抽出されていません。")
            return []

        if "人名" not in self.entities:
            logger.warning("人物名の固有表現が抽出されていません。")
            return []

        person_names = self.entities["人名"]
        relations = []
        person_name_list = list(person_names.keys())  # 人名リストをリスト型で取得 # 追加

        # 全文をテキストとして取得
        all_text = ""
        for section in self.text_data["headings_and_text"]:
            logger.debug(f"section のキー: {section.keys()}")  # デバッグログ: section のキーを出力
            #  修正: section["heading"] -> section.get("heading_text", "")
            all_text += section.get("heading_text", "") + " "  # 修正: .get() を使用
            all_text += section["text_content"] + " "  # text_content に変更 **重要**

        # 文単位で分割
        sentences = re.split(r'[。！？]', all_text)
        for sentence in sentences:  # 変数名変更 (sent -> sentence)
            # 文中に2人以上のPERSONが存在するかどうか
            sentence_person_entities = []  # 文書中から抽出されたPERSONエンティティを格納するリスト # 追加
            doc = self.nlp(sentence)  # 変数名変更 (sent -> sentence)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    sentence_person_entities.append(ent.text)  # 文書中のPERSONエンティティをリストに追加 # 追加

            if len(sentence_person_entities) < 2:  # 文中に2人以上のPERSONが存在するかどうか # 修正
                continue

            # spacyで文を解析
            for i in range(len(sentence_person_entities)):  # あいまい一致で人物名比較 # 修正
                for j in range(i + 1, len(sentence_person_entities)):  # あいまい一致で人物名比較 # 修正
                    person1_name = sentence_person_entities[i]  # あいまい一致で人物名比較 # 修正
                    person2_name = sentence_person_entities[j]  # あいまい一致で人物名比較 # 修正

                    # あいまい一致で人名がperson_names (extract_entitiesで抽出された人名リスト) に含まれるか確認 # 追加
                    person1_candidate = None
                    person2_candidate = None
                    for extracted_name in person_name_list:  # 抽出された人名リストから候補を検索 # 追加
                        if fuzz.partial_ratio(person1_name, extracted_name) >= 80:  # 類似度80%以上を閾値とする (調整可能) # 追加
                            person1_candidate = extracted_name  # 候補が見つかったら格納 # 追加
                            break  # 最初に見つかった候補を採用 # 追加
                    for extracted_name in person_name_list:  # 抽出された人名リストから候補を検索 # 追加
                        if fuzz.partial_ratio(person2_name, extracted_name) >= 80:  # 類似度80%以上を閾値とする (調整可能) # 追加
                            person2_candidate = extracted_name  # 候補が見つかったら格納 # 追加
                            break  # 最初に見つかった候補を採用 # 追加

                    if person1_candidate and person2_candidate:  # 両方の人物候補が見つかった場合のみ関係抽出 # 追加
                        # 関係の種類を判定 (係り受け解析)
                        relation_type = self._determine_relation_type(person1_candidate, person2_candidate,
                                                                        doc)  # 候補名で関係抽出 # 修正
                        if relation_type:  # 関係性が特定できた場合のみ追加
                            relations.append((person1_candidate, person2_candidate, relation_type))  # 候補名で関係を登録 # 修正

        logger.info("人物関係抽出完了")
        return relations

    def _format_name(self, name):
        """
        名前を整形する (日本語/英語表記対応)。
        例:  "アインシュタイン, アルベルト/Albert Einstein" -> "アインシュタイン/Albert Einstein"

        Args:
            name (str): 整形前の名前

        Returns:
            str: 整形後の名前
        """
        if isinstance(name, str):
            match = re.match(r"([ァ-ヶー]+)[\s・]*([A-Za-z].*)", name)
            if match:
                japanese_name = match.group(1)
                english_name = match.group(2)
                return f"{japanese_name}/{english_name}"
        return name

    def extract_entities(self) -> Dict[str, defaultdict[str, int]]:
        """
        GiNZAとルールベースで、本文全体から固有表現抽出を行う。
        """
        logger.info("固有表現抽出開始")  # 開始ログを追加

        if not self.text_data or not self.text_data['headings_and_text']:  # text_data が空の場合はエラー # 追記
            logger.error(
                "テキストデータがありません。fetch_data() または process_data() を実行してください。")  # エラーログ出力 # 追記
            raise ValueError(
                "テキストデータがありません。fetch_data() または process_data() を実行してください。")  # エラーをraise # 追記

        all_entities = defaultdict(lambda: defaultdict(int))  # defaultdict の defaultdict
        mecab = MeCab.Tagger("-Owakati") #  標準 MeCab を使用 (形態素解析用)

        logger.debug(
            f"text_data のキー: {self.text_data.keys() if self.text_data else None}")  # text_data のキーをログ出力 # 修正
        if self.text_data and 'headings_and_text' in self.text_data:  # text_data と headings_and_text が存在する場合のみ # 修正
            logger.debug(
                f"text_data['headings_and_text'] の長さ: {len(self.text_data['headings_and_text'])}")  # text_data['headings_and_text'] の長さをログ出力 # 修正
            if self.text_data['headings_and_text']:  # headings_and_text が空リストでない場合のみ # 修正
                for i, section in enumerate(self.text_data['headings_and_text']):  # enumerate でインデックス付きループ # 修正
                    logger.debug(f"セクション {i} のキー: {section.keys()}")  # セクション (辞書) のキーをログ出力 # 修正
                    if 'heading_text' in section:  # heading_text キーが存在する場合のみ # 修正
                        logger.debug(f"処理中のセクション: {section['heading_text']}")  # 処理中のセクション名をログ出力 # 修正
                    else:  # heading_text キーが存在しない場合 # 修正
                        logger.debug(f"セクション {i} に 'heading_text' キーが存在しません")  # 警告ログを出力 # 修正
                    section_text = section.get("text_content", "")  # text_content が存在しない場合は空文字を代入 # 修正
                    logger.debug(f"セクションテキストの長さ: {len(section_text)}")  # セクションテキストの長さをログ出力 # 修正
                    logger.debug(
                        f"spaCy 入力テキスト (セクション '{section.get('heading_text', 'No Heading')}') : {section_text[:30]}...")  # spaCy 入力テキスト (先頭100文字) を DEBUG レベルでログ出力 # 追加 **重要**
                    doc = self.nlp(section_text)
                    logger.debug(
                        f"spaCy 入力テキスト (セクション '{section.get('heading_text', 'No Heading')}') : {section_text[:100]}...")  # spaCy 入力テキスト (先頭100文字) を DEBUG レベルでログ出力 # 追加 **重要**
                    entity_list = [(ent.text, ent.label_) for ent in doc.ents]  # 抽出された固有表現リストを作成 # 追加
                    person_entities = [(ent.text, ent.label_, ent.root.pos_) for ent in doc.ents if
                                       ent.label_ == "PERSON"]  # PERSON の固有表現リストを作成 # 追加
                    logger.debug(
                        f"spaCy 抽出結果 (セクション '{section.get('heading_text', 'No Heading')}') : 抽出数={len(entity_list)}, PERSONのみ={person_entities}")  # spaCy 抽出結果 (抽出数と PERSON のみ) を DEBUG レベルでログ出力 # 修正 **重要**
                    logger.debug(f"doc.ents の内容: {doc.ents}")  # doc.ents の内容をログ出力 # 追加  **重要**
                    for token in doc:  # 修正: doc.tokens -> doc
                        if token.pos_ == "NOUN":
                            all_entities["名詞"][token.text] += 1
                    for ent in doc.ents:
                        logger.debug(
                            f"抽出された固有表現: text='{ent.text}', label_='{ent.label_}', pos_='{ent.root.pos_}'")  # ログ出力追加
                        if ent.label_ == "PERSON":  # フィルタリングを全解除 # 修正 (条件式を削除)
                            mecab_result = mecab.parse(ent.text).strip()  # MeCab で形態素解析 # 追加  **重要: -Owakati オプション**
                            logger.debug(
                                f"MeCab 解析結果: text='{ent.text}', result='{mecab_result}'")  # MeCab 解析結果を DEBUG レベルでログ出力 # 追加 **重要**
                            all_entities["人名"][ent.text] += 1
                        elif ent.label_ == "ORG":
                            all_entities["組織"][ent.text] += 1
                        elif ent.label_ == "LOC":
                            all_entities["地名"][ent.text] += 1
                        elif ent.label_ == "DATE":
                            all_entities["日付"][ent.text] += 1
                        elif ent.label_ == "GPE":  # GPE (国・都市・州) を地名として扱う場合
                            all_entities["地名"][ent.text] += 1
                        #  以下に 固有表現 のカウント処理を追加 (例:  ent.label_ が固有表現を表すタイプの場合)
                        #  **重要: キーを "固有表現" に指定**
                        else:  # PERSON, ORG, LOC, DATE, GPE 以外のエンティティタイプを「固有表現」として扱う場合 (例)
                            all_entities["固有表現"][ent.text] += 1  # キーを "固有表現" に修正

                #  ルールベース NER (辞書検索)  **←  ルールベース NER (辞書検索) を追加**
                rule_based_entities_dict = self.extract_rule_based_entities_dict(section_text) #  辞書検索で人名抽出 **←  修正: section_text を渡す**
                for person_name in rule_based_entities_dict:
                    all_entities["人名"][person_name] += 1
                    logger.debug(f"ルールベース (辞書: MeCab-IPADIC-NEologd) 抽出: text='{person_name}'") #  ルールベース (辞書) の抽出結果をログ出力

                #  ルールベース NER (正規表現)  **←  ルールベース NER (正規表現) は一旦コメントアウト**
                # rule_based_entities_regex = self.extract_rule_based_entities_regex(self.wiki_doc.content) #  正規表現で人名抽出
                # for person_name in rule_based_entities_regex:
                #     all_entities["人名"][person_name] += 1
                #     logger.warning(f"ルールベース (正規表現) 抽出: text='{person_name}'") #  ルールベース (正規表現) の抽出結果をログ出力

            else:  # text_data または headings_and_text が存在しない場合 # 修正
                logger.debug("text_data または 'headings_and_text' が空です")  # 警告ログを出力 # 修正

        logger.info("固有表現抽出完了")  # 完了ログを追加
        return all_entities

    def extract_rule_based_entities_dict(self, text: str) -> list[str]:
        """
        ルールベース NER (辞書検索) で人名を抽出する (MeCab-IPADIC-NEologd 使用)。
        """
        if self.mecab_neologd is None: # MeCab-IPADIC-NEologd の初期化に失敗している場合は空リストを返す # 追記
            logger.warning("MeCab-IPADIC-NEologd が初期化されていません。ルールベース NER (辞書検索) をスキップします。") # 警告ログ出力 # 追記
            return [] # 空リストを返す # 追記

        extracted_names = []
        node = self.mecab_neologd.parseToNode(text) #  MeCab-IPADIC-NEologd でテキストを解析 # 修正
        while node:
            features = node.feature.split(",") #  品詞情報を取得
            if features[0] == "名詞" and features[1] == "固有名詞" and features[2] == "人名": #  品詞が「名詞-固有名詞-人名」の場合
                extracted_names.append(node.surface) #  表層形 (単語) を人名として抽出
                logger.debug(f"ルールベース (辞書: MeCab-IPADIC-NEologd) 抽出: text='{node.surface}', 品詞='{','.join(features[:3])}'") #  ログ出力 (DEBUG レベル)
            node = node.next
        return extracted_names

    def extract_rule_based_entities_regex(self, text: str) -> list[str]:
        """
        ルールベース NER (正規表現) で人名を抽出する。
        """
        extracted_names = []
        patterns = [
            r"([一-龯]{1,})\s([一-龯]{1,})",  #  漢字の姓と名の間に空白
            r"([一-龯]{1,})先生",  #  漢字の姓 + 先生
            r"([一-龯]{1,})氏",  #  漢字の姓 + 氏
            r"([A-Z][a-z]+)\s([A-Z][a-z]+)",  #  英語の姓と名
            #  必要に応じて正規表現パターンを追加
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                extracted_names.append(match.group(0)) #  マッチした文字列全体を人名として抽出
        return extracted_names

    def _determine_relation_type(self, person1: str, person2: str, doc: spacy.tokens.doc.Doc) -> str:
        """
        係り受け解析に基づき、2つの人名間の関係の種類を判定する。

        Args:
            person1 (str): 人物1の名前
            person2 (str): 人物2の名前
            doc (spacy.tokens.doc.Doc): spaCy Docオブジェクト (文単位)

        Returns:
            str: 関係の種類 (例: "指導教員", "兄弟", "不明")、関係性が特定できない場合は None
        """
        #  (係り受け解析処理は変更なし)
        return None #  一旦 None を返すように変更 (ダミー)


    def analyze_persona(self) -> Dict[str, List[Tuple[str, int]]]:
        """
        人物像分析を実行し、名詞と固有表現の上位エンティティを抽出する。

        Returns:
            Dict[str, List[Tuple[str, int]]]: 分析結果 (辞書形式)
                キー: "名詞", "固有表現"
                値: 各エンティティタイプの上位エンティティリスト
        """
        logger.info("人物像分析開始", page_title=self.name)
        if self.entities is None: #  entities が None の場合のエラー処理 # 追記
            logger.error("エンティティが抽出されていません。process_data() を実行してください。") # loguru logger # 追記
            raise ValueError("エンティティが抽出されていません。process_data() を実行してください。") # エラーをraise # 追記


        top_nouns = self.get_top_entities("名詞")
        top_entities = self.get_top_entities("固有表現")

        persona_analysis = {
            "名詞": top_nouns,
            "固有表現": top_entities,
        }
        logger.info("人物像分析完了", page_title=self.name)
        return persona_analysis

    def format_analysis_results(self, analysis_results: Dict[str, List[Tuple[str, int]]]) -> str:
        """
        人物像分析結果を整形されたテキスト形式で出力する。

        Args:
            analysis_results (Dict[str, List[Tuple[str, int]]]): 分析結果 (辞書形式)

        Returns:
            str: 整形された分析結果 (テキスト形式)
        """
        logger.info("分析結果整形開始", page_title=self.name)
        formatted_text = f"人物名: {self.name}\n\n"
        for entity_type, top_entities in analysis_results.items():
            formatted_text += f"--- 上位の{entity_type} ---\n"
            for entity, count in top_entities:
                formatted_text += f"- {entity}: {count}回\n"
            formatted_text += "\n"
        logger.info("分析結果整形完了", page_title=self.name)
        return formatted_text

    def get_top_entities(self, entity_type: str, top_n: int = 10) -> List[Tuple[str, int]]:
        """
        指定されたエンティティタイプの上位エンティティを取得する。

        Args:
            entity_type (str): エンティティタイプ ("名詞", "固有表現" など)
            top_n (int): 上位何件を取得するか (デフォルト: 10)

        Returns:
            List[Tuple[str, int]]: 上位エンティティのリスト ( (エンティティ名, 出現回数) のタプル)
        """
        if entity_type not in self.entities:
            logger.warning(f"エンティティタイプ '{entity_type}' は存在しません。")
            return []

        entities_of_type = self.entities[entity_type]
        sorted_entities = sorted(entities_of_type.items(), key=lambda item: item[1], reverse=True) #  出現回数で降順ソート
        return sorted_entities[:top_n] #  上位 top_n 件を返す


if __name__ == "__main__":
    from utils.logger import configure_logging, get_logger
    import logging
    import sys

    configure_logging(level=logging.DEBUG, stream=sys.stdout)
    logger = get_logger(__name__)

    page_title = "アルベルト・アインシュタイン"  #  例: アルベルト・アインシュタイン

    try:
        processor = DataProcessor(page_title=page_title)
        processor.fetch_data()
        processor.process_data() #  process_data() を実行 # 追記
        analysis_results = processor.analyze_persona()
        formatted_results = processor.format_analysis_results(analysis_results)

        print("--- 人物像分析結果 ---")
        print(formatted_results)

    except ValueError as e:
        logger.error(f"データ処理中にエラーが発生しました: {e}")
    except Exception as e:
        logger.exception(f"予期せぬエラーが発生しました: {e}")