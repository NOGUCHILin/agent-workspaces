"""
メルカリ Playwrightを使った相場調査スクリプト
"""
import time
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import json
from pathlib import Path
from playwright.async_api import async_playwright, Page

from models import get_all_model_capacity_combinations, get_search_keywords, should_exclude_product


class MercariScraper:
    """メルカリのブラウザ自動化スクレイピング"""

    BASE_URL = "https://jp.mercari.com"
    SLEEP_INTERVAL = 2.0  # ページ間の待機時間（秒）
    MAX_ITEMS_PER_SEARCH = 50  # 1検索あたりの最大取得件数

    async def search_products(
        self, page: Page, keyword: str
    ) -> List[Dict]:
        """
        キーワードで商品検索

        Args:
            page: Playwrightのページオブジェクト
            keyword: 検索キーワード

        Returns:
            検索結果のリスト
        """
        # メルカリの検索URL（URLエンコード）
        import urllib.parse
        encoded_keyword = urllib.parse.quote(keyword)
        search_url = f"{self.BASE_URL}/search?keyword={encoded_keyword}&status=on_sale"

        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)  # ページ読み込み待機（長めに）

            # 商品リストを取得
            items = []

            # 複数のセレクタを試す（メルカリのHTML構造の変更に対応）
            selectors = [
                '[data-testid="item-cell"]',
                'li[data-testid*="item"]',
                '.merItem',
                'ul > li > a'  # より一般的なセレクタ
            ]

            product_cards = []
            for selector in selectors:
                product_cards = await page.query_selector_all(selector)
                if product_cards:
                    print(f"    セレクタ '{selector}' で{len(product_cards)}件検出")
                    break

            for card in product_cards[:self.MAX_ITEMS_PER_SEARCH]:
                try:
                    # 商品名
                    name_elem = await card.query_selector('[data-testid="thumbnail-item-name"]')
                    product_name = await name_elem.inner_text() if name_elem else ""

                    # 価格
                    price_elem = await card.query_selector('[data-testid="thumbnail-item-price"]')
                    price_text = await price_elem.inner_text() if price_elem else "0"
                    # "¥10,000" → "10000" に変換
                    price = int(price_text.replace("¥", "").replace(",", "").strip())

                    # URL
                    link_elem = await card.query_selector('a')
                    url = await link_elem.get_attribute('href') if link_elem else ""
                    if url and not url.startswith("http"):
                        url = self.BASE_URL + url

                    # 画像URL
                    img_elem = await card.query_selector('img')
                    image_url = await img_elem.get_attribute('src') if img_elem else ""

                    items.append({
                        "product_name": product_name,
                        "price": price,
                        "url": url,
                        "image_url": image_url,
                    })

                except Exception as e:
                    print(f"    商品カード解析エラー: {e}")
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

        # 検索キーワードのバリエーション
        keywords = get_search_keywords(model, capacity)

        all_products = []
        seen_urls = set()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            for keyword in keywords:
                print(f"  キーワード: {keyword}")
                items = await self.search_products(page, keyword)

                valid_count = 0
                for item in items:
                    # 除外すべき商品をスキップ
                    if should_exclude_product(item["product_name"]):
                        continue

                    # 重複除去（URLベース）
                    if item["url"] not in seen_urls:
                        item["search_keyword"] = keyword
                        item["model"] = model
                        item["capacity"] = capacity
                        item["scraped_at"] = datetime.now().isoformat()
                        item["channel"] = "メルカリ"
                        all_products.append(item)
                        seen_urls.add(item["url"])
                        valid_count += 1

                print(f"    {len(items)}件取得 → {valid_count}件有効")

                # レート制限対策
                await page.wait_for_timeout(int(self.SLEEP_INTERVAL * 1000))

            await browser.close()

        print(f"  合計: {len(all_products)}件（重複除去後）")

        # 保存
        if output_dir and all_products:
            output_dir.mkdir(parents=True, exist_ok=True)
            filename = f"mercari_{model.replace(' ', '_')}_{capacity}.json"
            filepath = output_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(all_products, f, ensure_ascii=False, indent=2)

            print(f"  保存: {filepath}")

        return all_products


async def main():
    """メイン処理"""
    # 出力ディレクトリ
    output_dir = Path(__file__).parent.parent / "data" / "raw" / "mercari"

    # スクレイパー初期化
    scraper = MercariScraper()

    # 全モデル×容量の組み合わせ
    combinations = get_all_model_capacity_combinations()

    print(f"メルカリ iPhone価格調査開始")
    print(f"対象: {len(combinations)}件")
    print(f"保存先: {output_dir}")
    print("-" * 60)

    # テスト実行（最初の3件のみ）
    for model, capacity in combinations[:3]:
        await scraper.scrape_iphone_prices(model, capacity, output_dir)
        time.sleep(2)  # サイトへの負荷を考慮

    print("-" * 60)
    print("完了！")


if __name__ == "__main__":
    asyncio.run(main())
