import requests
from bs4 import BeautifulSoup, Comment
import json
from rich.console import Console
from rich.syntax import Syntax
from rich import print  # rich の print 関数で置き換え # 追記

# 調査対象のWikipedia URL
WIKIPEDIA_URL = "https://ja.wikipedia.org/wiki/%E3%82%A2%E3%83%AB%E3%83%99%E3%83%AB%E3%83%88%E3%83%BB%E3%82%A2%E3%82%A4%E3%83%B3%E3%82%B7%E3%83%A5%E3%82%BF%E3%82%A4%E3%83%B3#cite_note-3"  # アルベルト・アインシュタイン

console = Console() #  Console オブジェクトを作成 # 追記

def fetch_html(url):
    """URLからHTMLコンテンツを取得する."""
    response = requests.get(url)
    response.raise_for_status()  # エラーレスポンスをチェック
    response.encoding = response.apparent_encoding  # 文字コードを自動検出
    return response.text

def inspect_tags_text_search_rich(html_content, query): # 関数名を変更 # 修正
    """HTMLコンテンツとクエリ (CSSセレクターまたはテキスト) に基づいてタグを調査し、詳細情報をrichで表示する (rich装飾版)."""
    soup = BeautifulSoup(html_content, 'html.parser')
    search_type = "CSSセレクター"

    if query.startswith(('#', '.')) or query.isalnum(): # CSSセレクターの可能性を判定
        try:
            selected_tags = soup.select(query)
        except Exception as e:
            console.print(f"[bold red]無効なCSSセレクターです:[/bold red] '{query}' - {e}") # rich でエラーメッセージ # 修正
            return
    else: # テキスト検索とみなす
        selected_tags = soup.find_all(string=lambda text: text and query in text) # テキスト検索
        if not selected_tags:
            selected_tags = soup.find_all(text=query) #  完全一致テキスト検索も試す
        search_type = "テキスト"

    if not selected_tags:
        console.print(f"[bold blue]クエリ[/bold blue] '[bold magenta]{query}[/bold magenta]' [bold blue]に一致するタグは見つかりませんでした[/bold blue] ([cyan]{search_type}[/cyan]検索)。") # rich でメッセージ # 修正
        return

    console.print(f"\n[bold green]クエリ[/bold green] '[bold magenta]{query}[/bold magenta]' [bold green]に一致するタグ[/bold green] ([cyan]{search_type}[/cyan]検索): [bold yellow]{len(selected_tags)}個[/bold yellow]\n") # rich でメッセージ # 修正

    for i, tag in enumerate(selected_tags):
        if search_type == "テキスト": # テキスト検索の場合は親タグを表示
            tag = tag.parent

        console.print(f"[bold]----- タグ {i+1} -----[/bold]") # rich でタグ番号 # 修正
        console.print(f"  [bold blue]タグ名:[/bold blue] [magenta]{tag.name}[/magenta]") # rich でタグ名 # 修正
        if tag.attrs:
            console.print(f"  [bold blue]属性:[/bold blue] [magenta]{tag.attrs}[/magenta]") # rich で属性 # 修正
        console.print(f"  [bold blue]親タグ:[/bold blue] [magenta]{tag.parent.name if tag.parent else 'なし'}[/magenta]") # rich で親タグ # 修正
        console.print(f"  [bold blue]子要素数:[/bold blue] [magenta]{len(tag.contents)}[/magenta]") # rich で子要素数 # 修正
        if tag.get('class'):
            console.print(f"  [bold blue]クラス:[/bold blue] [magenta]{tag['class']}[/magenta]") # rich でクラス # 修正
        if tag.get('id'):
            console.print(f"  [bold blue]ID:[/bold blue] [magenta]{tag['id']}[/magenta]") # rich で ID # 修正

        #  テキスト内容を一部表示 (長すぎる場合は省略)
        text_content = tag.get_text(strip=True)
        if len(text_content) > 100:
            console.print(f"  [bold blue]テキスト内容 (先頭100文字):[/bold blue] [italic magenta]{text_content[:100]}...[/italic magenta]") # rich でテキスト内容 # 修正
        else:
            console.print(f"  [bold blue]テキスト内容:[/bold blue] [italic magenta]{text_content}[/italic magenta]") # rich でテキスト内容 # 修正

        #  HTML全体を強調表示 (rich syntax highlight)
        syntax = Syntax(str(tag), "html", theme="monokai", line_numbers=False, word_wrap=True) # rich syntax highlight # 修正
        console.print(f"\n[bold blue]HTML (強調表示):[/bold blue]") # rich で HTML ヘッダー # 修正
        console.print(syntax) # rich syntax highlight を表示 # 修正
        console.print("\n") #  改行


def main():
    html_content = fetch_html(WIKIPEDIA_URL)

    while True:
        query = input("調査したいタグのCSSセレクターまたはテキストを入力してください (終了するには quit と入力): ")
        if query.lower() == 'quit':
            break

        inspect_tags_text_search_rich(html_content, query) # rich装飾版関数を使用 # 修正
        console.rule(style="[bold blue]") #  区切り線を rule で描画 # 修正

if __name__ == "__main__":
    main()