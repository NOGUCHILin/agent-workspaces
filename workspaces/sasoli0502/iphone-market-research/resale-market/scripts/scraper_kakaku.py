"""
価格.com Playwrightを使った相場調査スクリプト
価格.comは複数の販売サイトの価格を集約しているため、これ一つで複数サイトの相場が分かる
"""
import time
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import json
from pathlib import Path
from playwright.async_api import async_playwright, Page
import re

from models import get_all_model_capacity_combinations, should_exclude_product


class KakakuScraper:
    """価格.comのブラウザ自動化スクレイピング"""

    BASE_URL = "https://kakaku.com"
    SLEEP_INTERVAL = 3.0  # ページ間の待機時間（秒）
    MAX_ITEMS_PER_SEARCH = 100  # 1検索あたりの最大取得件数

    async def search_products(
        self, page: Page, keyword: str
    ) -> List[Dict]:
        """
        キーワードで商品検索

        Args:
            page: Playwrightのページオブジェクト
            keyword: 検索キーワード

        Returns:
            検索結果のリスト（販売店情報含む）
        """
        # 価格.comの検索URL
        import urllib.parse
        encoded_keyword = urllib.parse.quote(keyword)
        search_url = f"{self.BASE_URL}/search_results/{encoded_keyword}/"

        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(4000)  # ページ読み込み待機

            # 商品リストを取得
            items = []

            # 価格.comの商品リンクをクリックして詳細ページへ
            # まず商品一覧から最初の商品を見つける
            product_links = await page.query_selector_all('a[class*="ckitanker"]')

            if not product_links:
                # 別のセレクタを試す
                product_links = await page.query_selector_all('.p-item_name a')

            if not product_links:
                print(f"    商品リンクが見つかりません")
                return []

            print(f"    {len(product_links)}件の商品リンク検出")

            # 最初の商品の詳細ページを開く（価格一覧を取得するため）
            first_product = product_links[0]
            product_url = await first_product.get_attribute('href')

            if not product_url.startswith('http'):
                product_url = self.BASE_URL + product_url

            # 商品詳細ページに移動
            await page.goto(product_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)

            # 商品名を取得
            product_name = ""
            name_selectors = ['h2', '.itemName', 'h1']
            for sel in name_selectors:
                name_elem = await page.query_selector(sel)
                if name_elem:
                    product_name = await name_elem.inner_text()
                    if product_name:
                        break

            # 価格一覧テーブルを探す
            price_rows_selectors = [
                'table.tblBorderGray tr',
                '.shopListTbl tr',
                'tr[class*="shop"]',
                'tbody tr'
            ]

            price_rows = []
            for selector in price_rows_selectors:
                price_rows = await page.query_selector_all(selector)
                if price_rows and len(price_rows) > 1:  # ヘッダー行を除く
                    print(f"    セレクタ '{selector}' で{len(price_rows)}行検出")
                    break

            for row in price_rows[:self.MAX_ITEMS_PER_SEARCH]:
                try:
                    # ショップ名
                    shop_selectors = ['.shopName', 'td:first-child', 'a']
                    shop_name = ""
                    for sel in shop_selectors:
                        shop_elem = await row.query_selector(sel)
                        if shop_elem:
                            shop_name = await shop_elem.inner_text()
                            if shop_name and len(shop_name) > 1:
                                break

                    # 価格
                    price_selectors = [
                        '.priceTxt',
                        'td[class*="price"]',
                        'span[class*="price"]',
                        'p[class*="price"]'
                    ]
                    price_text = ""
                    for sel in price_selectors:
                        price_elem = await row.query_selector(sel)
                        if price_elem:
                            price_text = await price_elem.inner_text()
                            if price_text and any(char.isdigit() for char in price_text):
                                break

                    # 価格をパース
                    price = 0
                    if price_text:
                        # 数字のみを抽出
                        price_numbers = re.findall(r'\d+', price_text.replace(',', '').replace('円', ''))
                        if price_numbers:
                            price = int(''.join(price_numbers))

                    # ショップURL
                    url = ""
                    link_elem = await row.query_selector('a')
                    if link_elem:
                        url = await link_elem.get_attribute('href')

                    # データが有効な場合のみ追加
                    if shop_name and price > 0:
                        items.append({
                            "product_name": product_name.strip() if product_name else keyword,
                            "price": price,
                            "shop_name": shop_name.strip(),
                            "url": url if url else "",
                            "source": "価格.com",
                        })

                except Exception as e:
                    continue

            return items

        except Exception as e:
            print(f"  エラー: {keyword} - {e}")
            return []

    async def scrape_iphone_prices(
        self, model: str, capacity: str, output_dir: Optional[Path] = None
    ) -> List[Dict]:
        """
        特定のiPhoneモデル・容量の価格情報を取得

        Args:
            model: iPhoneモデル（例: "iPhone 15 Pro"）
            capacity: 容量（例: "256GB"）
            output_dir: 保存先ディレクトリ（Noneの場合は保存しない）

        Returns:
            商品情報のリスト
        """
        print(f"検索中: {model} {capacity}")

        # 検索キーワード（価格.com向けにシンプル化）
        keyword = f"{model} {capacity} SIMフリー"

        all_products = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()

            # WebDriverを検出されにくくする
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            print(f"  キーワード: {keyword}")
            items = await self.search_products(page, keyword)

            for item in items:
                # 除外すべき商品をスキップ
                if should_exclude_product(item["product_name"]):
                    continue

                item["search_keyword"] = keyword
                item["model"] = model
                item["capacity"] = capacity
                item["scraped_at"] = datetime.now().isoformat()
                item["channel"] = "価格.com"
                all_products.append(item)

            print(f"    {len(items)}件取得 → {len(all_products)}件有効")

            await browser.close()

        print(f"  合計: {len(all_products)}件")

        # 保存
        if output_dir and all_products:
            output_dir.mkdir(parents=True, exist_ok=True)
            filename = f"kakaku_{model.replace(' ', '_')}_{capacity}.json"
            filepath = output_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(all_products, f, ensure_ascii=False, indent=2)

            print(f"  保存: {filepath}")

        return all_products


async def main():
    """メイン処理"""
    # 出力ディレクトリ
    output_dir = Path(__file__).parent.parent / "data" / "raw" / "kakaku"

    # スクレイパー初期化
    scraper = KakakuScraper()

    # 全モデル×容量の組み合わせ
    combinations = get_all_model_capacity_combinations()

    print(f"価格.com iPhone価格調査開始")
    print(f"対象: {len(combinations)}件")
    print(f"保存先: {output_dir}")
    print("-" * 60)

    # テスト実行（最初の3件のみ）
    for model, capacity in combinations[2:5]:  # iPhone XR からテスト
        await scraper.scrape_iphone_prices(model, capacity, output_dir)
        time.sleep(3)  # サイトへの負荷を考慮

    print("-" * 60)
    print("完了！")


if __name__ == "__main__":
    asyncio.run(main())
