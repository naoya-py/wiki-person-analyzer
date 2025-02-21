import pandas as pd
import networkx as nx

class Analyzer:
    """
    データフレームを分析するクラス。
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

    def analyze_basic_info(self):
        """
        基本情報の分析を行う。
        """
        analysis_result = {}

        # 例: 年齢計算 (生没年がある場合)
        if "生年月日" in self.df_basic.columns and "没年月日" in self.df_basic.columns:
            # 生年月日と没年月日をdatetime型に変換
            try:
                birth_date = pd.to_datetime(self.df_basic["生年月日"].iloc[0], errors='coerce')
                death_date = pd.to_datetime(self.df_basic["没年月日"].iloc[0], errors='coerce')
                if pd.notna(birth_date) and pd.notna(death_date):
                    age = (death_date - birth_date).days // 365
                    analysis_result["age"] = age
            except (ValueError, TypeError):
                analysis_result["age"] = "計算不可"
        return analysis_result

    def analyze_timeline(self, start_year=None, end_year=None):
        """
        年表の分析を行う。

        Args:
            start_year (int, optional): 抽出する期間の開始年。
            end_year (int, optional): 抽出する期間の終了年。

        Returns:
            dict: 分析結果。
                - "events_per_year": 年ごとの出来事数 (pd.Series)。
                - "filtered_events": 指定期間内の出来事 (pd.DataFrame)。
        """
        if self.df_timeline.empty:
            return {
                "events_per_year": pd.Series(dtype=int),
                "filtered_events": pd.DataFrame(columns=["year","date","event"])
            }
        # 年ごとの出来事数を集計
        events_per_year = self.df_timeline["year"].value_counts().sort_index()

        # 特定の期間の出来事を抽出
        filtered_events = self.df_timeline.copy()
        if start_year:
            filtered_events = filtered_events[filtered_events["year"] >= start_year]
        if end_year:
            filtered_events = filtered_events[filtered_events["year"] <= end_year]

        return {
            "events_per_year": events_per_year,
            "filtered_events": filtered_events,
        }

    def analyze_network(self, target_person=None):
        """
        関係ネットワークの分析を行う。

        Args:
            target_person (str, optional): 関係を抽出する対象の人物名。

        Returns:
            dict: 分析結果。
                - "related_persons": target_personと関係のある人物リスト (list)。
                - "relations_by_type": 関係の種類ごとの人物リスト (dict)。
                - (オプション) "centrality": ネットワークの中心性指標 (dict)。
        """
        if self.df_network.empty:
            return {
                "related_persons": [],
                "relations_by_type": {},
                "centrality": {},
                }

        # NetworkXグラフを作成 (無向グラフ)
        self.graph = nx.from_pandas_edgelist(self.df_network, "source", "target", edge_attr="relation", create_using=nx.Graph())

        # 特定の人物と関係のある人物をリストアップ
        related_persons = []
        if target_person and target_person in self.graph:
            related_persons = list(self.graph.neighbors(target_person))

        # 関係の種類ごとに人物を分類
        relations_by_type = {}
        for _, row in self.df_network.iterrows():
            relation_type = row["relation"]
            source = row["source"]
            target = row["target"]

            if relation_type not in relations_by_type:
                relations_by_type[relation_type] = set()
            # source, target両方
            if source != target_person:
                relations_by_type[relation_type].add(source)
            if target != target_person:
                relations_by_type[relation_type].add(target)

        # (オプション) 中心性指標を計算
        centrality = {}
        # 次数中心性、近接中心性、媒介中心性、固有ベクトル中心性
        if self.graph.number_of_nodes() > 0: # nodeが0だとエラーになるため
            centrality["degree_centrality"] = nx.degree_centrality(self.graph)
            # centrality["closeness_centrality"] = nx.closeness_centrality(self.graph) #時間かかる場合あり
            centrality["betweenness_centrality"] = nx.betweenness_centrality(self.graph)
            # centrality["eigenvector_centrality"] = nx.eigenvector_centrality(self.graph) #時間かかる場合あり

        return {
            "related_persons": related_persons,
            "relations_by_type": relations_by_type,
            "centrality": centrality,
        }