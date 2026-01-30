"""
じゃんぱら販売価格スクレイパー v2
詳細ページからランク情報を取得
"""
import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from playwright.async_api import async_playwright
import random


class JanparaResaleScraperV2:
    """じゃんぱら販売価格スクレイパー v2"""

    BASE_URL = "https://www.janpara.co.jp"

    # モデル別検索URL
    MODEL_URLS = {
        "iPhone 12": "/sale/search/result/?KEYWORDS=iPhone12&OUTCLSCODE=78&NOTKEYWORDS=Pro+mini",
        "iPhone 13": "/sale/search/result/?KEYWORDS=iPhone13&OUTCLSCODE=78&NOTKEYWORDS=Pro+mini",
        "iPhone 14": "/sale/search/result/?KEYWORDS=iPhone14&OUTCLSCODE=78&NOTKEYWORDS=Pro+mini+Plus",
    }

    async def scrape_product_detail(self, page, url: str) -> Optional[str]:
        """
        商品詳細ページからランク情報を取得
        """
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            # ページテキストを取得
            body_text = await page.inner_text('body')

            # ランクを抽出
            rank = self.extract_rank(body_text)

            return rank

        except Exception as e:
            print(f"      詳細ページエラー: {e}")
            return None

    def extract_rank(self, text: str) -> Optional[str]:
        """テキストからランクを抽出"""
        text_upper = text.upper()

        if "ランクA" in text or "A ランク" in text or "Aランク" in text:
            return "A"
        elif "ランクB" in text or "B ランク" in text or "Bランク" in text:
            return "B"
        elif "ランクC" in text or "C ランク" in text or "Cランク" in text:
            return "C"
        elif "ランクD" in text or "D ランク" in text or "Dランク" in text:
            return "D"
        elif "未使用" in text or "新品" in text:
            return "S"

        return None

    def extract_capacity(self, text: str) -> Optional[str]:
        """容量を抽出"""
        match = re.search(r'(\d+(?:GB|TB))', text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None

    def extract_price(self, text: str) -> Optional[int]:
        """価格を抽出"""
        numbers = re.findall(r'\d+', text.replace(',', '').replace('¥', ''))
        if numbers:
            return int(''.join(numbers))
        return None

    async def scrape_model_page(self, page, model: str, max_items: int = 30) -> List[Dict]:
        """
        モデルページから商品データを取得
        """
        url = self.BASE_URL + self.MODEL_URLS[model]

        print(f"  アクセス: {url}")

        products = []

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)

            # 商品カードを取得
            items = await page.query_selector_all(".search_item_s")

            print(f"  商品カード数: {len(items)}")

            # 最初のmax_items件のみ処理（詳細ページアクセスが多いため）
            for idx, item in enumerate(items[:max_items]):
                try:
                    # 商品名
                    name_elem = await item.query_selector('.search_itemname')
                    product_name = await name_elem.inner_text() if name_elem else ""

                    # 価格
                    price_elem = await item.query_selector('.item_amount')
                    price_text = await price_elem.inner_text() if price_elem else ""

                    # URL
                    link = await item.query_selector('a.search_itemlink')
                    url_path = await link.get_attribute('href') if link else ""
                    full_url = self.BASE_URL + url_path if url_path else ""

                    # 容量を抽出
                    capacity = self.extract_capacity(product_name)

                    # 価格を数値化
                    price = self.extract_price(price_text)

                    if product_name and price and capacity and full_url:
                        # 詳細ページからランクを取得
                        print(f"    {idx+1}/{min(max_items, len(items))}: {product_name[:40]}...")
                        rank = await self.scrape_product_detail(page, full_url)

                        products.append({
                            "product_name": product_name.strip(),
                            "price": price,
                            "url": full_url,
                            "rank": rank,
                            "capacity": capacity,
                            "model": model,
                            "scraped_at": datetime.now().isoformat(),
                            "source": "じゃんぱら",
                        })

                        # レート制限
                        await asyncio.sleep(random.uniform(2, 3))

                except Exception as e:
                    print(f"    商品{idx+1}のパースエラー: {e}")
                    continue

            print(f"  取得成功: {len(products)}件")

        except Exception as e:
            print(f"  エラー: {e}")

        return products

    async def scrape_all_models(self, models: List[str], output_dir: Path, max_items: int = 30) -> Dict[str, List[Dict]]:
        """全モデルをスクレイピング"""

        all_results = {}

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()

            for model in models:
                print(f"\n=== {model} ===")
                products = await self.scrape_model_page(page, model, max_items)
                all_results[model] = products

                # 保存
                if products:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"janpara_{model.replace(' ', '_')}_{timestamp}.json"
                    filepath = output_dir / filename

                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(products, f, ensure_ascii=False, indent=2)

                    print(f"  保存: {filepath}")

                await asyncio.sleep(random.uniform(5, 8))

            await browser.close()

        return all_results


async def main():
    """メイン処理"""
    output_dir = Path(__file__).parent.parent / "data" / "resale" / "janpara"

    scraper = JanparaResaleScraperV2()

    # テスト: iPhone 12のみ、20件
    models = ["iPhone 12"]

    print(f"じゃんぱら販売価格調査開始 v2")
    print(f"保存先: {output_dir}")
    print(f"注意: 各商品の詳細ページにアクセスするため時間がかかります")
    print("-" * 60)

    results = await scraper.scrape_all_models(models, output_dir, max_items=20)

    # サマリー
    print("\n" + "=" * 60)
    print("完了サマリー")
    print("=" * 60)
    for model, products in results.items():
        print(f"{model}: {len(products)}件")

        # ランク別集計
        from collections import Counter
        ranks = Counter([p['rank'] for p in products if p.get('rank')])
        for rank, count in sorted(ranks.items()):
            print(f"  {rank}ランク: {count}件" if rank else f"  ランク不明: {count}件")

    print("\n完了！")


if __name__ == "__main__":
    asyncio.run(main())
