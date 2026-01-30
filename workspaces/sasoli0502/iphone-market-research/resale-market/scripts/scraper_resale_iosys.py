"""
イオシス販売価格スクレイパー（ランク別）
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


class IosysResaleScraper:
    """イオシス販売価格スクレイパー（ランク別抽出）"""

    BASE_URL = "https://iosys.co.jp"
    SLEEP_MIN = 2.0
    SLEEP_MAX = 4.0

    # ランク抽出パターン
    RANK_PATTERNS = {
        "S": r"[【\[].*?[Ss].*?ランク.*?[】\]]|未使用品|新品同様",
        "A": r"[【\[].*?[Aa].*?ランク.*?[】\]]",
        "B": r"[【\[].*?[Bb].*?ランク.*?[】\]]",
        "C": r"[【\[].*?[Cc].*?ランク.*?[】\]]",
        "D": r"[【\[].*?[Dd].*?ランク.*?[】\]]",
        "ジャンク": r"ジャンク|JUNK",
    }

    async def create_stealth_context(self, playwright) -> BrowserContext:
        """
        ボット検出回避用のブラウザコンテキスト作成
        """
        browser = await playwright.chromium.launch(
            headless=False,  # headless=Falseでより人間らしく
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--no-sandbox',
            ]
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='ja-JP',
            timezone_id='Asia/Tokyo',
            geolocation={'latitude': 35.6762, 'longitude': 139.6503},  # 東京
            permissions=['geolocation'],
        )

        # WebDriverプロパティを隠す
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Chrome拡張機能のふり
            window.chrome = {
                runtime: {}
            };

            // プラグインの偽装
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // 言語設定
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ja-JP', 'ja', 'en-US', 'en']
            });
        """)

        return context

    def extract_rank(self, product_name: str, description: str = "") -> Optional[str]:
        """
        商品名・説明からランクを抽出
        """
        text = f"{product_name} {description}".upper()

        # 優先度順にチェック
        for rank_key, pattern in self.RANK_PATTERNS.items():
            if re.search(pattern, product_name + description, re.IGNORECASE):
                return rank_key

        return None

    def extract_capacity(self, text: str) -> Optional[str]:
        """
        容量を抽出（64GB, 128GB, 256GB, 512GB, 1TB）
        """
        capacity_pattern = r'(\d+(?:GB|TB))'
        match = re.search(capacity_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None

    def extract_price(self, text: str) -> Optional[int]:
        """
        価格を抽出（数字のみ）
        """
        # "¥12,800" → 12800
        price_numbers = re.findall(r'\d+', text.replace(',', ''))
        if price_numbers:
            return int(''.join(price_numbers))
        return None

    async def random_sleep(self):
        """ランダムな待機時間"""
        await asyncio.sleep(random.uniform(self.SLEEP_MIN, self.SLEEP_MAX))

    async def human_like_scroll(self, page: Page):
        """人間らしいスクロール動作"""
        for _ in range(random.randint(2, 4)):
            await page.evaluate(f"window.scrollBy(0, {random.randint(300, 600)})")
            await asyncio.sleep(random.uniform(0.3, 0.8))

    async def search_by_model_capacity_rank(
        self,
        page: Page,
        model: str,
        capacity: str,
        rank: str
    ) -> List[Dict]:
        """
        モデル・容量・ランク指定で検索
        """
        # ランクのマッピング
        rank_map = {
            "S": "新品/未使用",
            "A": "Aランク",
            "B": "Bランク",
            "C": "Cランク",
            "D": "Dランク",
        }

        products = []

        try:
            # 検索キーワード
            search_keyword = f"{model} {capacity}"
            search_url = f"{self.BASE_URL}/items/smartphone/iphone"

            print(f"    検索: {search_keyword} {rank_map.get(rank, rank)}")

            # ページアクセス
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            await self.random_sleep()

            # フィルタを適用（モデル名、容量、ランク）
            # ※実際のサイト構造に応じて調整が必要

            # スクロールしてコンテンツをロード
            await self.human_like_scroll(page)

            # 商品カードを取得
            # 複数のセレクタパターンを試す
            selectors = [
                '.item-box',
                '.product-card',
                '.goods-item',
                'article.product',
                '[data-product-id]',
            ]

            product_cards = []
            for selector in selectors:
                product_cards = await page.query_selector_all(selector)
                if product_cards:
                    print(f"      ✓ セレクタ '{selector}' で{len(product_cards)}件検出")
                    break

            if not product_cards:
                print(f"      商品カードが見つかりません")
                # ページのHTMLを保存（デバッグ用）
                content = await page.content()
                debug_file = Path(__file__).parent.parent / f"debug_iosys_{model}_{capacity}_{rank}.html"
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"      デバッグ用HTML保存: {debug_file}")
                return products

            # 各商品カードをパース
            for idx, card in enumerate(product_cards[:30]):  # 最大30件
                try:
                    # 商品名
                    name_elem = await card.query_selector('h3, h4, .item-name, .product-title, a')
                    product_name = await name_elem.inner_text() if name_elem else ""

                    # 価格
                    price_elem = await card.query_selector('.price, .item-price, [class*="price"]')
                    price_text = await price_elem.inner_text() if price_elem else ""
                    price = self.extract_price(price_text)

                    # 商品説明（ランク情報が含まれる可能性）
                    desc_elem = await card.query_selector('.description, .item-desc, p')
                    description = await desc_elem.inner_text() if desc_elem else ""

                    # URL
                    link_elem = await card.query_selector('a')
                    url = await link_elem.get_attribute('href') if link_elem else ""
                    if url and not url.startswith('http'):
                        url = self.BASE_URL + url

                    # ランクを抽出
                    extracted_rank = self.extract_rank(product_name, description)

                    # 容量を抽出
                    extracted_capacity = self.extract_capacity(product_name)

                    # フィルタリング: 指定されたモデル・容量・ランクに一致するか
                    if (
                        model.replace(" ", "").lower() in product_name.replace(" ", "").lower() and
                        extracted_capacity == capacity and
                        extracted_rank == rank and
                        price and price > 0
                    ):
                        products.append({
                            "product_name": product_name.strip(),
                            "price": price,
                            "url": url,
                            "rank": extracted_rank,
                            "capacity": extracted_capacity,
                            "model": model,
                            "description": description.strip()[:200],  # 最初の200文字
                            "scraped_at": datetime.now().isoformat(),
                            "source": "イオシス",
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
        ranks: List[str],
        output_dir: Optional[Path] = None
    ) -> List[Dict]:
        """
        特定モデルの全容量・全ランクをスクレイピング
        """
        print(f"\n=== {model} ===")

        all_products = []

        async with async_playwright() as p:
            context = await self.create_stealth_context(p)
            page = await context.new_page()

            for capacity in capacities:
                print(f"  容量: {capacity}")
                for rank in ranks:
                    products = await self.search_by_model_capacity_rank(
                        page, model, capacity, rank
                    )
                    all_products.extend(products)
                    await self.random_sleep()

            await context.close()

        print(f"  合計: {len(all_products)}件")

        # 保存
        if output_dir and all_products:
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"iosys_resale_{model.replace(' ', '_')}_{timestamp}.json"
            filepath = output_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(all_products, f, ensure_ascii=False, indent=2)

            print(f"  保存: {filepath}")

        return all_products


async def main():
    """メイン処理"""
    output_dir = Path(__file__).parent.parent / "data" / "resale" / "iosys"

    scraper = IosysResaleScraper()

    # 対象モデル
    models = [
        ("iPhone 12", ["64GB", "128GB", "256GB"]),
        ("iPhone 13", ["128GB", "256GB", "512GB"]),
        ("iPhone 14", ["128GB", "256GB", "512GB"]),
    ]

    # 対象ランク
    ranks = ["S", "A", "B", "C"]

    print(f"イオシス販売価格調査開始")
    print(f"保存先: {output_dir}")
    print("-" * 60)

    for model, capacities in models:
        await scraper.scrape_model(model, capacities, ranks, output_dir)

    print("-" * 60)
    print("完了！")


if __name__ == "__main__":
    asyncio.run(main())
