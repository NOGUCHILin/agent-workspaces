"""
イオシス買取価格表スクレイパー（Playwright使用）
買取価格表ページ: https://k-tai-iosys.com/pricelist/smartphone/iphone/
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from playwright.async_api import async_playwright
import re


class IosysBuybackScraper:
    """イオシス買取価格表スクレイパー"""

    BUYBACK_URL = "https://k-tai-iosys.com/pricelist/smartphone/iphone/"

    async def scrape_buyback_prices(self) -> List[Dict]:
        """
        イオシスの買取価格表を取得

        Returns:
            買取価格情報のリスト
        """
        print(f"イオシス買取価格表を取得中...")
        print(f"URL: {self.BUYBACK_URL}")

        results = []

        async with async_playwright() as p:
            # ブラウザ起動
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()

            try:
                # ページアクセス
                await page.goto(self.BUYBACK_URL, wait_until="networkidle", timeout=60000)

                # JavaScriptの実行を待つ
                await page.wait_for_timeout(5000)

                # ページの内容を確認（デバッグ用）
                print("\n=== ページタイトル ===")
                print(await page.title())

                # 価格表のテーブルやリストを探す
                # 複数のセレクタパターンを試す
                table_selectors = [
                    'table',
                    '.price-table',
                    '.pricelist',
                    '#price-list',
                    '[class*="price"]',
                ]

                print("\n=== セレクタ検索 ===")
                for selector in table_selectors:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"  ✓ '{selector}': {len(elements)}個見つかりました")
                    else:
                        print(f"  ✗ '{selector}': 見つかりません")

                # テーブルデータを取得
                tables = await page.query_selector_all('table')

                if not tables:
                    print("\n警告: テーブルが見つかりません。")
                    print("ページの全テキストを確認します...")

                    # ページ全体のテキストを取得してパターンを探す
                    body_text = await page.inner_text('body')

                    # iPhone の名前と価格のパターンを探す
                    # 例: "iPhone 12" "64GB" "Aランク" "10,000円"
                    lines = body_text.split('\n')

                    print(f"\n取得したテキスト行数: {len(lines)}")
                    print("\n最初の50行:")
                    for i, line in enumerate(lines[:50]):
                        if line.strip():
                            print(f"  {i+1}: {line.strip()[:100]}")

                else:
                    print(f"\n✓ {len(tables)}個のテーブルを発見")

                    # 各テーブルをパース
                    for idx, table in enumerate(tables):
                        print(f"\n--- テーブル {idx + 1} ---")

                        # ヘッダー行を取得
                        headers = []
                        header_cells = await table.query_selector_all('thead th, tr:first-child th, tr:first-child td')

                        if header_cells:
                            for cell in header_cells:
                                text = await cell.inner_text()
                                headers.append(text.strip())
                            print(f"  ヘッダー: {headers}")

                        # データ行を取得
                        rows = await table.query_selector_all('tbody tr, tr')
                        print(f"  データ行数: {len(rows)}")

                        for row_idx, row in enumerate(rows[:5]):  # 最初の5行のみ表示
                            cells = await row.query_selector_all('td, th')
                            cell_texts = []
                            for cell in cells:
                                text = await cell.inner_text()
                                cell_texts.append(text.strip())
                            if cell_texts:
                                print(f"    行{row_idx + 1}: {cell_texts}")

                        # 実際のデータをパース
                        for row in rows:
                            cells = await row.query_selector_all('td')
                            if len(cells) >= 3:  # 最低3列（モデル、容量、価格など）
                                cell_texts = []
                                for cell in cells:
                                    text = await cell.inner_text()
                                    cell_texts.append(text.strip())

                                # データ構造を推測してパース
                                # 一般的なパターン: [モデル, 容量, Aランク, Bランク, Cランク]
                                if len(cell_texts) >= 2:
                                    result = {
                                        "raw_data": cell_texts,
                                        "scraped_at": datetime.now().isoformat(),
                                        "source": "イオシス買取"
                                    }
                                    results.append(result)

                # スクリーンショットを保存（デバッグ用）
                screenshot_path = Path(__file__).parent.parent / "debug_iosys_buyback.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                print(f"\nスクリーンショット保存: {screenshot_path}")

            except Exception as e:
                print(f"エラー: {e}")
                import traceback
                traceback.print_exc()

            finally:
                await browser.close()

        print(f"\n取得完了: {len(results)}件")
        return results


async def main():
    """メイン処理"""
    scraper = IosysBuybackScraper()
    results = await scraper.scrape_buyback_prices()

    # 結果を保存
    if results:
        output_dir = Path(__file__).parent.parent / "data" / "buyback"
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"iosys_buyback_{timestamp}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n保存完了: {output_file}")
    else:
        print("\n保存するデータがありません")


if __name__ == "__main__":
    asyncio.run(main())
