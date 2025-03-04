from core.scraper import Scraper
from core.data_processor import DataProcessor
from core.analyzer import Analyzer
from visualizers.visualizer import Visualizer
from core.report_generator import ReportGenerator
import os
import datetime
from utils.logger import configure_logging, get_logger
import logging
import sys

configure_logging(level=logging.INFO, stream=sys.stdout)
logger = get_logger(__name__)


def main():
    """
    メインの処理を行う関数。
    """
    try:
        # 1. ユーザーから分析対象の人物名を入力
        page_title = input(
            "分析対象のWikipediaページタイトルを正確に入力してください (例: アルベルト・アインシュタイン): "
        )
        logger.info(f"User input: {page_title}")

        # 2. Scraperオブジェクトを作成
        scraper = Scraper(page_title)

        # 3. Wikipedia APIからページデータを取得
        scraper.fetch_page_data()

        # 4. 各種データ抽出
        infobox_data = scraper.extract_infobox_data()
        text_data = scraper.extract_text()
        image_data = scraper.extract_image_data()
        categories = scraper.extract_categories()

        # 5. DataProcessorオブジェクトを作成し、データ処理 (page_titleを渡す)
        processor = DataProcessor(
            infobox_data, text_data, image_data, categories, page_title
        )  # 引数を修正
        processor.process_data()  # データ処理実行　←　ここがコメントアウトされていたりしないか確認

        # 6. 各データフレームを取得 (process_dataメソッド内で処理されるようになった)
        df_basic = processor.df_basic
        df_timeline = processor.df_timeline
        df_network = processor.df_network

        # 7. Analyzerオブジェクトを作成
        analyzer = Analyzer(df_basic, df_timeline, df_network)

        # 8. Visualizerオブジェクトを作成
        visualizer = Visualizer(analyzer)

        # 9. 可視化 (ファイルパスを決定)
        # outputディレクトリが存在しない場合は作成
        output_dir = "data/output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"出力ディレクトリ '{output_dir}' を作成しました。")

        # 既存ファイルがあるか確認し、上書きするかどうかをユーザーに確認
        timeline_image_path = os.path.join(output_dir, "timeline.png")
        network_image_path = os.path.join(
            output_dir, f"network_{scraper.page_title}.png"
        )  # page_titleを使用
        wordcloud_image_path = os.path.join(output_dir, "wordcloud.png")
        report_path = os.path.join(output_dir, "report.html")

        if os.path.exists(report_path):
            print("data/output/ に既存のレポートがあります。上書きしますか？ (y/n)")
            overwrite = input().lower()
            if overwrite != "y":
                # 上書きしない場合は、ファイル名にタイムスタンプを追加
                now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                timeline_image_path = os.path.join(output_dir, f"timeline_{now}.png")
                network_image_path = os.path.join(
                    output_dir, f"network_{scraper.page_title}_{now}.png"
                )  # page_titleを使用
                wordcloud_image_path = os.path.join(
                    output_dir, f"wordcloud_{now}.png"
                )
                report_path = os.path.join(output_dir, f"report_{now}.html")
                logger.info(f"既存のレポートは上書きしません。新しいファイル名: {report_path}")
            else:
                logger.info("既存のレポートを上書きします。")
        else:
            logger.info(f"レポートの出力先: {report_path}")

        # 年表の可視化
        visualizer.plot_timeline()
        if visualizer.figure:  # 追加
            visualizer.figure.savefig(timeline_image_path)
            logger.info(f"年表画像を保存しました: {timeline_image_path}")
        else:
            logger.warning("年表の可視化に失敗したため、画像は保存されません。")

        # 関係ネットワークの可視化
        visualizer.plot_network(target_person=scraper.page_title)  # page_titleを使用
        if visualizer.figure:  # 追加
            visualizer.figure.savefig(network_image_path)
            logger.info(f"関係ネットワーク画像を保存しました: {network_image_path}")
        else:
            logger.warning("関係ネットワークの可視化に失敗したため、画像は保存されません。")

        # ワードクラウドの可視化
        # text_dataから本文を結合
        # body_text = " ".join(processor.text_data["body_text"]) #  エラー発生箇所 (body_textキーが存在しない)
        body_text_list = [item["text"] for item in processor.text_data["headings_and_text"]] # headings_and_text から text を抽出
        body_text = " ".join(body_text_list) #  抽出した text を結合
        visualizer.create_wordcloud(body_text)
        if visualizer.figure:  # 追加
            visualizer.figure.savefig(wordcloud_image_path)
            logger.info(f"ワードクラウド画像を保存しました: {wordcloud_image_path}")
        else:
            logger.warning("ワードクラウドの生成に失敗したため、画像は保存されません。")

        # 10. レポート生成に必要なデータをまとめる
        # data_processorでdf_basicがDataframeオブジェクトになっているので、to_dictで辞書型にする

        if df_basic.empty:
            report_data = {
                "person_name": scraper.page_title,
                "basic_info": {},  # 空の辞書
                "timeline": df_timeline.to_dict("records") if df_timeline is not None else [],
                "network": analyzer.analyze_network(target_person=scraper.page_title),
                "timeline_image": timeline_image_path,
                "network_image": network_image_path,
                "wordcloud_image": wordcloud_image_path,
            }
        else:
            if df_basic.empty:
                report_data = {
                    "person_name": scraper.page_title,
                    "basic_info": {},  # 空の辞書
                    "timeline": df_timeline.to_dict("records") if df_timeline is not None else [],
                    "network": analyzer.analyze_network(target_person=scraper.page_title),
                    "timeline_image": timeline_image_path,
                    "network_image": network_image_path,
                    "wordcloud_image": wordcloud_image_path,
                }
            else:
                report_data = {
                    "person_name": df_basic.iloc[0].get(
                        "name", scraper.page_title
                    ),  # dataframeから取得 #page_titleを使用
                    "basic_info": df_basic.iloc[0].to_dict(),  # dataframeから取得
                    "timeline": df_timeline.to_dict("records") if df_timeline is not None else [],
                    "network": analyzer.analyze_network(target_person=scraper.page_title),
                    "timeline_image": timeline_image_path,  # 変更されたパス
                    "network_image": network_image_path,  # 変更されたパス
                    "wordcloud_image": wordcloud_image_path,  # 変更されたパス
                }

        # 11. ReportGeneratorオブジェクトを作成
        report_generator = ReportGenerator()

        # 12. HTMLレポートを生成
        report_generator.generate_report(report_data, output_path=report_path)   # ファイルパスを渡す
        logger.info(f"HTMLレポートを生成しました: {report_path}")
    except Exception as e:
        logger.exception(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()