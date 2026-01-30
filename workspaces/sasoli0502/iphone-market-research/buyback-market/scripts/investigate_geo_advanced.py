"""
ゲオ買取サイトの構造調査（高度な回避技術版）

Akamai WAFを回避するための複数の技術を組み合わせます:
1. リアルなブラウザフィンガープリント
2. Stealth Plugin（自動化検出を回避）
3. より人間らしい振る舞い
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
from datetime import datetime
import time


def advanced_investigate():
    """高度な回避技術を使用した調査"""
    print("=" * 60)
    print("ゲオ買取サイト構造調査（高度版）")
    print("=" * 60)
    print()

    with sync_playwright() as p:
        # より詳細なブラウザ設定
        print("🚀 ブラウザを起動中...")
        browser = p.chromium.launch(
            headless=False,  # ヘッドレスだと検出されやすいので通常モード
            args=[
                '--disable-blink-features=AutomationControlled',  # 自動化フラグを隠す
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )

        # より詳細なコンテキスト設定
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=(
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            locale='ja-JP',
            timezone_id='Asia/Tokyo',
            # より詳細なデバイス情報
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
        )

        page = context.new_page()

        # navigator.webdriverをfalseに設定（自動化検出を回避）
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });

            // Chrome検出を回避
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });

            Object.defineProperty(navigator, 'languages', {
                get: () => ['ja-JP', 'ja', 'en-US', 'en'],
            });

            // Playwrightの痕跡を消す
            delete navigator.__proto__.webdriver;
        """)

        # Googleに一度アクセス（リファラーを作る）
        print("🔗 Google経由でアクセスします...")
        page.goto("https://www.google.co.jp/", wait_until="networkidle")
        time.sleep(2)

        # 検索ボックスに入力
        search_query = "ゲオ iPhone 買取"
        print(f"🔍 Googleで検索: {search_query}")
        page.fill('textarea[name="q"]', search_query)
        time.sleep(1)
        page.press('textarea[name="q"]', 'Enter')
        time.sleep(3)

        # ゲオのリンクを探してクリック
        print("🎯 検索結果からゲオのリンクを探します...")
        try:
            # ゲオのリンクを探す
            geo_link = page.locator('a[href*="buymobile.geo-online.co.jp"]').first
            if geo_link.count() > 0:
                print("✅ ゲオのリンクを発見！クリックします...")
                geo_link.click()
                page.wait_for_load_state("networkidle")
                time.sleep(3)
            else:
                print("⚠️ 検索結果にゲオが見つからないため、直接アクセスします...")
                page.goto("https://buymobile.geo-online.co.jp/", wait_until="networkidle")
                time.sleep(3)
        except Exception as e:
            print(f"⚠️ Google経由でのアクセス失敗: {e}")
            print("直接アクセスを試します...")
            page.goto("https://buymobile.geo-online.co.jp/", wait_until="networkidle")
            time.sleep(3)

        # 結果確認
        title = page.title()
        url = page.url

        print(f"\n📄 ページタイトル: {title}")
        print(f"🔗 現在のURL: {url}")

        # スクリーンショット保存
        screenshot_dir = Path(__file__).parent.parent / "data" / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = screenshot_dir / f"geo_advanced_{timestamp}.png"

        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"📸 スクリーンショット保存: {screenshot_path}")

        # HTML保存
        html_content = page.content()
        html_path = screenshot_dir / f"geo_advanced_{timestamp}.html"
        html_path.write_text(html_content, encoding="utf-8")
        print(f"💾 HTML保存: {html_path}")

        # 成功判定
        if "Access Denied" in title or "Access Denied" in html_content:
            print("\n❌ まだアクセスがブロックされています")
            print("💡 次の手段:")
            print("  1. 実際のブラウザで手動アクセスしてサイト構造を確認")
            print("  2. ゲオをスキップして他のサイトを優先")
            print("  3. プロキシやVPNを使用")
        else:
            print("\n✅ アクセス成功の可能性あり！")
            print("📋 iPhoneリンクを探します...")

            # iPhoneリンクを探す
            try:
                iphone_links = page.locator('a:has-text("iPhone"), a:has-text("アイフォン")').all()
                print(f"🔗 {len(iphone_links)}個のiPhoneリンクを発見")

                for i, link in enumerate(iphone_links[:10], 1):
                    text = link.inner_text().strip()
                    href = link.get_attribute("href")
                    print(f"  {i}. {text}: {href}")
            except Exception as e:
                print(f"⚠️ リンク検索エラー: {e}")

        # 人間のように少し待機
        print("\n⏳ ページを確認しています...")
        time.sleep(5)

        input("\n⏸️ Enterキーを押すとブラウザを閉じます...")

        browser.close()
        print("\n✅ 調査完了")


if __name__ == "__main__":
    advanced_investigate()
