from scraper import Scraper
from data_processor import DataProcessor
from analyzer import Analyzer
from visualizer import Visualizer
from report_generator import ReportGenerator
from logger import logger

def main():
    """
    メインの処理を行う関数。
    """
    try:
        # 1. ユーザーから分析対象の人物名を入力
        page_title = input("分析対象のWikipediaページタイトルを入力してください: ")
        logger.info(f"User input: {page_title}")

        # 2. Scraperオブジェクトを作成
        scraper = Scraper(page_title)

        # 3. Wikipedia APIからページデータを取得
        scraper.fetch_page_data()

        # 4. 基本情報を抽出
        basic_info = scraper.extract_basic_info()

        # 5. 本文テキストを抽出
        text = scraper.extract_text()

        # 6. DataProcessorオブジェクトを作成し、データ処理
        processor = DataProcessor(basic_info, text)

        # 7. 各データフレームを取得
        df_basic = processor.create_basic_info_dataframe()
        cleaned_text = processor.clean_text()
        df_timeline = processor.extract_timeline()
        df_network = processor.extract_network()

        # 8. Analyzerオブジェクトを作成
        analyzer = Analyzer(df_basic, df_timeline, df_network)

        # 9. Visualizerオブジェクトを作成  <-- ここは修正不要
        visualizer = Visualizer(analyzer)

        # 10. 年表の可視化
        visualizer.plot_timeline()
        timeline_image_path = "data/output/timeline.png"
        visualizer.figure.savefig(timeline_image_path)

        # 11. 関係ネットワークの可視化
        target_person = basic_info.get("名前", page_title)
        visualizer.plot_network(target_person=target_person)
        network_image_path = f"data/output/network_{target_person}.png"
        visualizer.figure.savefig(network_image_path)

        # 12. ワードクラウドの可視化
        visualizer.create_wordcloud(cleaned_text)
        wordcloud_image_path = "data/output/wordcloud.png"
        visualizer.figure.savefig(wordcloud_image_path)

        # 13. レポート生成に必要なデータをまとめる
        report_data = {
            "person_name": basic_info.get("名前", page_title),
            "basic_info": basic_info,
            "timeline": df_timeline.to_dict("records"),
            "network": analyzer.analyze_network(target_person=target_person),
            "timeline_image": timeline_image_path,
            "network_image": network_image_path,
            "wordcloud_image": wordcloud_image_path,
        }

        # 14. ReportGeneratorオブジェクトを作成し、レポートを生成
        report_generator = ReportGenerator()
        report_generator.generate_report(report_data, output_path="data/output/report.html")
        logger.info(f"Report generated at: data/output/report.html")


    except ValueError as e:
        logger.error(f"ValueError: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()