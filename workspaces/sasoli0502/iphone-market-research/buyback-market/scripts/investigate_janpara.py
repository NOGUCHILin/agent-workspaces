"""
じゃんぱらのHTML構造を調査するスクリプト
"""

import requests
from bs4 import BeautifulSoup

# HTTPヘッダー
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}

def investigate_search():
    """検索ページの構造を調査"""

    # iPhone 15 Pro 256GBで検索
    url = "https://buy.janpara.co.jp/buy/search/"
    params = {
        "keyword": "iPhone 15 Pro 256GB",
    }

    print("=== じゃんぱら検索ページ構造調査 ===\n")
    print(f"URL: {url}")
    print(f"検索キーワード: {params['keyword']}\n")

    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        print(f"ステータスコード: {response.status_code}")
        print(f"実際のURL: {response.url}\n")

        if response.status_code != 200:
            print(f"エラー: HTTPステータス {response.status_code}")
            return

        soup = BeautifulSoup(response.content, "lxml")

        # ページタイトル
        title = soup.find("title")
        print(f"ページタイトル: {title.get_text() if title else 'なし'}\n")

        # 商品リストの構造を探す
        print("=== HTML構造分析 ===\n")

        # よくある商品リストのクラス名を試す
        possible_containers = [
            "product-list",
            "products",
            "item-list",
            "search-results",
            "list-item",
            "buy-list",
            "kaitori-list"
        ]

        print("1. 商品コンテナの候補を検索:")
        for container_class in possible_containers:
            elements = soup.find_all(class_=container_class)
            if elements:
                print(f"  ✓ class=\"{container_class}\" 見つかりました: {len(elements)}個")

        # divやliで始まる要素を探す
        print("\n2. divとliタグの分析:")
        all_divs = soup.find_all("div", limit=20)
        all_lis = soup.find_all("li", limit=20)

        print(f"  div要素の総数: {len(soup.find_all('div'))}")
        print(f"  li要素の総数: {len(soup.find_all('li'))}")

        # class属性を持つdivの最初の10件を表示
        print("\n3. class属性を持つdivの例（最初の10件）:")
        divs_with_class = [d for d in all_divs if d.get('class')]
        for i, div in enumerate(divs_with_class[:10], 1):
            classes = ' '.join(div.get('class', []))
            print(f"  {i}. class=\"{classes}\"")

        # 価格らしい要素を探す
        print("\n4. 価格表示の候補:")
        price_keywords = ["price", "kaitori", "buy", "yen", "円"]
        for keyword in price_keywords:
            elements = soup.find_all(class_=lambda x: x and keyword in x.lower())
            if elements:
                print(f"  ✓ '{keyword}'を含むclass: {len(elements)}個")
                # 最初の要素のテキストを表示
                if elements:
                    sample_text = elements[0].get_text(strip=True)[:100]
                    print(f"    例: {sample_text}")

        # aタグ（リンク）の分析
        print("\n5. リンク（aタグ）の分析:")
        links = soup.find_all("a", href=True, limit=10)
        for i, link in enumerate(links, 1):
            href = link.get("href", "")
            text = link.get_text(strip=True)[:50]
            if "iphone" in href.lower() or "iphone" in text.lower():
                print(f"  {i}. href=\"{href}\" text=\"{text}\"")

        # HTMLの一部を保存
        print("\n6. HTML保存:")
        output_file = "janpara_search_sample.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"  完全なHTMLを保存しました: {output_file}")

        # bodyの最初の1000文字を表示
        print("\n7. HTMLボディのサンプル（最初の1000文字）:")
        body = soup.find("body")
        if body:
            body_text = str(body)[:1000]
            print(body_text)

    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()


def investigate_category():
    """iPhoneカテゴリページを調査"""
    url = "https://buy.janpara.co.jp/buy/list/iphone/"

    print("\n\n=== じゃんぱらiPhoneカテゴリページ構造調査 ===\n")
    print(f"URL: {url}\n")

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        print(f"ステータスコード: {response.status_code}\n")

        if response.status_code != 200:
            print(f"エラー: HTTPステータス {response.status_code}")
            return

        soup = BeautifulSoup(response.content, "lxml")

        # ページタイトル
        title = soup.find("title")
        print(f"ページタイトル: {title.get_text() if title else 'なし'}\n")

        # HTMLを保存
        output_file = "janpara_iphone_category.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"完全なHTMLを保存しました: {output_file}")

    except Exception as e:
        print(f"エラー: {e}")


if __name__ == "__main__":
    investigate_search()
    investigate_category()
