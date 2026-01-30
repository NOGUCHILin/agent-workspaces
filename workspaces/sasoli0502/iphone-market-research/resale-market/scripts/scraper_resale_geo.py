"""
ゲオオンライン販売価格スクレイパー（ランク別）
Playwright使用、ボットブロック対策実装
"""
import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, BrowserContext
import random


class GeoResaleScraper:
    """ゲオオンライン販売価格スクレイパー（ランク別抽出）"""

    BASE_URL = "https://geo-online.co.jp"
    SLEEP_MIN = 2.0
    SLEEP_MAX = 4.0

    async def create_stealth_context(self, playwright) -> BrowserContext:
        """ボット検出回避用のブラウザコンテキスト作成"""
        browser = await playwright.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='ja-JP',
            timezone_id='Asia/Tokyo',
        )

        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = { runtime: {} };
        """)

        return context

    def extract_rank(self, product_name: str, description: str = "") -> Optional[str]:
        """商品名・説明からランクを抽出"""
        text = f"{product_name} {description}".upper()

        rank_patterns = {
            "S": r"未使用|新品同様|Sランク",
            "A": r"Aランク|状態良好",
            "B": r"Bランク",
            "C": r"Cランク",
        }

        for rank, pattern in rank_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return rank

        return None

    def extract_capacity(self, text: str) -> Optional[str]:
        """容量を抽出"""
        capacity_pattern = r'(\d+(?:GB|TB))'
        match = re.search(capacity_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None

    def extract_price(self, text: str) -> Optional[int]:
        """価格を抽出"""
        price_numbers = re.findall(r'\d+', text.replace(',', '').replace('¥', ''))
        if price_numbers:
            return int(''.join(price_numbers))
        return None

    async def random_sleep(self):
        """ランダムな待機時間"""
        await asyncio.sleep(random.uniform(self.SLEEP_MIN, self.SLEEP_MAX))

    async def search_by_model_capacity(
        self,
        page: Page,
        model: str,
        capacity: str
    ) -> List[Dict]:
        """モデル・容量で検索し、商品リストを取得"""
        products = []

        try:
            # ゲオオンラインの検索URL
            search_keyword = f"{model} {capacity}".replace(" ", "+")
            search_url = f"{self.BASE_URL}/search/?text={search_keyword}"

            print(f"    検索: {model} {capacity}")
            print(f"    URL: {search_url}")

            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            await self.random_sleep()

            # 商品カードを取得
            selectors = [
                '.item',
                '.product-card',
                '.goods-item',
                'article',
                '[data-product]',
            ]

            product_cards = []
            for selector in selectors:
                product_cards = await page.query_selector_all(selector)
                if product_cards:
                    print(f"      ✓ セレクタ '{selector}' で{len(product_cards)}件検出")
                    break

            if not product_cards:
                print(f"      商品カードが見つかりません")
                # デバッグ用スクリーンショット
                screenshot_path = Path(__file__).parent.parent / f"debug_geo_{model}_{capacity}.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                print(f"      スクリーンショット保存: {screenshot_path}")
                return products

            # 各商品カードをパース
            for idx, card in enumerate(product_cards[:20]):
                try:
                    # 商品名
                    name_elem = await card.query_selector('h3, h4, .item-name, .product-title, a')
                    product_name = await name_elem.inner_text() if name_elem else ""

                    # 価格
                    price_elem = await card.query_selector('.price, .item-price, [class*="price"]')
                    price_text = await price_elem.inner_text() if price_elem else ""
                    price = self.extract_price(price_text)

                    # 商品説明
                    desc_elem = await card.query_selector('.description, .item-desc, p')
                    description = await desc_elem.inner_text() if desc_elem else ""

                    # URL
                    link_elem = await card.query_selector('a')
                    url = await link_elem.get_attribute('href') if link_elem else ""
                    if url and not url.startswith('http'):
                        url = self.BASE_URL + url

                    # ランクを抽出
                    rank = self.extract_rank(product_name, description)

                    # 容量を抽出
                    extracted_capacity = self.extract_capacity(product_name)

                    # フィルタリング
                    if (
                        model.replace(" ", "").lower() in product_name.replace(" ", "").lower() and
                        extracted_capacity == capacity and
                        price and price > 0
                    ):
                        products.append({
                            "product_name": product_name.strip(),
                            "price": price,
                            "url": url,
                            "rank": rank,
                            "capacity": extracted_capacity,
                            "model": model,
                            "description": description.strip()[:200],
                            "scraped_at": datetime.now().isoformat(),
                            "source": "ゲオオンライン",
                        })

                except Exception as e:
                    print(f"      商品カード{idx}のパースエラー: {e}")
                    continue

            print(f"      取得: {len(products)}件")

        except Exception as e:
            print(f"    エラー: {e}")

        return products

    async def scrape_model(
        self,
        model: str,
        capacities: List[str],
        output_dir: Optional[Path] = None
    ) -> List[Dict]:
        """特定モデルの全容量をスクレイピング"""
        print(f"\n=== {model} ===")

        all_products = []

        async with async_playwright() as p:
            context = await self.create_stealth_context(p)
            page = await context.new_page()

            for capacity in capacities:
                print(f"  容量: {capacity}")
                products = await self.search_by_model_capacity(page, model, capacity)
                all_products.extend(products)
                await self.random_sleep()

            await context.close()

        print(f"  合計: {len(all_products)}件")

        # 保存
        if output_dir and all_products:
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"geo_resale_{model.replace(' ', '_')}_{timestamp}.json"
            filepath = output_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(all_products, f, ensure_ascii=False, indent=2)

            print(f"  保存: {filepath}")

        return all_products


async def main():
    """メイン処理"""
    output_dir = Path(__file__).parent.parent / "data" / "resale" / "geo"

    scraper = GeoResaleScraper()

    # 対象モデル（テスト: iPhone 12のみ）
    models = [
        ("iPhone 12", ["64GB", "128GB"]),
    ]

    print(f"ゲオオンライン販売価格調査開始")
    print(f"保存先: {output_dir}")
    print("-" * 60)

    for model, capacities in models:
        await scraper.scrape_model(model, capacities, output_dir)

    print("-" * 60)
    print("完了！")


if __name__ == "__main__":
    asyncio.run(main())
