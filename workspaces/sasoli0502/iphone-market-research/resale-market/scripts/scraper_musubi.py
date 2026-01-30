"""
ムスビー Playwrightを使った相場調査スクリプト
"""
import time
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import json
from pathlib import Path
from playwright.async_api import async_playwright, Page
import re

from models import get_all_model_capacity_combinations, get_search_keywords, should_exclude_product


class MusubiScraper:
    """ムスビーのブラウザ自動化スクレイピング"""

    BASE_URL = "https://www.musbi.net"
    SLEEP_INTERVAL = 2.0  # ページ間の待機時間（秒）
    MAX_ITEMS_PER_SEARCH = 60  # 1検索あたりの最大取得件数

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
        # ムスビーの検索URL
        import urllib.parse
        encoded_keyword = urllib.parse.quote(keyword)
        search_url = f"{self.BASE_URL}/item/search/?keyword={encoded_keyword}"

        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)  # ページ読み込み待機

            # 商品リストを取得
            items = []

            # ムスビーの商品カードを取得
            # 複数のセレクタパターンを試す
            selectors = [
                '.item-list li',
                '.product-item',
                '.item',
                'article',
                '.goods-item'
            ]

            product_cards = []
            for selector in selectors:
                product_cards = await page.query_selector_all(selector)
                if product_cards:
                    print(f"    セレクタ '{selector}' で{len(product_cards)}件検出")
                    break

            if not product_cards:
                print(f"    商品カードが見つかりません")
                return []

            for card in product_cards[:self.MAX_ITEMS_PER_SEARCH]:
                try:
                    # 商品名を取得
                    name_selectors = ['h3', 'h4', 'h2', '.item-name', '.product-name', '.title', 'a']
                    product_name = ""
                    for sel in name_selectors:
                        name_elem = await card.query_selector(sel)
                        if name_elem:
                            text = await name_elem.inner_text()
                            if text and len(text) > 5:  # 最低5文字以上
                                product_name = text
                                break

                    # 価格を取得
                    price_selectors = [
                        '.price',
                        '.item-price',
                        '.product-price',
                        'span[class*="price"]',
                        'p[class*="price"]',
                        '.price-val',
                        '.amount'
                    ]
                    price_text = ""
                    for sel in price_selectors:
                        price_elem = await card.query_selector(sel)
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

                    # URLを取得
                    url = ""
                    link_elem = await card.query_selector('a')
                    if link_elem:
                        url = await link_elem.get_attribute('href')
                        if url and not url.startswith('http'):
                            url = self.BASE_URL + url

                    # 画像URLを取得
                    image_url = ""
                    img_elem = await card.query_selector('img')
                    if img_elem:
                        image_url = await img_elem.get_attribute('src')
                        if image_url and not image_url.startswith('http'):
                            if image_url.startswith('//'):
                                image_url = 'https:' + image_url
                            else:
                                image_url = self.BASE_URL + image_url

                    # データが有効な場合のみ追加
                    if product_name and price > 0:
                        items.append({
                            "product_name": product_name.strip(),
                            "price": price,
                            "url": url,
                            "image_url": image_url,
                        })

                except Exception as e:
                    # 個別の商品カードのエラーはスキップ
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

        # 検索キーワード（ムスビー向けにシンプル化）
        keywords = [
            f"{model} {capacity}",
            f"{model} {capacity} SIMフリー",
        ]

        all_products = []
        seen_urls = set()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()

            for keyword in keywords:
                print(f"  キーワード: {keyword}")
                items = await self.search_products(page, keyword)

                valid_count = 0
                for item in items:
                    # 除外すべき商品をスキップ
                    if should_exclude_product(item["product_name"]):
                        continue

                    # 重複除去（URLベース）
                    if item["url"] and item["url"] not in seen_urls:
                        item["search_keyword"] = keyword
                        item["model"] = model
                        item["capacity"] = capacity
                        item["scraped_at"] = datetime.now().isoformat()
                        item["channel"] = "ムスビー"
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
            filename = f"musubi_{model.replace(' ', '_')}_{capacity}.json"
            filepath = output_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(all_products, f, ensure_ascii=False, indent=2)

            print(f"  保存: {filepath}")

        return all_products


async def main():
    """メイン処理"""
    # 出力ディレクトリ
    output_dir = Path(__file__).parent.parent / "data" / "raw" / "musubi"

    # スクレイパー初期化
    scraper = MusubiScraper()

    # 全モデル×容量の組み合わせ
    combinations = get_all_model_capacity_combinations()

    print(f"ムスビー iPhone価格調査開始")
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
