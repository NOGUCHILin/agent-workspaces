"""
じゃんぱら販売価格スクレイパー（ランク別）
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


class JanparaResaleScraper:
    """じゃんぱら販売価格スクレイパー（ランク別抽出）"""

    BASE_URL = "https://www.janpara.co.jp"
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
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)

        return context

    def extract_rank_from_url_or_page(self, url: str, page_text: str) -> Optional[str]:
        """
        URLまたはページテキストからランクを抽出
        じゃんぱらは商品詳細ページにランク情報がある
        """
        # URLやテキストからランク情報を抽出
        rank_patterns = {
            "A": r"[ラランク]*[Aa](?:ランク)?",
            "B": r"[ラランク]*[Bb](?:ランク)?",
            "C": r"[ラランク]*[Cc](?:ランク)?",
            "D": r"[ラランク]*[Dd](?:ランク)?",
        }

        text = f"{url} {page_text}".upper()

        for rank, pattern in rank_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return rank

        # 未使用品
        if "未使用" in page_text or "新品" in page_text:
            return "S"

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

    async def scrape_product_detail(self, page: Page, product_url: str) -> Optional[Dict]:
        """
        商品詳細ページからランク情報を取得
        """
        try:
            await page.goto(product_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(1)

            # ページ全体のテキストを取得
            body_text = await page.inner_text('body')

            # ランクを抽出
            rank = self.extract_rank_from_url_or_page(product_url, body_text)

            return {"rank": rank, "page_text": body_text[:500]}

        except Exception as e:
            print(f"        詳細ページエラー: {e}")
            return None

    async def search_by_model_capacity(
        self,
        page: Page,
        model: str,
        capacity: str,
        fetch_details: bool = True
    ) -> List[Dict]:
        """
        モデル・容量で検索し、商品リストを取得
        """
        products = []

        try:
            # じゃんぱらの検索URL
            # 例: https://www.janpara.co.jp/sale/search/result/?KEYWORDS=iPhone+12+64GB&OUTCLSCODE=78
            search_keyword = f"{model} {capacity}".replace(" ", "+")
            search_url = f"{self.BASE_URL}/sale/search/result/?KEYWORDS={search_keyword}&OUTCLSCODE=78"

            print(f"    検索: {model} {capacity}")
            print(f"    URL: {search_url}")

            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            await self.random_sleep()

            # 商品カードを取得
            selectors = [
                '.item-box',
                '.product-item',
                'article',
                '[data-product-id]',
                '.goods-item',
            ]

            product_cards = []
            for selector in selectors:
                product_cards = await page.query_selector_all(selector)
                if product_cards:
                    print(f"      ✓ セレクタ '{selector}' で{len(product_cards)}件検出")
                    break

            if not product_cards:
                print(f"      商品カードが見つかりません")
                # デバッグ用: ページのスクリーンショット
                screenshot_path = Path(__file__).parent.parent / f"debug_janpara_{model}_{capacity}.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                print(f"      スクリーンショット保存: {screenshot_path}")
                return products

            # 最初の10件のみ詳細ページを取得（時間短縮）
            for idx, card in enumerate(product_cards[:10]):
                try:
                    # 商品名
                    name_elem = await card.query_selector('h3, h4, .item-name, .product-title, a')
                    product_name = await name_elem.inner_text() if name_elem else ""

                    # 価格
                    price_elem = await card.query_selector('.price, .item-price, [class*="price"]')
                    price_text = await price_elem.inner_text() if price_elem else ""
                    price = self.extract_price(price_text)

                    # URL
                    link_elem = await card.query_selector('a')
                    url = await link_elem.get_attribute('href') if link_elem else ""
                    if url and not url.startswith('http'):
                        url = self.BASE_URL + url

                    # 容量を抽出
                    extracted_capacity = self.extract_capacity(product_name)

                    # フィルタリング
                    if (
                        model.replace(" ", "").lower() in product_name.replace(" ", "").lower() and
                        extracted_capacity == capacity and
                        price and price > 0 and
                        url
                    ):
                        # 詳細ページからランクを取得
                        rank = None
                        if fetch_details:
                            print(f"        詳細取得: {idx+1}/{len(product_cards[:10])}")
                            detail_info = await self.scrape_product_detail(page, url)
                            if detail_info:
                                rank = detail_info["rank"]

                        products.append({
                            "product_name": product_name.strip(),
                            "price": price,
                            "url": url,
                            "rank": rank,
                            "capacity": extracted_capacity,
                            "model": model,
                            "scraped_at": datetime.now().isoformat(),
                            "source": "じゃんぱら",
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
                products = await self.search_by_model_capacity(
                    page, model, capacity, fetch_details=True
                )
                all_products.extend(products)
                await self.random_sleep()

            await context.close()

        print(f"  合計: {len(all_products)}件")

        # 保存
        if output_dir and all_products:
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"janpara_resale_{model.replace(' ', '_')}_{timestamp}.json"
            filepath = output_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(all_products, f, ensure_ascii=False, indent=2)

            print(f"  保存: {filepath}")

        return all_products


async def main():
    """メイン処理"""
    output_dir = Path(__file__).parent.parent / "data" / "resale" / "janpara"

    scraper = JanparaResaleScraper()

    # 対象モデル（テスト: iPhone 12のみ）
    models = [
        ("iPhone 12", ["64GB", "128GB"]),
    ]

    print(f"じゃんぱら販売価格調査開始")
    print(f"保存先: {output_dir}")
    print("-" * 60)

    for model, capacities in models:
        await scraper.scrape_model(model, capacities, output_dir)

    print("-" * 60)
    print("完了！")


if __name__ == "__main__":
    asyncio.run(main())
