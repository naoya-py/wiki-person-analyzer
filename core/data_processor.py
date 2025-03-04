import spacy
import pandas as pd
import re
import ginza
from dateutil.parser import parse
from utils.logger import configure_logging, get_logger
import logging
import sys

configure_logging(level=logging.DEBUG, stream=sys.stdout)
logger = get_logger(__name__)


class DataProcessor:
    """
    スクレイピングしたデータを整形・加工するクラス。
    """

    def __init__(self, infobox_data, text_data, image_data, categories, page_title):
        """
        コンストラクタ。

        Args:
            infobox_data (dict): Scraper.extract_infobox_data() からの出力 (基本情報)。
            text_data (dict): Scraper.extract_text() からの出力 (本文テキスト, 見出し)。
            image_data (list): Scraper.extract_image_data() からの出力 (画像URL, キャプション)
            categories (list): Scraper.extract_categories() からの出力 (カテゴリ)
            page_title (str): ページタイトル
        """
        self.infobox_data = infobox_data
        self.text_data = text_data
        self.image_data = image_data
        self.categories = categories
        self.page_title = page_title
        self.df_basic = None
        self.df_timeline = None
        self.df_network = None
        self.entities = None
        self.nlp = spacy.load("ja_ginza_electra")
        ginza.set_split_mode(self.nlp, "C")  # 分割単位を最大に
        logger.debug("DataProcessorオブジェクトを初期化しました。")

    def process_data(self):
        """
        データの整形・加工を行うメインメソッド。
        各データ処理メソッドを呼び出し、DataFrame を生成する。
        """
        logger.info("データ処理開始")
        self.df_basic = self.create_basic_info_dataframe()
        self.entities = self.extract_entities()
        self.df_timeline = self.extract_timeline()
        self.df_network = self.extract_network() #  TODO:  後で実装
        logger.info("データ処理完了")

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

    def concatenate_text_data(self) -> str:
        """text_data (抽出された本文と見出し) を一つの文字列に連結する。"""
        logger.info("text_data を連結して一つのテキストデータを作成")
        concatenated_text = ""

        if not self.text_data or not self.text_data[
            'headings_and_text']:  # text_data または headings_and_text が None/空の場合は空文字列を返す
            logger.warning("text_data が空です。空文字列を返します。")
            return ""

        for section in self.text_data['headings_and_text']:
            logger.debug(f"concatenate_text_data: section の内容: {section}")  # 追加: section の内容をログ出力 # 追加
            heading_text = section.get('heading_text')  # 修正: .get('heading_text') を使用 (KeyError 回避)
            text_content = section['text_content']  # text_content は必須キーと想定

            if heading_text:  # 見出しがある場合
                concatenated_text += f"## {heading_text}\n\n{text_content}\n\n"  # Markdown形式
            else:  # 見出しがない場合 (概要など)
                concatenated_text += f"{text_content}\n\n"  # 見出しなしで本文のみ連結

        logger.debug(f"連結後のテキストデータ (冒頭100文字): {concatenated_text[:100]}")  # 連結後テキストデータ (冒頭100文字) をログ出力
        logger.info("テキストデータの連結処理完了")
        return concatenated_text

    def concatenate_text_data_recursive(self, sub_sections): #  再帰呼び出し用ヘルパー関数を追加 # 追記
        """
        (内部用) サブセクションのテキストデータを再帰的に結合するヘルパー関数.

        Args:
            sub_sections (List[Dict]): サブセクションの構造化データ.

        Returns:
            str: 結合されたテキストデータ.
        """
        combined_text = ""
        for section in sub_sections: #  sub_sections をループ処理 # 修正
            heading_text = section["heading"]
            text_content = section["text"]

            combined_text += heading_text + " " + text_content + " " # 見出しと本文を結合

            if "sub sections" in section: #  section でチェック # 修正
                sub_sections_text = self.concatenate_text_data_recursive(section["sub sections"]) #  再帰呼び出し
                combined_text += sub_sections_text #  サブセクションのテキストも結合
        return combined_text


    def extract_entities(self):
        """
        GiNZAを使って、本文全体から固有表現抽出を行う。
        """
        logger.info("固有表現抽出開始")

        # テキストデータを結合 # 追記
        all_text = self.concatenate_text_data() #  concatenate_text_data メソッドを呼び出す # 追記
        for section in self.text_data["headings_and_text"]:
            all_text += section.get("heading", "") + "\n"
            all_text += section.get("text", "") + "\n"

        # ページタイトルを人名としてルール追加
        ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        patterns = [{"label": "PERSON", "pattern": self.page_title}]
        ruler.add_patterns(patterns)

        doc = self.nlp(all_text)
        entities = {}
        for ent in doc.ents:
            label = ent.label_
            if label not in entities:
                entities[label] = []
            entities[label].append(ent.text)
        logger.info("固有表現抽出完了")
        return entities

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

        if "PERSON" not in self.entities:
            logger.warning("人物名の固有表現が抽出されていません。")
            return []

        person_names = self.entities["PERSON"]
        relations = []

        # 全文をテキストとして取得
        all_text = ""
        for section in self.text_data["headings_and_text"]:
            all_text += section["heading"] + " "
            all_text += section["text"] + " "

        # 文単位で分割
        sentences = re.split(r'[。！？]', all_text)
        for sentence in sentences: #  変数名変更 (sent -> sentence)
            # 文中に2人以上のPERSONが存在するかどうか
            person_in_sentence = [person for person in person_names if person in sentence] #  変数名変更 (sent -> sentence)
            if len(person_in_sentence) < 2:
                continue

            # spacyで文を解析
            doc = self.nlp(sentence) #  変数名変更 (sent -> sentence)
            for ent1 in doc.ents:
                if ent1.label_ == "PERSON" and ent1.text in person_names:
                    for ent2 in doc.ents:
                        if ent2.label_ == "PERSON" and ent2.text in person_names and ent1 != ent2:
                            # 関係の種類を判定 (係り受け解析)
                            relation_type = self._determine_relation_type(ent1.text, ent2.text, doc)
                            if relation_type: # 関係性が特定できた場合のみ追加
                                relations.append((ent1.text, ent2.text, relation_type))

        logger.info("人物関係抽出完了")
        return relations

    def extract_timeline(self):
        """
        本文から年表を抽出する。
        「年譜」「年表」「略歴」などの見出しがあるセクションから年を抽出する。
        詳細年表抽出機能(extract_detailed_timeline)と統合。

        Returns:
            pandas.DataFrame: 年表 DataFrame (year, date, event カラム)
        """
        logger.info("年表抽出開始")
        timeline = []
        if not self.text_data:
            logger.warning("本文データがありません。")
            return pd.DataFrame(columns=["year", "date", "event"])
        for section in self.text_data["headings_and_text"]:
            heading = section["heading"]
            text = section["text"]
            # 見出しに「年譜」「年表」「略歴」が含まれているか確認
            if "年" in heading or "歴" in heading:
                # 年を抽出(4桁 or 2桁 + "年代" or 世紀)
                years = re.findall(r"(\d{4}年代?|\d{2}年代?|\d{1,2}世紀)", heading + text) # 見出しからも年号を抽出
                if years:
                    for year in set(years): #  重複年号を削除
                        # 出来事を抽出(セクションテキスト)
                        events = [text] # セクション全体をイベントとして登録
                        for event in events:
                            timeline.append({"year": year, "date": "", "event": event})


        # 詳細な年表抽出
        detailed_timeline = self.extract_detailed_timeline()
        if not detailed_timeline.empty:
            timeline.extend(detailed_timeline.to_dict("records")) #  辞書型データ対応

        logger.info("年表抽出完了")

        # 重複を削除
        timeline_df = pd.DataFrame(timeline)
        timeline_df.drop_duplicates(subset=["year", "date", "event"], inplace=True)

        return timeline_df

    def extract_detailed_timeline(self):
        """
        本文全体から詳細な年表を抽出する。
        **年代、世紀表記に対応**

        Returns:
            pandas.DataFrame: 詳細年表 DataFrame (year, date, event カラム)
        """
        logger.info("詳細な年表抽出開始")
        detailed_timeline = []
        all_text = ""
        for section in self.text_data["headings_and_text"]:
            all_text += section["heading"] + " "
            all_text += section["text"] + " "

        sentences = re.split(r'[。！？]', all_text)
        for sentence in sentences:
            # 年号の正規表現パターンを修正 (年代、世紀に対応)
            year_match = re.search(r"(\d{4}年代?|\d{2}年代?|\d{1,2}世紀)年?|(\d{4})年(\d{1,2})月", sentence)
            if year_match:
                if year_match.group(1): #  年代、世紀
                    year = year_match.group(1)
                elif year_match.group(2): #  年
                    year = year_match.group(2)
                else:
                    year = None #  念のため year を None で初期化

                if year and year_match.group(3): #  年、月
                    month = year_match.group(3)
                    date_str = f"{year}年{month}月"
                    date = self.normalize_date(date_str)  # 日付を正規化
                elif year: # 年のみ
                    date_str = f"{year}年"
                    date = self.normalize_date(date_str) # 日付を正規化
                else:
                    date = "" #  日付がない場合は空文字

                event = sentence
                detailed_timeline.append({"year": year, "date": date, "event": event})
        logger.info("詳細な年表抽出完了")
        return pd.DataFrame(detailed_timeline)

    def normalize_date(self, date_str):
        """
        日付文字列を正規化する関数。
        dateutil.parser.parse を使用して日付を解析し、"YYYY-MM-DD" 形式に変換する。
        **fuzzy オプションを False に設定**

        Args:
            date_str (str): 正規化対象の日付文字列

        Returns:
            str: 正規化後の日付文字列 (YYYY-MM-DD 形式)
                 解析失敗時は "不明" を返す
        """
        try:
            date = parse(date_str, fuzzy=False) #  fuzzy_parser を False に設定
            return date.strftime('%Y-%m-%d')  # 〇〇〇〇年〇〇月〇〇日形式に変換
        except ValueError:
            return "不明"

    @staticmethod
    def convert_to_ce(year_str):
        """
        紀元前 (BC) の年表記を西暦 (CE) に変換する関数。
        例:  "紀元前100年" -> "-100", "1990年" -> "1990"

        Args:
            year_str (str): 変換対象の年文字列 (紀元前 or 西暦)

        Returns:
            str: 西暦表記の年文字列
        """
        if "紀元前" in year_str or "BC" in year_str:
            year_str = re.sub(r"[^0-9]", "", year_str)
            year = int(year_str)
            return f"-{year}"
        return year_str

    def extract_network(self):
        """
        人物間のネットワークデータ (共演関係など) を抽出する (未実装)。
        TODO:  人物ネットワーク抽出処理を実装

        Returns:
            pandas.DataFrame: 人物ネットワーク DataFrame (未実装、空の DataFrame を返す)
        """
        # 後で修正
        logger.info("人物ネットワーク抽出開始 (未実装)")
        return pd.DataFrame()

    def _determine_relation_type(self, person1, person2, doc):
        """
        人物間の関係の種類を文脈から判断する。
        **係り受け解析を利用して関係性を判定**
        **判定できる関係の種類:  師弟関係、夫婦、親子関係、同僚、不明**

        Args:
            person1 (str): 人物1の名前
            person2 (str): 人物2の名前
            doc (spacy.tokens.Doc): 関係性を判断する文の SpaCy Docオブジェクト

        Returns:
            str: 関係の種類 (例: "師弟関係", "夫婦", "同僚", "親子関係", "不明")
        """
        # doc (spacy doc) から person1, person2 の spacy.tokens.Span を取得
        person_span1 = None
        person_span2 = None
        for ent in doc.ents:
            if ent.label_ == "PERSON" and ent.text == person1:
                person_span1 = ent
            if ent.label_ == "PERSON" and ent.text == person2:
                person_span2 = ent

        if person_span1 is None or person_span2 is None:
            return "不明" #  Span が見つからない場合は不明

        # 係り受け解析で関係性を判断するロジックを実装 (例:  述語となる動詞、係り先などをチェック)
        for token in doc:
            if token.dep_ in ("ROOT", "主体", "述語") and token.pos_ in ("VERB", "NOUN", "ADJ"): #  文の主辞かつ動詞、名詞、形容詞
                # print(f"  述語となるトークン: {token.text}, dep_: {token.dep_}, pos_: {token.pos_}") #  デバッグ用
                for child in token.children: #  述語の係り受け先を確認
                    # print(f"    係り先: {child.text}, dep_: {child.dep_}, pos_: {child.pos_}") #  デバッグ用
                    if child == person_span1.root or child == person_span2.root: #  係り先が person1 or person2
                        if "師" in token.text or "教" in token.text: #  述語に「師」「教」が含まれる -> 師弟関係
                            return "師弟関係"
                        elif "結婚" in token.text or " супруг" in token.lemma_ or "妻" in token.text or "夫" in token.text: #  述語に「結婚」「 супруг」「妻」「夫」が含まれる -> 夫婦
                            return "夫婦"
                        elif "親子" in token.text or " родитель" in token.lemma_ or " родила" in token.lemma_ or " родил" in token.lemma_ or "父" in token.text or "母" in token.text or "息子" in token.text or "娘" in token.text: # 述語に「親子」「родитель」「родила」「родил」「父」「母」「息子」「娘」が含まれる -> 親子関係
                            return "親子関係"
                        elif "同僚" in token.text or " 共同研究" in token.text or " 協力" in token.lemma_: # 述語に「同僚」「共同研究」「協力」が含まれる -> 同僚
                            return "同僚"
        return "不明" #  上記以外は不明


if __name__ == "__main__":
    from core.scraper import Scraper
    import json

    # logger設定 (ファイルとコンソール出力)
    configure_logging(level=logging.DEBUG, stream=sys.stdout)

    page_title = "アルベルト・アインシュタイン" #  例: アルベルト・アインシュタイン
    scraper = Scraper(page_title=page_title)
    scraper.fetch_page_data()
    infobox_data = scraper.extract_infobox_data()
    text_data = scraper.extract_text(normalize_text=True, remove_exclude_words=True)
    image_data = scraper.extract_image_data()
    categories = scraper.extract_categories()

    processor = DataProcessor(
        infobox_data=infobox_data,
        text_data=text_data,
        image_data=image_data,
        categories=categories,
        page_title=page_title,
    )
    processor.process_data()

    print("\n--- 基本情報 DataFrame ---")
    print(processor.df_basic.to_json(orient="records", indent=2, force_ascii=False))

    print("\n--- 固有表現抽出結果 ---")
    print(json.dumps(processor.entities, ensure_ascii=False, indent=2))

    print("\n--- 人物関係抽出結果 ---")
    print(processor.extract_relations())

    print("\n--- 年表抽出結果 ---")
    print(processor.df_timeline.to_json(orient="records", indent=2, force_ascii=False))