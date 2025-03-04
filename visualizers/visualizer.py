import matplotlib.pyplot as plt
from wordcloud import WordCloud
import networkx as nx
import seaborn as sns
from utils.logger import configure_logging, get_logger
import logging
import sys

configure_logging(level=logging.INFO, stream=sys.stdout)
logger = get_logger(__name__)

class Visualizer:
    """
    データフレームを可視化するクラス。
    """

    def __init__(self, analyzer):
        """
        コンストラクタ。

        Args:
            analyzer (Analyzer): 分析済みデータを持つAnalyzerオブジェクト。
        """
        self.analyzer = analyzer
        self.figure = None  # figureオブジェクトを保持
        logger.debug("Visualizerオブジェクトを初期化しました。")

    def plot_timeline(self):
        """
        年表データをプロットする。
        """
        logger.info("年表プロット開始")
        if self.analyzer.df_timeline is None:
            logger.warning("年表データがNoneです。")
            return
        if self.analyzer.df_timeline.empty:
            logger.warning("年表データが空です。")
            return

        try:
            # 転換点を特定し、辞書に変換
            turning_points = self.analyzer.identify_turning_points()
            turning_points_dict = {str(year): event for year, event, _ in turning_points}

            # 活動期間を特定
            activity_periods = self.analyzer.detect_activity_periods()

            # 年表のプロット作成
            fig, ax = plt.subplots(figsize=(25, 12))  # 幅を広げた
            self.figure = fig  # figureオブジェクトを保存

            # 活動期間を強調表示
            for start_year, end_year in activity_periods:
                ax.axvspan(
                    start_year,
                    end_year,
                    alpha=0.2,
                    color="yellow",
                    label="活動期間" if start_year == activity_periods[0][0] else None,  # 最初の期間のみラベルを表示
                )

            # 年ごとにイベントをプロット
            for index, row in self.analyzer.df_timeline.iterrows():
                year = str(row["year"])
                date = row["date"]
                event = row["event"]
                x = int(year)
                y = index  # y軸の位置を調整

                # イベントタイプによるマーカーの設定
                if year in turning_points_dict:
                    # 転換点
                    ax.plot(x, y, "ro",
                            label="転換点" if "転換点" not in ax.get_legend_handles_labels()[1] else None)  # 追加
                    #yの値で配置を変える
                    if y % 2 == 0:
                            ax.annotate(
                            event, (x, y), textcoords="offset points", xytext=(10, 0), ha="left", fontsize=8,wrap=True
                        )
                    else:
                        ax.annotate(
                            event, (x, y), textcoords="offset points", xytext=(-10, 0), ha="right", fontsize=8,wrap=True#右配置
                        )
                else:
                    # 通常イベント
                    ax.plot(x, y, "bo",
                            label="イベント" if "イベント" not in ax.get_legend_handles_labels()[1] else None)  # 追加
                    #yの値で配置を変える
                    if y % 2 == 0:
                        ax.annotate(
                            event, (x, y), textcoords="offset points", xytext=(10, 0), ha="left", fontsize=8,wrap=True
                        )
                    else:
                        ax.annotate(
                            event, (x, y), textcoords="offset points", xytext=(-10, 0), ha="right", fontsize=8,wrap=True #右配置
                        )
            # x軸ラベルの調整
            min_year = min(self.analyzer.df_timeline["year"].astype(str).str.replace("-", "").astype(int))
            max_year = max(self.analyzer.df_timeline["year"].astype(str).str.replace("-", "").astype(int))
            ax.set_xlim(min_year - 5, max_year + 5)  # 範囲を広げた

            # 凡例の設定
            handles, labels = ax.get_legend_handles_labels()
            unique_labels = dict(zip(labels, handles))  # ラベルとハンドルを紐づけて重複を削除
            ax.legend(unique_labels.values(), unique_labels.keys())

            plt.xlabel("年")
            # plt.ylabel("イベント") # 必要に応じてコメントアウトを外す
            plt.yticks([])  # y軸ラベルを非表示にする。
            plt.title("年表")
            #plt.tight_layout() #コメントアウト
            plt.subplots_adjust(left=0.05, right=0.95) #調整
            logger.info("年表プロット完了")

        except ValueError as e:
            logger.error(f"プロット中にエラーが発生しました: {e}")
            self.figure = None  # プロットに失敗した場合はfigureをNoneにする

    def plot_network(self, target_person=None):
        """
        関係ネットワークをプロットする。seabornを使ってデザインを改善しました

        Args:
            target_person (str, optional): 関係を抽出する対象の人物名。デフォルトはNone。
        """
        logger.info("関係ネットワークプロット開始")
        network_analysis = self.analyzer.analyze_network(target_person)

        if network_analysis["graph"] is None:
            logger.warning("グラフデータがありません。関係ネットワークのプロットをスキップします。")
            return

        try:
            self.figure = plt.figure(figsize=(12, 10))  # figureオブジェクトを保存
            ax = self.figure.add_subplot(111)

            # seabornのスタイルを適用
            sns.set_style("whitegrid")

            # レイアウトを設定
            pos = nx.spring_layout(network_analysis["graph"], k=0.8, iterations=50)

            # ノードの色を調整 (中心性を利用)
            node_centrality = nx.degree_centrality(network_analysis["graph"])
            node_colors = [node_centrality[node] for node in network_analysis["graph"].nodes()]

            # ノードの描画 (中心性に応じた色のグラデーション)
            nodes = nx.draw_networkx_nodes(
                network_analysis["graph"],
                pos,
                node_color=node_colors,
                cmap=plt.cm.YlGnBu,
                node_size=2000,
                alpha=0.8,
            )

            # ノードの境界線を黒で設定
            nodes.set_edgecolor("k")

            # エッジの描画
            edges = nx.draw_networkx_edges(
                network_analysis["graph"],
                pos,
                width=2,
                alpha=0.5,
                edge_color="gray",
            )

            # ノードラベルの描画
            nx.draw_networkx_labels(
                network_analysis["graph"],
                pos,
                font_size=10,
                font_weight="bold",
                font_color="black",
            )

            # エッジラベルの描画
            edge_labels = nx.get_edge_attributes(network_analysis["graph"], "relation")
            nx.draw_networkx_edge_labels(
                network_analysis["graph"],
                pos,
                edge_labels=edge_labels,
                font_size=8,
                label_pos=0.3,
            )

            # タイトルと軸ラベル
            plt.title(f"{target_person}の関連人物ネットワーク", fontsize=16)
            plt.axis("off")  # 軸を非表示

            # カラーバーを追加（中心性に応じて）
            sm = plt.cm.ScalarMappable(cmap=plt.cm.YlGnBu, norm=plt.Normalize(vmin=min(node_colors), vmax=max(node_colors)))
            sm._A = []
            cbar = plt.colorbar(sm, ax=ax)
            cbar.set_label("中心性")

            plt.tight_layout()
            logger.info("関係ネットワークプロット完了")
        except Exception as e:
            logger.error(f"関係ネットワークのプロット中にエラーが発生しました: {e}")
            self.figure = None  # プロットに失敗した場合はfigureをNoneにする

    def create_wordcloud(self, text):
        """
        テキストからワードクラウドを作成し、表示する。

        Args:
            text (str): ワードクラウドの作成に使用するテキスト。
        """
        logger.info("ワードクラウド作成開始")
        if not text:
            logger.warning("テキストが空です。ワードクラウドの作成をスキップします。")
            return

        try:
            self.figure = plt.figure(figsize=(10, 8))  # figureオブジェクトを保存
            wordcloud = WordCloud(
                width=800,
                height=400,
                background_color="white",
                font_path="C:/Windows/Fonts/msgothic.ttc",
            ).generate(text)  # 日本語のフォントを指定
            plt.imshow(wordcloud, interpolation="bilinear")
            plt.axis("off")  # 軸を非表示
            plt.title("ワードクラウド")
            plt.tight_layout()

            logger.info("ワードクラウド作成完了")
        except Exception as e:
            logger.error(f"ワードクラウドの作成中にエラーが発生しました: {e}")
            self.figure = None  # 作成に失敗した場合はfigureをNoneにする