# Wikipedia Biography Analyzer (wiki-nlp-analyzer)

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://example.com)  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)  ## 概要

Wikipedia Biography Analyzer (WBA) は、Wikipediaの人物ページから情報を抽出し、分析・可視化するPythonプロジェクトです。
Webスクレイピング、自然言語処理、データ分析、データ可視化の技術を組み合わせて、人物の生涯、業績、人間関係などを多角的に分析します。

## 機能

*   **データ収集:**
    *   Wikipedia API (MediaWiki API) を使用して、指定された人物のページ情報を取得。
    *   Beautiful Soup を使用して、HTML から基本情報（名前、生年月日、出身地など）と本文テキストを抽出。
*   **データ処理:**
    *   抽出したデータを Pandas DataFrame に格納。
    *   テキストデータのクリーニング（不要な文字の削除、正規化）。
    *   Juman++ と KNP を使用して、本文テキストから年表データと関係ネットワークデータを抽出。
*   **データ分析:**
    *   基本情報の統計量計算（例：年齢）。
    *   年表データの分析（年ごとの出来事数集計、特定期間の出来事抽出）。
    *   関係ネットワーク分析（NetworkX を使用）。
*   **データ可視化:**
    *   Matplotlib (Seaborn) を使用して、年表を棒グラフで表示。
    *   NetworkX と Matplotlib を使用して、関係ネットワーク図を作成。
    *   WordCloud ライブラリを使用して、本文テキストからワードクラウドを生成。
*   **レポート生成:**
    *   Jinja2 テンプレートエンジンを使用して、分析結果をまとめた HTML レポートを生成。

## 使用技術

*   **言語:** Python 3.9 以上
*   **ライブラリ:**
    *   Requests: Wikipedia API へのリクエスト
    *   Beautiful Soup 4: HTML のパース
    *   Pandas: データフレームの操作
    *   Matplotlib: グラフの作成
    *   Seaborn: グラフのスタイル設定 (Matplotlib ベース)
    *   NetworkX: ネットワーク分析、グラフ作成
    *   wordcloud: ワードクラウドの作成
    *   Jinja2: HTML レポートの生成
    *   pyknp: Juman++ と KNP の Python インターフェース
    *   loguru: ロギング
    *   (オプション) japanize-matplotlib: Matplotlib での日本語表示 (システムに日本語フォントがインストールされていれば不要)

## 動作環境
* Python 3.9以上
* OS: Windows 11で開発 (他のOSでも動作する可能性はありますが、未検証)
* その他:
    * Juman++
    * KNP

## インストール方法
1.  **Juman++ と KNP のインストール**

   Juman++とKNPをインストールしてください
   
   公式サイト:
    * Juman++: [https://nlp.ist.i.kyoto-u.ac.jp/?JUMAN%2B%2B](https://www.google.com/search?q=https://www.google.com/search%3Fq%3Dhttps://nlp.ist.i.kyoto-u.ac.jp/%253FJUMAN%252B%252B)
    * KNP: [http://nlp.ist.i.kyoto-u.ac.jp/index.php?KNP](https://www.google.com/url?sa=E&source=gmail&q=http://nlp.ist.i.kyoto-u.ac.jp/index.php?KNP)

2.  **リポジトリのクローン:**

    ```bash
    git clone [https://github.com/your-username/wikipedia-biography-analyzer.git](https://www.google.com/search?q=https://github.com/your-username/wikipedia-biography-analyzer.git)
    cd wikipedia-biography-analyzer
    ```

    (注: `your-username` はあなたのGitHubユーザー名に置き換えてください)

3.  **Python 仮想環境の作成 (推奨):**

    ```bash
    python -m venv .venv
    ```

4.  **仮想環境のアクティベート:**

    *   **Windows (PowerShell):**

        ```powershell
        .venv\Scripts\Activate.ps1
        ```

    *   **Windows (コマンドプロンプト):**

        ```
        .venv\Scripts\activate.bat
        ```

    *   **macOS / Linux:**

        ```bash
        source .venv/bin/activate
        ```

5.  **必要なライブラリのインストール:**

    ```bash
    pip install -r requirements.txt
    ```

## 使用方法

1.  **`main.py` を実行:**

    ```bash
    python main.py
    ```

2.  **Wikipediaのページタイトルを入力:**

    プロンプトが表示されたら、分析したい人物のWikipediaページタイトル（例: `アルベルト・アインシュタイン`）を入力し、Enterキーを押します。

3.  **結果の確認:**

    *   `data/output` ディレクトリに、以下のファイルが生成されます。
        *   `report.html`: 分析結果をまとめたHTMLレポート
        *   `timeline.png`: 年表のグラフ
        *   `network_<人物名>.png`: 関係ネットワーク図
        *   `wordcloud.png`: ワードクラウド
    *   `data/logs` ディレクトリにログファイルが生成されます

## 今後の課題/拡張機能

*   関係ネットワーク抽出精度の向上 (固有表現抽出、係り受け解析の改善)
*   複数人物の比較分析機能
*   Wikipedia以外のデータソースへの対応
*   Webアプリケーション化
*   テストの追加
*   コードのリファクタリング