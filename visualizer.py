import matplotlib.pyplot as plt
import networkx as nx
from wordcloud import WordCloud, STOPWORDS
import seaborn as sns
from logger import logger


class Visualizer:
    """
    分析結果を可視化するクラス。
    """

    def __init__(self, analyzer):
        """
        コンストラクタ。

        Args:
            analyzer (Analyzer): Analyzerオブジェクト。
        """
        self.analyzer = analyzer
        self.figure = None

    def plot_timeline(self, start_year=None, end_year=None):
        """
        年表を棒グラフで可視化する (Seabornを使用)。
        """
        timeline_analysis = self.analyzer.analyze_timeline(start_year, end_year)
        events_per_year = timeline_analysis["events_per_year"]
        filtered_events = timeline_analysis["filtered_events"]

        plt.figure(figsize=(12, 6))
        plt.rcParams['font.family'] = 'Meiryo'

        # Seabornのbarplotを使用
        sns.barplot(x=events_per_year.index, y=events_per_year.values, color="skyblue", label="すべての年")

        # 特定期間のデータを強調表示
        if not filtered_events.empty:
            filtered_years = filtered_events["year"].unique()
            filtered_counts = events_per_year.loc[filtered_years]
            sns.barplot(x=filtered_counts.index, y=filtered_counts.values, color="orange", label=f"{start_year}-{end_year}")

        plt.xlabel("年")
        plt.ylabel("出来事の数")
        plt.title("年表 (出来事の数)")
        plt.grid(axis="y")
        plt.legend()
        plt.tight_layout()
        self.figure = plt
        # plt.show()

    def plot_network(self, target_person=None):
        """
        関係ネットワーク図を作成する (Seabornは使用しない)。
        """
        network_analysis = self.analyzer.analyze_network(target_person)
        graph = self.analyzer.graph

        if not graph:
            print("関係ネットワークがありません")
            return

        plt.figure(figsize=(10, 10))

        # レイアウトを決定 (スプリングレイアウト)
        pos = nx.spring_layout(graph, k=0.5, iterations=50)

        # ノードの描画
        nx.draw_networkx_nodes(graph, pos, node_color="skyblue", node_size=500)

        # エッジの描画
        nx.draw_networkx_edges(graph, pos, edge_color="gray")

        # ノードラベルとエッジラベルの描画
        nx.draw_networkx_labels(graph, pos, font_family='Meiryo', font_size=12)
        edge_labels = nx.get_edge_attributes(graph, "relation")
        nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_family='Meiryo')

        plt.title(f"関係ネットワーク (対象: {target_person})")
        plt.axis("off")
        plt.tight_layout()
        self.figure = plt
        # plt.show()

    def create_wordcloud(self, text):
        """
        ワードクラウドを作成する。
        """
        # 日本語のストップワードを追加
        stopwords = set(STOPWORDS)
        stopwords.update(["ある", "する", "いる", "ない", "ため", "こと", "もの", "これ","できる","れる","なる","よる","よっ","行わ","行っ","つい","中","的"])

        try:
            wordcloud = WordCloud(
                background_color="white",
                width=800,
                height=600,
                stopwords=stopwords,
                font_path='meiryo.ttc',  # フォント名を指定
            ).generate(text)

            plt.figure(figsize=(10, 8))
            plt.imshow(wordcloud, interpolation="bilinear")
            plt.axis("off")
            plt.tight_layout()
            self.figure = plt
            # plt.show()

        except Exception as e:
            logger.exception(f"ワードクラウド生成中にエラーが発生: {e}")
            self.figure = None  # エラーが発生した場合は None に設定