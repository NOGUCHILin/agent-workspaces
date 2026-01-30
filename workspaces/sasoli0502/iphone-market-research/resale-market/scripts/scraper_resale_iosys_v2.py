"""
イオシス販売価格スクレイパー v2（修正版）
実際の商品カード構造に基づいた実装
"""
import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from playwright.async_api import async_playwright
import random


class IosysResaleScraperV2:
    """イオシス販売価格スクレイパー v2"""

    BASE_URL = "https://iosys.co.jp"

    # モデル別URL
    MODEL_URLS = {
        "iPhone 12": "/items/smartphone/iphone12",
        "iPhone 13": "/items/smartphone/iphone13",
        "iPhone 14": "/items/smartphone/iphone14",
    }

    async def scrape_model_page(self, page, model: str) -> List[Dict]:
        """
        モデルページから商品データを取得
        """
        url = self.BASE_URL + self.MODEL_URLS[model]

        print(f"  アクセス: {url}")

        products = []

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(10)  # JavaScriptの実行を待つ

            # スクロールして全商品をロード
            for i in range(3):
                await page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(2)

            # 商品カードを取得
            items = await page.query_selector_all(".items-container li.item")

            print(f"  商品カード数: {len(items)}")

            for idx, item in enumerate(items):
                try:
                    # 商品名
                    name_input = await item.query_selector('input[name="name"]')
                    product_name = await name_input.get_attribute('value') if name_input else ""

                    # ランク
                    rank_input = await item.query_selector('input[name="rank"]')
                    rank_text = await rank_input.get_attribute('value') if rank_input else ""

                    # 価格
                    price_elem = await item.query_selector('.price p')
                    price_text = await price_elem.inner_text() if price_elem else ""

                    # URL
                    link = await item.query_selector('a[href]')
                    url_path = await link.get_attribute('href') if link else ""
                    full_url = self.BASE_URL + url_path if url_path else ""

                    # 容量を抽出
                    capacity_match = re.search(r'(\d+(?:GB|TB))', product_name, re.IGNORECASE)
                    capacity = capacity_match.group(1).upper() if capacity_match else None

                    # ランクを正規化
                    rank = self.normalize_rank(rank_text)

                    # 価格を数値化
                    price = self.extract_price(price_text)

                    if product_name and price and capacity and rank:
                        products.append({
                            "product_name": product_name,
                            "price": price,
                            "url": full_url,
                            "rank": rank,
                            "rank_raw": rank_text,
                            "capacity": capacity,
                            "model": model,
                            "scraped_at": datetime.now().isoformat(),
                            "source": "イオシス",
                        })

                except Exception as e:
                    print(f"    商品{idx+1}のパースエラー: {e}")
                    continue

            print(f"  取得成功: {len(products)}件")

        except Exception as e:
            print(f"  エラー: {e}")

        return products

    def normalize_rank(self, rank_text: str) -> Optional[str]:
        """ランクテキストを正規化"""
        if not rank_text:
            return None

        text_upper = rank_text.upper()

        if "未使用" in rank_text or "S" in text_upper:
            return "S"
        elif "A" in text_upper:
            return "A"
        elif "B" in text_upper:
            return "B"
        elif "C" in text_upper:
            return "C"
        elif "D" in text_upper or "ジャンク" in rank_text:
            return "D"

        return None

    def extract_price(self, text: str) -> Optional[int]:
        """価格を抽出"""
        numbers = re.findall(r'\d+', text.replace(',', ''))
        if numbers:
            return int(''.join(numbers))
        return None

    async def scrape_all_models(self, models: List[str], output_dir: Path) -> Dict[str, List[Dict]]:
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
                products = await self.scrape_model_page(page, model)
                all_results[model] = products

                # 保存
                if products:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"iosys_{model.replace(' ', '_')}_{timestamp}.json"
                    filepath = output_dir / filename

                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(products, f, ensure_ascii=False, indent=2)

                    print(f"  保存: {filepath}")

                await asyncio.sleep(random.uniform(3, 5))

            await browser.close()

        return all_results


async def main():
    """メイン処理"""
    output_dir = Path(__file__).parent.parent / "data" / "resale" / "iosys"

    scraper = IosysResaleScraperV2()

    models = ["iPhone 12", "iPhone 13", "iPhone 14"]

    print(f"イオシス販売価格調査開始 v2")
    print(f"保存先: {output_dir}")
    print("-" * 60)

    results = await scraper.scrape_all_models(models, output_dir)

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
            print(f"  {rank}ランク: {count}件")

    print("\n完了！")


if __name__ == "__main__":
    asyncio.run(main())
