"""
Amazon購入履歴取得スクリプト
2025年4月〜2026年3月の10万円以上の購入を抽出
"""
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from pathlib import Path
from datetime import datetime
import json
import re

AUTH_DIR = Path(__file__).parent / "auth"
AUTH_DIR.mkdir(exist_ok=True)
BLOCKED_RESOURCES = ['image', 'stylesheet', 'font', 'media']

def block_resources(page):
    """不要なリソースをブロック"""
    def handler(route):
        if route.request.resource_type in BLOCKED_RESOURCES:
            route.abort()
        else:
            route.continue_()
    page.route('**/*', handler)

def login_amazon(page, email, password):
    """Amazonにログイン"""
    print("Amazonにアクセス中...")
    page.goto('https://www.amazon.co.jp/')
    page.wait_for_load_state('domcontentloaded')

    # すでにログイン済みかチェック
    content = page.content()
    if 'こんにちは' in content or 'アカウント&リスト' in content:
        print("既にログイン済みです")
        return True

    # ログインボタンをクリック
    print("ログインページに移動中...")
    try:
        # 複数の可能性のあるセレクタを試す
        selectors = [
            'a#nav-link-accountList',
            'a[href*="ap_signin_notification_privacy_notice"]',
            'a:has-text("ログイン")',
            '#nav-signin-tooltip a'
        ]

        clicked = False
        for selector in selectors:
            try:
                page.click(selector, timeout=3000)
                clicked = True
                break
            except:
                continue

        if not clicked:
            print("ログインボタンが見つかりません。手動でログインしてください（30秒待機）...")
            page.wait_for_timeout(30000)
            return True

    except Exception as e:
        print(f"ログインボタンクリックエラー: {e}")

    page.wait_for_load_state('domcontentloaded')

    # メールアドレス入力
    print("メールアドレスを入力中...")
    try:
        # メールアドレス入力欄を探す
        email_selectors = ['input#ap_email', 'input[name="email"]', 'input[type="email"]']
        for selector in email_selectors:
            try:
                page.fill(selector, email, timeout=5000)
                break
            except:
                continue

        # 続行ボタンをクリック
        continue_selectors = ['input#continue', 'input[type="submit"]', '#continue']
        for selector in continue_selectors:
            try:
                page.click(selector, timeout=3000)
                break
            except:
                continue

        page.wait_for_load_state('domcontentloaded')
    except Exception as e:
        print(f"メールアドレス入力エラー: {e}")
        print("手動でメールアドレスを入力してください（30秒待機）...")
        page.wait_for_timeout(30000)

    # パスワード入力
    print("パスワードを入力中...")
    try:
        password_selectors = ['input#ap_password', 'input[name="password"]', 'input[type="password"]']
        for selector in password_selectors:
            try:
                page.fill(selector, password, timeout=5000)
                break
            except:
                continue

        # サインインボタンをクリック
        signin_selectors = ['input#signInSubmit', 'input[type="submit"]', '#signInSubmit']
        for selector in signin_selectors:
            try:
                page.click(selector, timeout=3000)
                break
            except:
                continue

        page.wait_for_load_state('domcontentloaded')
    except Exception as e:
        print(f"パスワード入力エラー: {e}")
        print("手動でパスワードを入力してください（30秒待機）...")
        page.wait_for_timeout(30000)

    # 2段階認証やCAPTCHAの可能性があるため待機
    print("ログイン処理を確認中（30秒待機）...")
    page.wait_for_timeout(30000)

    content = page.content()
    if 'こんにちは' in content or 'アカウント&リスト' in content:
        print("ログイン成功")
        return True
    else:
        print("ログイン状態を確認できません。手動で確認してください")
        return True  # 続行を試みる

def get_purchase_history(page, start_date, end_date):
    """購入履歴を取得"""
    print("購入履歴ページにアクセス中...")
    page.goto('https://www.amazon.co.jp/gp/css/order-history')
    page.wait_for_load_state('domcontentloaded')

    purchases = []

    # 年フィルターを試す
    years_to_check = ['2026', '2025']

    for year in years_to_check:
        print(f"\n{year}年の購入履歴を取得中...")

        # 年フィルターURLで直接アクセス
        try:
            filter_url = f'https://www.amazon.co.jp/gp/your-account/order-history?orderFilter=year-{year}'
            page.goto(filter_url)
            page.wait_for_load_state('domcontentloaded')
            page.wait_for_timeout(2000)  # ページ読み込み待機
        except Exception as e:
            print(f"年フィルターアクセスエラー: {e}")
            continue

        # ページネーション対応
        page_num = 1
        max_pages = 20  # 最大20ページまで
        found_old_dates = False

        while page_num <= max_pages and not found_old_dates:
            print(f"  ページ {page_num} を処理中...")

            # 注文カードを取得
            try:
                page.wait_for_selector('.order', timeout=10000)
            except:
                print("  注文が見つかりませんでした")
                break

            orders = page.query_selector_all('.order')
            print(f"  {len(orders)}件の注文を確認中...")

            for order in orders:
                try:
                    # 注文日を取得
                    date_elems = order.query_selector_all('.a-color-secondary, .a-size-base')
                    order_date_text = ""

                    for elem in date_elems:
                        text = elem.inner_text()
                        if '年' in text and '月' in text and '日' in text:
                            order_date_text = text
                            break

                    if not order_date_text:
                        continue

                    # 日付を解析
                    date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', order_date_text)
                    if not date_match:
                        continue

                    order_year = int(date_match.group(1))
                    order_month = int(date_match.group(2))
                    order_day = int(date_match.group(3))

                    order_date = datetime(order_year, order_month, order_day)

                    # 対象期間より古い日付が見つかったら、この年の処理を終了
                    if order_date < start_date:
                        found_old_dates = True
                        break

                    # 期間内かチェック
                    if not (start_date <= order_date <= end_date):
                        continue

                    # 金額を取得（複数の可能性のあるセレクタ）
                    price_text = ""
                    price_selectors = [
                        '.a-color-price',
                        '.yohtmlc-order-total .a-color-base',
                        '.value',
                        'span:has-text("￥")',
                        'span:has-text("¥")'
                    ]

                    for selector in price_selectors:
                        try:
                            price_elems = order.query_selector_all(selector)
                            for elem in price_elems:
                                text = elem.inner_text()
                                if '¥' in text or '￥' in text or text.replace(',', '').isdigit():
                                    price_text = text
                                    break
                            if price_text:
                                break
                        except:
                            continue

                    if not price_text:
                        continue

                    # 金額を解析
                    price_match = re.search(r'[¥￥]?\s?([\d,]+)', price_text)
                    if not price_match:
                        continue

                    price = int(price_match.group(1).replace(',', ''))

                    # 10万円以上のみ
                    if price < 100000:
                        continue

                    # 商品名を取得
                    item_links = order.query_selector_all('.a-link-normal')
                    items = []
                    for link in item_links:
                        item_text = link.inner_text().strip()
                        # URLがある（商品リンク）かつ、適切な長さのテキスト
                        href = link.get_attribute('href')
                        if item_text and len(item_text) > 5 and href and '/dp/' in href:
                            items.append(item_text)

                    if not items:
                        # リンクがない場合、テキストから商品名を探す
                        text_elems = order.query_selector_all('.a-size-base, .a-size-medium')
                        for elem in text_elems:
                            text = elem.inner_text().strip()
                            if text and len(text) > 10 and '年' not in text and '¥' not in text:
                                items.append(text)
                                if len(items) >= 3:
                                    break

                    purchases.append({
                        'date': order_date.strftime('%Y年%m月%d日'),
                        'price': price,
                        'items': items[:3] if items else ['商品名取得できず']
                    })

                    print(f"    ✓ {order_date.strftime('%Y/%m/%d')} - ¥{price:,} - {items[0] if items else '商品名取得できず'}")

                except Exception as e:
                    print(f"    注文処理エラー: {e}")
                    continue

            if found_old_dates:
                print("  対象期間より古い日付に到達したため、この年の処理を終了します")
                break

            # 次のページがあるかチェック
            try:
                # 複数の次ページボタンパターン
                next_selectors = [
                    'ul.a-pagination li.a-last:not(.a-disabled) a',
                    'a:has-text("次へ")',
                    '.a-pagination .a-last a'
                ]

                next_button = None
                for selector in next_selectors:
                    try:
                        next_button = page.query_selector(selector)
                        if next_button:
                            break
                    except:
                        continue

                if next_button:
                    next_button.click()
                    page.wait_for_load_state('domcontentloaded')
                    page.wait_for_timeout(2000)
                    page_num += 1
                else:
                    print("  次のページがありません")
                    break
            except Exception as e:
                print(f"  ページネーションエラー: {e}")
                break

    return purchases

def main():
    email = "uprose.info@gmail.com"
    password = "4669uprose"

    start_date = datetime(2025, 4, 1)
    end_date = datetime(2026, 3, 31)

    print("=" * 60)
    print("Amazon購入履歴取得ツール")
    print(f"期間: {start_date.strftime('%Y年%m月%d日')} 〜 {end_date.strftime('%Y年%m月%d日')}")
    print(f"対象: 10万円以上の購入")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # 2段階認証対応のため表示
            args=['--disable-dev-shm-usage']
        )

        state_file = AUTH_DIR / "amazon_state.json"
        context = browser.new_context(
            storage_state=str(state_file) if state_file.exists() else None,
            locale='ja-JP'
        )

        page = context.new_page()

        # リソースブロックは一旦無効化（画像が必要な場合があるため）
        # block_resources(page)

        try:
            # ログイン
            if not login_amazon(page, email, password):
                print("\nログインに失敗したか、追加の認証が必要です")
                print("ブラウザで手動で認証を完了してください（60秒待機）...")
                page.wait_for_timeout(60000)

            # 購入履歴取得
            purchases = get_purchase_history(page, start_date, end_date)

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
                        print(f"   商品: {purchase['items'][0]}")
                        for item in purchase['items'][1:]:
                            print(f"         {item}")
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

        except Exception as e:
            print(f"\nエラー発生: {e}")
            import traceback
            traceback.print_exc()

        finally:
            print("\nブラウザを閉じています...")
            browser.close()

if __name__ == "__main__":
    main()
