"""
イオシス買取サイトのHTML構造を調査するスクリプト
"""

import requests
from bs4 import BeautifulSoup

# HTTPヘッダー
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}

def investigate_iosys_main():
    """イオシストップページを調査"""
    url = "https://k-tai-iosys.com/"

    print("=== イオシス買取トップページ構造調査 ===\n")
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

        # iPhoneへのリンクを探す
        print("=== iPhoneへのリンク検索 ===\n")
        iphone_links = soup.find_all("a", href=True)
        for link in iphone_links[:30]:
            href = link.get("href", "")
            text = link.get_text(strip=True)
            if "iphone" in href.lower() or "iphone" in text.lower():
                print(f"  href=\"{href}\" text=\"{text}\"")

        # フォーム要素を探す
        print("\n=== 検索フォーム ===\n")
        forms = soup.find_all("form")
        for i, form in enumerate(forms, 1):
            print(f"Form {i}:")
            action = form.get("action", "")
            method = form.get("method", "")
            print(f"  action=\"{action}\" method=\"{method}\"")

            # フォーム内のinput要素
            inputs = form.find_all("input")
            for inp in inputs[:5]:
                name = inp.get("name", "")
                input_type = inp.get("type", "")
                print(f"    input: name=\"{name}\" type=\"{input_type}\"")

        # HTMLを保存
        output_file = "iosys_main.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"\n完全なHTMLを保存しました: {output_file}")

    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()


def investigate_iosys_search():
    """イオシスでiPhone 15 Pro 256GBを検索"""

    # 検索ページのURLを試す
    possible_urls = [
        "https://k-tai-iosys.com/search?keyword=iPhone+15+Pro+256GB",
        "https://k-tai-iosys.com/search.php?keyword=iPhone+15+Pro+256GB",
        "https://k-tai-iosys.com/iphone",
        "https://k-tai-iosys.com/products/iphone",
    ]

    print("\n\n=== イオシス検索ページ調査 ===\n")

    for url in possible_urls:
        print(f"試行中: {url}")
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            print(f"  ステータスコード: {response.status_code}")

            if response.status_code == 200:
                print(f"  ✓ 成功！このURLでアクセス可能")

                soup = BeautifulSoup(response.content, "lxml")
                title = soup.find("title")
                print(f"  ページタイトル: {title.get_text() if title else 'なし'}")

                # HTMLを保存
                filename = f"iosys_{url.split('/')[-1] or 'index'}.html"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"  HTMLを保存: {filename}\n")

                break
            else:
                print(f"  × 失敗（{response.status_code}）\n")

        except Exception as e:
            print(f"  × エラー: {e}\n")


if __name__ == "__main__":
    investigate_iosys_main()
    investigate_iosys_search()
