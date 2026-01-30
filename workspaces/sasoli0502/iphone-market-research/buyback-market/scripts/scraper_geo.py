"""
ゲオ買取価格スクレイパー（Playwright版）

Akamai WAFを回避するために高度なブラウザ自動化技術を使用します。
"""

from browser_scraper_base import BrowserScraperBase
from playwright.sync_api import sync_playwright
from models import IPHONE_MODELS
from pathlib import Path
from datetime import datetime
import json
import time
import re


class GeoScraper:
    """
    ゲオ買取価格スクレイパー

    Playwrightを使用してゲオのWAFを回避しながらデータを収集します。
    """

    BASE_URL = "https://buymobile.geo-online.co.jp/"
    SEARCH_URL = "https://buymobile.geo-online.co.jp/mitsumori/"

    def __init__(self, headless: bool = False):
        """
        Args:
            headless: ヘッドレスモード（WAF回避のため通常はFalse推奨）
        """
        self.headless = headless
        self.results = []

    def _setup_browser(self, p):
        """WAF回避のためのブラウザ設定"""
        browser = p.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=(
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            locale='ja-JP',
            timezone_id='Asia/Tokyo',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
        )

        return browser, context

    def _add_stealth_scripts(self, page):
        """自動化検出を回避するスクリプトを追加"""
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ja-JP', 'ja', 'en-US', 'en'],
            });
            delete navigator.__proto__.webdriver;
        """)

    def scrape_model(self, model: str, capacity: str) -> list[dict]:
        """
        指定モデル・容量の買取価格を取得

        Args:
            model: モデル名（例: "iPhone 15 Pro"）
            capacity: 容量（例: "256GB"）

        Returns:
            買取価格データのリスト
        """
        search_query = f"{model} {capacity}"
        print(f"\n🔍 検索: {search_query}")

        with sync_playwright() as p:
            browser, context = self._setup_browser(p)
            page = context.new_page()
            self._add_stealth_scripts(page)

            try:
                # メインページにアクセス
                print(f"📄 {self.BASE_URL} にアクセス中...")
                page.goto(self.BASE_URL, wait_until="domcontentloaded", timeout=60000)
                time.sleep(3)  # ページの読み込みを待つ

                # モーダルを閉じる（表示されている場合）
                print("🔲 モーダルを閉じます...")
                try:
                    # モーダルの閉じるボタンを探す
                    close_button = page.query_selector('.modal .close, .modal button, .modal [class*="close"]')
                    if close_button and close_button.is_visible():
                        close_button.click()
                        time.sleep(1)
                        print("  ✓ モーダルを閉じました")
                    else:
                        # モーダル背景をクリック（または Escape キー）
                        page.keyboard.press('Escape')
                        time.sleep(1)
                        print("  ✓ Escapeキーでモーダルを閉じました")
                except Exception as e:
                    print(f"  ⚠️ モーダル処理スキップ: {e}")

                # 検索ボックスに入力
                print(f"⌨️  検索ボックスに入力: {search_query}")
                page.fill('input[name="search1"]', search_query)
                time.sleep(1)

                # 検索実行
                print("🔎 検索実行...")
                page.click('button[type="submit"]')
                page.wait_for_load_state("domcontentloaded", timeout=60000)
                time.sleep(4)  # 検索結果の表示を待つ

                # 検索結果ページのURL
                current_url = page.url
                print(f"📍 現在のURL: {current_url}")

                # スクリーンショット保存（デバッグ用）
                screenshot_dir = Path(__file__).parent.parent / "data" / "screenshots"
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_filename = search_query.replace(" ", "_")
                screenshot_path = screenshot_dir / f"geo_search_{safe_filename}_{timestamp}.png"
                page.screenshot(path=str(screenshot_path))
                print(f"📸 スクリーンショット: {screenshot_path}")

                # 買取価格を抽出
                results = self._extract_prices(page, model, capacity, current_url)

                print(f"✅ {len(results)}件のデータを取得")
                return results

            except Exception as e:
                print(f"❌ エラー: {e}")
                return []

            finally:
                browser.close()

    def _extract_prices(self, page, model: str, capacity: str, url: str) -> list[dict]:
        """ページから買取価格を抽出"""
        results = []
        timestamp = datetime.now().isoformat()

        try:
            # 商品カードを探す（複数のセレクターを試す）
            selectors = [
                '.product-item',
                '.product-card',
                '.item',
                'article',
                '[class*="product"]',
            ]

            products = []
            for selector in selectors:
                products = page.query_selector_all(selector)
                if products:
                    print(f"  ✓ セレクター '{selector}' で{len(products)}件発見")
                    break

            if not products:
                print("  ⚠️ 商品が見つかりませんでした")
                # HTMLを保存してデバッグ
                html_path = Path(__file__).parent.parent / "data" / "debug" / f"geo_no_results_{timestamp}.html"
                html_path.parent.mkdir(parents=True, exist_ok=True)
                html_path.write_text(page.content(), encoding='utf-8')
                print(f"  💾 デバッグ用HTML保存: {html_path}")
                return results

            # 各商品から情報を抽出
            for i, product in enumerate(products[:20], 1):  # 最初の20件まで
                try:
                    # 商品名
                    name_elem = product.query_selector('h2, h3, .title, [class*="name"], [class*="title"]')
                    product_name = name_elem.inner_text().strip() if name_elem else "不明"

                    # 価格（複数パターンを試す）
                    price_elem = product.query_selector('.price, [class*="price"], strong')
                    price_text = price_elem.inner_text() if price_elem else ""

                    # 価格から数値を抽出
                    price_match = re.search(r'([0-9,]+)円', price_text)
                    if price_match:
                        buyback_price = int(price_match.group(1).replace(',', ''))
                    else:
                        print(f"  ⚠️ 商品{i}: 価格が見つかりません（{product_name}）")
                        continue

                    # 詳細ページのURL
                    link_elem = product.query_selector('a')
                    detail_url = link_elem.get_attribute('href') if link_elem else ""
                    if detail_url and detail_url.startswith('/'):
                        detail_url = self.BASE_URL.rstrip('/') + detail_url

                    # 状態を推測（未使用品、中古など）
                    condition = "中古品"
                    if "未使用" in product_name:
                        condition = "未使用品"
                    elif "新品" in product_name:
                        condition = "新品"

                    result = {
                        "product_name": product_name,
                        "model": model,
                        "capacity": capacity,
                        "condition": condition,
                        "buyback_price": buyback_price,
                        "url": detail_url or url,
                        "site": "ゲオ",
                        "scraped_at": timestamp,
                    }

                    results.append(result)
                    print(f"  {i}. {product_name}: ¥{buyback_price:,}")

                except Exception as e:
                    print(f"  ⚠️ 商品{i}の解析エラー: {e}")
                    continue

        except Exception as e:
            print(f"  ❌ ページ解析エラー: {e}")

        return results

    def scrape_test_models(self) -> list[dict]:
        """
        テスト用：3モデルのみスクレイピング

        Returns:
            収集したデータのリスト
        """
        test_models = [
            ("iPhone X", "64GB"),
            ("iPhone X", "256GB"),
            ("iPhone XR", "64GB"),
        ]

        all_results = []

        print("=" * 60)
        print("ゲオ買取価格スクレイピング（テストモード）")
        print("=" * 60)

        for model, capacity in test_models:
            results = self.scrape_model(model, capacity)
            all_results.extend(results)

            # サーバー負荷軽減のため待機
            time.sleep(5)

        # 結果を保存
        if all_results:
            output_dir = Path(__file__).parent.parent / "data" / "raw" / "geo"
            output_dir.mkdir(parents=True, exist_ok=True)

            for model, capacity in test_models:
                model_results = [r for r in all_results if r["model"] == model and r["capacity"] == capacity]
                if model_results:
                    filename = f"geo_{model.replace(' ', '_')}_{capacity}.json"
                    output_path = output_dir / filename
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(model_results, f, ensure_ascii=False, indent=2)
                    print(f"\n💾 保存: {output_path}")

        print(f"\n✅ 完了: {len(all_results)}件のデータを収集")
        return all_results


def main():
    """メイン実行"""
    scraper = GeoScraper(headless=False)  # WAF回避のため通常モード
    results = scraper.scrape_test_models()

    if results:
        print("\n📊 収集データサマリー:")
        for r in results:
            print(f"  - {r['model']} {r['capacity']}: ¥{r['buyback_price']:,}")


if __name__ == "__main__":
    main()
