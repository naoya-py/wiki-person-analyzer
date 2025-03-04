import logging
import sys
import MeCab  # MeCabをインポート
import networkx as nx
import pandas as pd
import spacy
from dateutil.parser import parse
from sklearn.feature_extraction.text import TfidfVectorizer
from logger import configure_logging, get_logger
import dateparser

configure_logging(level=logging.INFO, stream=sys.stdout)
logger = get_logger(__name__)

class Analyzer:
    """
    データフレームを分析するクラス (spaCy ja_core_news_md, MeCab-ipadic-NEologd, scikit-learn 使用)。
    分かち書き処理、レンマタイズ・ステミング、品詞フィルタリング、TF-IDF計算機能を追加。
    """

    def __init__(self, df_basic, df_timeline, df_network):
        """
        コンストラクタ。

        Args:
            df_basic (pd.DataFrame): 基本情報データフレーム。
            df_timeline (pd.DataFrame): 年表データフレーム。
            df_network (pd.DataFrame): 関係ネットワークデータフレーム。
        """
        self.df_basic = df_basic
        self.df_timeline = df_timeline
        self.df_network = df_network
        self.graph = None  # 関係ネットワークのグラフ (NetworkX)
        self.nlp = spacy.load("ja_core_news_md")
        self.mecab = MeCab.Tagger("-Owakati")  # MeCab Wakati Taggerを初期化
        logger.debug("Analyzerオブジェクトを初期化しました (spaCy ja_core_news_md, MeCab使用)。")

    def analyze_basic_info(self):
        """基本情報の分析を行う。"""
        logger.info("基本情報の分析を開始します。")
        analysis_result = {}

        if "birth_date" not in self.df_basic.columns or "death_date" not in self.df_basic.columns:
            analysis_result["age"] = "計算不可"
            logger.warning("生年月日または没年月日がないため、年齢を計算できません。")
            return analysis_result

        try:
            birth_date = self._parse_date_dateparser(self.df_basic["birth_date"].iloc[0])
            death_date = self._parse_date_dateparser(self.df_basic["death_date"].iloc[0])
            if pd.isnull(birth_date) or pd.isnull(death_date):
                analysis_result["age"] = "計算不可"
                logger.warning("生年月日または没年月日が無効なため、年齢を計算できません。")
            else:
                age = death_date.year - birth_date.year - ((death_date.month, death_date.day) < (birth_date.month, birth_date.day))
                analysis_result["age"] = age
                analysis_result["birth_year"] = birth_date.year
                analysis_result["death_year"] = death_date.year
                logger.debug(f"年齢を計算しました: {age}")
        except (ValueError, TypeError) as e:
            analysis_result["age"] = "計算不可"
            logger.exception(f"年齢計算中にエラーが発生しました: {e}")
            raise

        logger.info("基本情報の分析が完了しました。")
        return analysis_result

    def _parse_date_dateparser(self, date_str):  # 関数名を変更 # 修正
        """
        日付文字列をdateparserでdatetime型に変換する。
        多言語対応の柔軟なパースが可能。
        パースできない場合はpd.NaTを返す。
        """
        if not isinstance(date_str, str):
            return pd.NaT
        try:
            date_obj = dateparser.parse(date_str, languages=['ja'])  # dateparser.parse を使用、language='ja' を指定 # 修正
            if date_obj:  # dateparser.parse は None を返す場合があるため、None 判定を追加 # 追記
                return date_obj
            else:
                return pd.NaT  # dateparser.parse が None を返した場合、pd.NaT を返す # 追記
        except (ValueError, TypeError):
            return pd.NaT

    def analyze_timeline(self, start_year=None, end_year=None):
        """
        年表の分析を行う。
        ... (後略)
        """
        logger.info(f"年表の分析を開始します。期間: {start_year} - {end_year}")

        if self.df_timeline is None or self.df_timeline.empty:
            logger.warning("年表データが空です。分析をスキップします。")
            return {"events_per_year": {}, "filtered_events": [], "activity_periods": [], "turning_points": [], "wakachi_events_mecab": {}}
        try: #  try-except ブロックを追加
            # 年ごとの出来事数を集計
            events_per_year = self.df_timeline["year"].value_counts().sort_index()
            logger.debug(f"年ごとの出来事数: \n{events_per_year}")

            # 特定の期間の出来事を抽出
            filtered_events = self.df_timeline.copy()
            if start_year:
                filtered_events = filtered_events[
                    filtered_events["year"].astype(str).str.replace("-", "").astype(int) >= int(start_year)]
            if end_year: filtered_events = filtered_events[filtered_events["year"].astype(str).str.replace("-", "").astype(int) <= int(end_year)]
            logger.debug(f"指定期間内の出来事: \n{filtered_events}")

            # 活動期間の特定
            activity_periods = self.detect_activity_periods()

            # 転換点の特定
            turning_points = self.identify_turning_points()

            # MeCabで分かち書き処理
            wakachi_events_mecab = self.wakachi_timeline_events_mecab()

            logger.info("年表の分析が完了しました。")
            return {"events_per_year": {str(year): int(count) for year, count in events_per_year.to_dict().items()}, "filtered_events": filtered_events.to_dict(orient='records'), "activity_periods": [(int(start), int(end)) for start, end in activity_periods], "turning_points": [(int(year), event, event_type) for year, event, event_type in turning_points], "wakachi_events_mecab": wakachi_events_mecab}
        except Exception as e: #  広範な例外をキャッチ
            logger.exception(f"年表分析中にエラーが発生しました: {e}")
            raise

    def detect_activity_periods(self):
        """
        年表データから活動期間を検出する (変更なし)。
        """
        logger.info("活動期間の検出を開始します。")
        if self.df_timeline.empty:
            logger.warning("年表データが空です。活動期間の検出をスキップします。")
            return []
        years = sorted(self.df_timeline["year"].astype(str).str.replace("-", "").astype(int).unique())
        periods = []
        start_year = None
        for i in range(len(years)):
            if start_year is None: start_year = years[i]
            if i + 1 < len(years) and years[i + 1] - years[i] > 3:  # 3年以内のギャップは結合
                periods.append((start_year, years[i]))
                start_year = None
        if start_year is not None:
            periods.append((start_year, years[-1]))
        logger.info(f"活動期間を検出しました。{periods}")
        return periods

    def identify_turning_points(self):
        """
        年表データから転換点を特定する (spaCy ja_core_news_md を使用)。
        イベント内容をspaCyで解析し、イベントタイプを判定する。
        """
        logger.info("転換点の特定を開始します (spaCy ja_core_news_md使用)。")
        turning_points = []

        for index, row in self.df_timeline.iterrows():
            event = row["event"]
            year = row["year"]

            # spaCyでイベント内容を解析
            doc = self.nlp(event)

            # イベントタイプを判定 (キーワードマッチングからspaCyの品詞情報などを活用した判定に変更も検討)
            event_type = self._determine_event_type_spacy(doc)  # spaCyでイベントタイプ判定

            if event_type:
                turning_points.append((year, event, event_type))

        logger.info("転換点を特定しました (spaCy ja_core_news_md使用)。")
        return turning_points

    def _determine_event_type_spacy(self, doc):
        """
        spaCyの解析結果からイベントタイプを判定する。
        (キーワードマッチングベース、必要に応じてルールベースや機械学習ベースに変更)
        """
        career_keywords = ["就任", "退任", "転職", "入社", "卒業", "入学", "就職", "退職", "異動", "昇進", "降格", "転籍", "出向"]
        success_keywords = ["受賞", "成功", "発表", "出版", "達成", "開発", "設立", "創設", "創立", "完成", "発売", "公開", "公開", "ヒット", "貢献", "寄与"]
        failure_keywords = ["失敗", "敗北", "撤退", "辞任", "逮捕", "解任", "辞職", "倒産", "解散", "炎上", "不祥事", "事故", "事件", "災害", "死去", "死亡", "解雇", "リストラ"]

        event_type = None
        for token in doc:
            if token.text in career_keywords:
                return "career_change"
            if token.text in success_keywords:
                return "success"
            if token.text in failure_keywords:
                return "failure"
        return event_type

    def wakachi_timeline_events_mecab(self):
        """
        年表データのイベント内容をMeCabで分かち書きする。

        Returns:
            dict: 分かち書きされたイベントリスト (dict: {year: [wakachi_tokens], ...})
        """
        logger.info("年表イベントの分かち書きを開始します (MeCab-ipadic-NEologd使用)。")
        wakachi_events_mecab = {}
        for index, row in self.df_timeline.iterrows():
            event = row["event"]
            year = row["year"]
            wakachi_events_mecab[year] = self.mecab.parse(event).strip().split()

        logger.info("年表イベントの分かち書きが完了しました (MeCab-ipadic-NEologd使用)。")
        return wakachi_events_mecab

    def analyze_text_features(self):  # テキスト特徴量分析関数 (修正版)
        """
        テキスト特徴量分析を行う (TF-IDF)。
        ... (後略)
        """
        logger.info("テキスト特徴量分析を開始します (TF-IDF, MeCab-ipadic-NEologd使用)。")
        tfidf_scores = {}  # TF-IDF スコアを格納する辞書

        # 年ごとのイベントテキストリストを作成
        year_event_texts = {}
        for year in sorted(self.df_timeline["year"].unique()):
            year_df = self.df_timeline[self.df_timeline["year"] == year]
            event_texts = year_df["event"].tolist()
            if event_texts: year_event_texts[year] = event_texts

        if not year_event_texts:
            logger.warning("分析対象となるイベントテキストが存在しません。テキスト特徴量分析をスキップします。")
            return {"tfidf_scores": {}}
        vectorizer = TfidfVectorizer(tokenizer=self.wakati_mecab, token_pattern=None)

        try:
            for year, event_texts in year_event_texts.items():
                logger.debug(f"年: {year} - イベントテキスト: {event_texts}")
                tfidf_matrix = vectorizer.fit_transform(event_texts)

                feature_names = vectorizer.get_feature_names_out()
                tfidf_scores[year] = {}
                for i in range(tfidf_matrix.shape[0]):
                    row = tfidf_matrix[i, :].toarray()[0]
                    for j, score in enumerate(row): tfidf_scores[year][feature_names[j]] = score

            logger.info("テキスト特徴量分析が完了しました (TF-IDF, MeCab-ipadic-NEologd使用)。")
            return {"tfidf_scores": tfidf_scores}

        except Exception as e:
            logger.exception(f"テキスト特徴量分析中にエラーが発生しました: {e}")
            raise

    def wakati_mecab(self, text):
        """
        MeCab-ipadic-NEologd を使用した tokenizer 関数 (TfidfVectorizer用)。
        レンマタイズ・品詞フィルタリング処理を追加。
        Args:
            text (str): 日本語テキスト。

        Returns:
            list: レンマタイズ・品詞フィルタリングされたトークンリスト。
        """
        return self.lemmatize_filter_mecab(text)

    def lemmatize_filter_mecab(self, text):
        """
        MeCab-ipadic-NEologd を使用したレンマタイズ・品詞フィルタリング関数 (新規追加)。
        ... (後略)
        """
        wakachi_result = self.mecab.parse(text)
        tokens = []
        print(f"\n--- 入力テキスト: {text} ---")
        for line in wakachi_result.splitlines():
            if line == "EOS": break
            parts = line.split("\t")
            if len(parts) < 2: continue
            surface = parts[0]
            features = parts[1].split(",")
            postag = features[0]
            base_form = features[6] if len(features) > 6 else surface
            print(f"表層形: {surface}, 品詞: {postag}, 原形: {base_form}")
            tokens.append(base_form)
        print(f"分かち書き結果 (レンマタイズ・品詞フィルタリング後): {tokens}")
        return tokens


    def analyze_network(self, target_person=None):
        """
        関係ネットワークの分析を行う (変更なし)。
        """
        logger.info(f"関係ネットワークの分析を開始します。対象: {target_person}")

        if self.df_network is None or self.df_network.empty:
            logger.warning("関係ネットワークデータが空です。")
            return {"graph": None, "related_persons": [], "relations_by_type": {}, "centrality": {}}
        try:
            self.graph = nx.from_pandas_edgelist(self.df_network, "source", "target", edge_attr="relation", create_using=nx.Graph())
            logger.debug(
                f"NetworkXグラフを作成しました。ノード数: {self.graph.number_of_nodes()}, エッジ数: {self.graph.number_of_edges()}"
            )

            related_persons = []
            if target_person and target_person in self.graph:
                related_persons = list(self.graph.neighbors(target_person))

            unique_related_persons = list(set(related_persons)); logger.debug(f"重複を削除した関連人物リスト: {unique_related_persons}")

            relations_by_type = {}
            for _, row in self.df_network.iterrows():
                relation_type = row["relation"]
                source = row["source"]
                target = row["target"]

                if relation_type not in relations_by_type:
                    relations_by_type[relation_type] = set()
                if source != target_person:
                    relations_by_type[relation_type].add(source)
                if target != target_person:
                    relations_by_type[relation_type].add(target)

            for relation_type, persons in relations_by_type.items(): relations_by_type[relation_type] = list(set(persons))
            logger.debug(f"重複を削除した関係の種類ごとの人物リスト: {relations_by_type}")

            centrality = {}
            if self.graph.number_of_nodes() > 0: centrality["degree_centrality"] = nx.degree_centrality(self.graph)
            logger.debug(f"中心性指標: {centrality}")

            logger.info("関係ネットワークの分析が完了しました。")
            return {"graph": self.graph, "related_persons": unique_related_persons, "relations_by_type": relations_by_type, "centrality": centrality}
        except Exception as e:
            logger.exception(f"関係ネットワーク分析中にエラーが発生しました: {e}")
            raise