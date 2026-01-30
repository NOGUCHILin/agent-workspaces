"""
Amazon購入履歴取得スクリプト（デバッグ版）
全ての購入を表示して確認
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
from datetime import datetime
import json
import re

AUTH_DIR = Path(__file__).parent / "auth"
AUTH_DIR.mkdir(exist_ok=True)

def login_amazon(page, email, password):
    """Amazonにログイン"""
    print("Amazonにアクセス中...")
    page.goto('https://www.amazon.co.jp/')
    page.wait_for_load_state('domcontentloaded')
    page.wait_for_timeout(3000)

    # すでにログイン済みかチェック
    content = page.content()
    if 'こんにちは' in content or 'アカウント&リスト' in content:
        print("既にログイン済みです")
        return True

    print("ログイン処理を開始します")
    print("ブラウザで手動でログインしてください（60秒待機）...")
    page.wait_for_timeout(60000)

    return True

def get_all_orders(page, start_date, end_date):
    """全ての注文を取得（デバッグ用）"""
    print("\n購入履歴ページにアクセス中...")
    page.goto('https://www.amazon.co.jp/gp/css/order-history')
    page.wait_for_load_state('domcontentloaded')
    page.wait_for_timeout(3000)

    print("\n" + "="*60)
    print("ページ内容を解析中...")
    print("="*60)

    # ページ全体のスクリーンショットを保存
    screenshot_path = Path(__file__).parent / "amazon_orders_screenshot.png"
    page.screenshot(path=str(screenshot_path), full_page=True)
    print(f"スクリーンショット保存: {screenshot_path}")

    # 年フィルターURLで2026年にアクセス
    print("\n2026年の注文ページにアクセス...")
    page.goto('https://www.amazon.co.jp/gp/your-account/order-history?orderFilter=year-2026')
    page.wait_for_load_state('domcontentloaded')
    page.wait_for_timeout(3000)

    all_purchases = []

    # 複数の可能性のある注文セレクタ
    order_selectors = [
        '.order',
        '.order-card',
        '.a-box-group',
        '[data-order-id]',
        '.shipment'
    ]

    orders = []
    for selector in order_selectors:
        orders = page.query_selector_all(selector)
        if orders:
            print(f"\n✓ セレクタ '{selector}' で {len(orders)}件の要素を発見")
            break

    if not orders:
        print("\n注文要素が見つかりません")
        print("ページのHTMLを保存します...")
        html_path = Path(__file__).parent / "amazon_orders_page.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(page.content())
        print(f"HTML保存: {html_path}")
        return []

    print(f"\n{len(orders)}件の注文を解析中...\n")

    for i, order in enumerate(orders, 1):
        try:
            print(f"\n--- 注文 {i} ---")

            # 注文全体のテキストを取得
            order_text = order.inner_text()
            print(f"注文テキスト（最初の200文字）:\n{order_text[:200]}...\n")

            # 日付を探す
            date_patterns = [
                r'(\d{4})年(\d{1,2})月(\d{1,2})日',
                r'(\d{4})/(\d{1,2})/(\d{1,2})',
            ]

            order_date = None
            for pattern in date_patterns:
                date_match = re.search(pattern, order_text)
                if date_match:
                    year = int(date_match.group(1))
                    month = int(date_match.group(2))
                    day = int(date_match.group(3))
                    order_date = datetime(year, month, day)
                    print(f"日付: {order_date.strftime('%Y年%m月%d日')}")
                    break

            if not order_date:
                print("日付が見つかりません")
                continue

            # 金額を探す
            price_patterns = [
                r'[¥￥]\s?([\d,]+)',
                r'合計[：:]\s*[¥￥]?\s?([\d,]+)',
                r'([\d,]+)\s*円',
            ]

            price = 0
            for pattern in price_patterns:
                price_match = re.search(pattern, order_text)
                if price_match:
                    price_str = price_match.group(1).replace(',', '')
                    price = int(price_str)
                    print(f"金額: ¥{price:,}")
                    break

            if price == 0:
                print("金額が見つかりません")

            # 商品名を探す（リンクから）
            item_links = order.query_selector_all('a[href*="/dp/"], a[href*="/gp/product/"]')
            items = []
            for link in item_links[:5]:  # 最初の5つまで
                item_text = link.inner_text().strip()
                if item_text and len(item_text) > 5:
                    items.append(item_text)

            if items:
                print(f"商品:")
                for item in items[:3]:
                    print(f"  - {item}")
            else:
                print("商品名が見つかりません")

            # 期間内で10万円以上の場合、リストに追加
            if start_date <= order_date <= end_date and price >= 100000:
                all_purchases.append({
                    'date': order_date.strftime('%Y年%m月%d日'),
                    'price': price,
                    'items': items[:3] if items else ['商品名取得できず']
                })
                print(f"\n★★★ 10万円以上の購入を発見！ ★★★")

        except Exception as e:
            print(f"エラー: {e}")
            import traceback
            traceback.print_exc()

    # 2025年も同様に確認
    print("\n\n" + "="*60)
    print("2025年の注文ページにアクセス...")
    print("="*60)
    page.goto('https://www.amazon.co.jp/gp/your-account/order-history?orderFilter=year-2025')
    page.wait_for_load_state('domcontentloaded')
    page.wait_for_timeout(3000)

    orders = []
    for selector in order_selectors:
        orders = page.query_selector_all(selector)
        if orders:
            print(f"\n✓ セレクタ '{selector}' で {len(orders)}件の要素を発見")
            break

    if orders:
        print(f"\n{len(orders)}件の注文を解析中...\n")

        for i, order in enumerate(orders[:10], 1):  # 最初の10件のみ
            try:
                print(f"\n--- 注文 {i} ---")
                order_text = order.inner_text()
                print(f"注文テキスト（最初の200文字）:\n{order_text[:200]}...\n")

                # 日付を探す
                order_date = None
                for pattern in date_patterns:
                    date_match = re.search(pattern, order_text)
                    if date_match:
                        year = int(date_match.group(1))
                        month = int(date_match.group(2))
                        day = int(date_match.group(3))
                        order_date = datetime(year, month, day)
                        print(f"日付: {order_date.strftime('%Y年%m月%d日')}")
                        break

                if not order_date:
                    print("日付が見つかりません")
                    continue

                # 金額を探す
                price = 0
                for pattern in price_patterns:
                    price_match = re.search(pattern, order_text)
                    if price_match:
                        price_str = price_match.group(1).replace(',', '')
                        price = int(price_str)
                        print(f"金額: ¥{price:,}")
                        break

                if price == 0:
                    print("金額が見つかりません")

                # 商品名を探す
                item_links = order.query_selector_all('a[href*="/dp/"], a[href*="/gp/product/"]')
                items = []
                for link in item_links[:5]:
                    item_text = link.inner_text().strip()
                    if item_text and len(item_text) > 5:
                        items.append(item_text)

                if items:
                    print(f"商品:")
                    for item in items[:3]:
                        print(f"  - {item}")

                # 期間内で10万円以上の場合、リストに追加
                if start_date <= order_date <= end_date and price >= 100000:
                    all_purchases.append({
                        'date': order_date.strftime('%Y年%m月%d日'),
                        'price': price,
                        'items': items[:3] if items else ['商品名取得できず']
                    })
                    print(f"\n★★★ 10万円以上の購入を発見！ ★★★")

            except Exception as e:
                print(f"エラー: {e}")

    return all_purchases

def main():
    email = "uprose.info@gmail.com"
    password = "4669uprose"

    start_date = datetime(2025, 4, 1)
    end_date = datetime(2026, 3, 31)

    print("=" * 60)
    print("Amazon購入履歴取得ツール（デバッグ版）")
    print(f"期間: {start_date.strftime('%Y年%m月%d日')} 〜 {end_date.strftime('%Y年%m月%d日')}")
    print(f"対象: 10万円以上の購入")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=['--disable-dev-shm-usage']
        )

        state_file = AUTH_DIR / "amazon_state.json"
        context = browser.new_context(
            storage_state=str(state_file) if state_file.exists() else None,
            locale='ja-JP'
        )

        page = context.new_page()

        try:
            # ログイン
            login_amazon(page, email, password)

            # 全注文取得
            purchases = get_all_orders(page, start_date, end_date)

            # セッション保存
            context.storage_state(path=str(state_file))

            # 結果出力
            print("\n" + "=" * 60)
            print(f"10万円以上の購入: {len(purchases)}件")
            print("=" * 60)

            if purchases:
                total = 0
                for i, purchase in enumerate(purchases, 1):
                    print(f"\n{i}. {purchase['date']}")
                    print(f"   金額: ¥{purchase['price']:,}")
                    if purchase['items']:
                        print(f"   商品:")
                        for item in purchase['items']:
                            print(f"     - {item}")
                    total += purchase['price']

                print("\n" + "=" * 60)
                print(f"合計金額: ¥{total:,}")
                print("=" * 60)

                # JSON保存
                output_file = Path(__file__).parent / f"amazon_purchases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(purchases, f, ensure_ascii=False, indent=2)
                print(f"\n結果を保存しました: {output_file}")
            else:
                print("\n該当する購入はありませんでした")
                print("または、ページ構造の解析に失敗しました")
                print("スクリーンショットとHTMLファイルを確認してください")

            print("\nブラウザを閉じるには何かキーを押してください...")
            input()

        except Exception as e:
            print(f"\nエラー発生: {e}")
            import traceback
            traceback.print_exc()
            print("\nブラウザを閉じるには何かキーを押してください...")
            input()

        finally:
            browser.close()

if __name__ == "__main__":
    main()
