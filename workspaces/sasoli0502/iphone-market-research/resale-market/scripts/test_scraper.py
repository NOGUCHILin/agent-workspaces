"""
スクレイパーのテストスクリプト（1モデルのみ）
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
import time


async def test_iosys_search():
    """イオシスの検索ページ構造を確認"""
    print("=== イオシス検索テスト ===")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()

        # イオシスのiPhone一覧ページ
        url = "https://iosys.co.jp/items/smartphone/iphone"
        print(f"アクセス: {url}")

        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)

        # スクリーンショット
        screenshot_path = Path(__file__).parent.parent / "test_iosys.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"スクリーンショット: {screenshot_path}")

        # ページのテキストを取得
        body_text = await page.inner_text('body')
        lines = [l.strip() for l in body_text.split('\n') if l.strip()]

        print(f"\nページテキスト行数: {len(lines)}")
        print("\n最初の100行:")
        for i, line in enumerate(lines[:100]):
            print(f"{i+1}: {line}")

        # 商品カードのセレクタを試す
        print("\n=== セレクタテスト ===")
        selectors = [
            '.item-box',
            '.product-card',
            '.goods-item',
            'article',
            '[data-product-id]',
            '.product-item',
            '.item',
        ]

        for selector in selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                print(f"✓ '{selector}': {len(elements)}個")

                # 最初の要素の内容を確認
                if len(elements) > 0:
                    first_elem = elements[0]
                    text = await first_elem.inner_text()
                    print(f"  最初の要素のテキスト: {text[:200]}")
            else:
                print(f"✗ '{selector}': 見つかりません")

        print("\nブラウザを30秒間開いたままにします...")
        time.sleep(30)

        await browser.close()


async def main():
    await test_iosys_search()


if __name__ == "__main__":
    asyncio.run(main())
