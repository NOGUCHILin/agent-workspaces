"""
朝の金額KPI入力自動化スクリプト（高速版）

Playwright高速化ルール準拠:
- slow_mo不使用
- time.sleep()不使用（動的待機のみ）
- 不要リソースブロック（スプレッドシート以外）
- storage_stateでセッション再利用

使用方法:
    uv run python scripts/morning_kpi_fast.py              # 通常実行
    uv run python scripts/morning_kpi_fast.py --dry-run    # データ収集のみ
    uv run python scripts/morning_kpi_fast.py --auto-confirm  # 確認なしで入力

必要な環境変数(.env):
    - LINE_EMAIL, LINE_PASSWORD
    - GOOGLE_EMAIL, GOOGLE_PASSWORD
    - YAHOO_EMAIL, YAHOO_PASSWORD
    - SPREADSHEET_URL
"""

import argparse
import csv
import json
import os
import platform
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

# 環境変数読み込み（スクリプトディレクトリの.envも読む）
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
load_dotenv(SKILL_DIR / ".env")
load_dotenv()  # カレントディレクトリの.envも

# ディレクトリ設定
DOWNLOADS_DIR = SCRIPT_DIR / "downloads"
AUTH_DIR = SCRIPT_DIR / "auth"
BACKUP_DIR = SCRIPT_DIR / "backups"
DOWNLOADS_DIR.mkdir(exist_ok=True)
AUTH_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

# ブロックするリソースタイプ
BLOCKED_RESOURCES = ["image", "stylesheet", "font", "media"]

# 日付計算
TODAY = datetime.now()
YESTERDAY = TODAY - timedelta(days=1)

# セッションファイル
SESSION_FILES = {
    "line": AUTH_DIR / "line_state.json",
    "google": AUTH_DIR / "google_state.json",
    "yahoo": AUTH_DIR / "yahoo_state.json",
    "spreadsheet": AUTH_DIR / "spreadsheet_state.json",
}

# Google広告の概要ページURL
GOOGLE_ADS_OVERVIEW_URL = (
    "https://ads.google.com/aw/overview"
    "?ocid=407079569&euid=592647351&__u=9861655999"
    "&uscid=407079569&__c=5657099081&authuser=0"
)


# ========== ユーティリティ ==========


def fmt_date_short(dt: datetime) -> str:
    """日付を '1/29' 形式にフォーマット（OS非依存）"""
    return f"{dt.month}/{dt.day}"


def fmt_date_japanese(dt: datetime) -> str:
    """日付を '1月29日' 形式にフォーマット（OS非依存）"""
    return f"{dt.month}月{dt.day}日"


def fmt_date_spreadsheet(dt: datetime) -> str:
    """日付を '26/01/29' 形式にフォーマット（スプレッドシート検索用）"""
    return dt.strftime("%y/%m/%d")


def parse_number(text: str) -> int:
    """テキストから数値を抽出（カンマ・万・¥ 対応）"""
    text = text.strip()
    # ¥13.9万 → 139000
    man_match = re.search(r"[¥￥]?([\d.]+)\s*万", text)
    if man_match:
        return int(float(man_match.group(1)) * 10000)
    # ¥12,345 or 12,345 or 12345
    num_str = re.sub(r"[¥￥,\s]", "", text)
    # 小数点以下は四捨五入
    try:
        return round(float(num_str))
    except ValueError:
        return 0


def block_resources(page: Page):
    """不要リソースをブロックして高速化"""

    def handler(route):
        if route.request.resource_type in BLOCKED_RESOURCES:
            route.abort()
        else:
            route.continue_()

    page.route("**/*", handler)


def load_session(browser: Browser, service: str) -> BrowserContext:
    """セッションを再利用してコンテキストを作成"""
    state_file = SESSION_FILES.get(service)
    try:
        if state_file and state_file.exists():
            context = browser.new_context(storage_state=str(state_file))
            print(f"  [{service}] セッションを再利用")
            return context
    except Exception:
        pass
    context = browser.new_context()
    print(f"  [{service}] 新規セッション")
    return context


def save_session(context: BrowserContext, service: str):
    """セッションを保存"""
    state_file = SESSION_FILES.get(service)
    if state_file:
        try:
            context.storage_state(path=str(state_file))
        except Exception:
            pass


def wait_for_user(message: str):
    """ユーザーの操作完了を待つ"""
    print(f"\n⏳ {message}")
    input("  → 完了したらEnterを押してください: ")


# ========== メインクラス ==========


class MorningKPIFast:
    """朝の金額KPI入力自動化（高速版）"""

    def __init__(self, dry_run: bool = False, auto_confirm: bool = False):
        self.dry_run = dry_run
        self.auto_confirm = auto_confirm
        self.browser: Browser = None
        self.playwright = None
        self.collected_data = {
            "line_delivery": None,
            "google_conversions": None,
            "google_cost_per_conv": None,
            "google_cost": None,
            "yahoo_conversions": None,
            "yahoo_cost_per_conv": None,
            "yahoo_cost": None,
            "line_friends": None,
            "line_reach": None,
        }
        self.target_row: int = None  # スプレッドシートの対象行番号

    def start(self):
        """ブラウザ起動"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=False,
            args=["--disable-dev-shm-usage"],
        )
        print("ブラウザを起動しました")

    def stop(self):
        """ブラウザ終了"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("ブラウザを終了しました")

    # ========== 1. LINE配信数 ==========
    def get_line_delivery_count(self) -> int:
        """LINE配信数を取得（B列用）"""
        print("\n" + "=" * 50)
        print("STEP 1: LINE配信数の取得")
        print("=" * 50)

        context = load_session(self.browser, "line")
        page = context.new_page()
        block_resources(page)

        try:
            # LINE Official Account Manager にアクセス
            page.goto(
                "https://manager.line.biz/", wait_until="domcontentloaded"
            )

            # ログインが必要かチェック
            if "login" in page.url.lower() or "account.line.biz" in page.url:
                print("  LINEにログインします...")

                # ログインページに遷移
                page.goto(
                    "https://account.line.biz/login",
                    wait_until="domcontentloaded",
                )

                # 「LINEアカウントでログイン」ボタンをクリック
                try:
                    line_login_btn = page.locator(
                        'a:has-text("LINEアカウント"), '
                        'button:has-text("LINEアカウント"), '
                        'a:has-text("LINE Account")'
                    )
                    line_login_btn.first.wait_for(timeout=10000)
                    line_login_btn.first.click()
                    page.wait_for_load_state("domcontentloaded")
                except Exception:
                    print("  LINEアカウントボタンが見つかりません。手動でログインしてください。")
                    wait_for_user("LINEにログインしてください")

                # メール・パスワード入力
                email_input = page.locator(
                    'input[name="tid"], input[type="email"], input[name="email"]'
                )
                if email_input.count() > 0:
                    email = os.getenv("LINE_EMAIL", "")
                    password = os.getenv("LINE_PASSWORD", "")
                    if not email or not password:
                        print("  LINE_EMAIL / LINE_PASSWORD が設定されていません")
                        wait_for_user("手動でログインしてください")
                    else:
                        email_input.first.fill(email)
                        pw_input = page.locator(
                            'input[name="tpasswd"], input[type="password"], input[name="password"]'
                        )
                        pw_input.first.fill(password)
                        submit_btn = page.locator(
                            'button[type="submit"], button:has-text("ログイン"), button:has-text("Log in")'
                        )
                        submit_btn.first.click()
                        page.wait_for_load_state("domcontentloaded")

                # 2FA認証チェック（認証番号がスマホに送られる場合）
                try:
                    auth_code = page.locator(
                        'text=/認証番号|verification|確認コード/'
                    )
                    auth_code.wait_for(timeout=5000)
                    # 認証番号が表示されている
                    code_text = page.locator(
                        '[class*="code"], [class*="number"], [class*="verification"]'
                    ).first.inner_text()
                    print(f"  認証番号: {code_text}")
                    wait_for_user(
                        "スマートフォンのLINEアプリで上記の認証番号を入力してください"
                    )
                except Exception:
                    pass  # 2FAなし or すでに通過

                # 400エラーチェック
                try:
                    error_page = page.locator('text=/400|Error|エラー/')
                    error_page.wait_for(timeout=3000)
                    go_home = page.locator(
                        'a:has-text("Go Home"), a:has-text("ホーム")'
                    )
                    if go_home.count() > 0:
                        go_home.first.click()
                        page.wait_for_load_state("domcontentloaded")
                except Exception:
                    pass

                # ログイン完了を待つ
                try:
                    page.wait_for_url(
                        "**/manager.line.biz/**", timeout=30000
                    )
                except Exception:
                    wait_for_user("ログインが完了するまで待ってください")

            # セッション保存（ログイン後すぐ）
            save_session(context, "line")

            # アカウント選択: アップルバイヤーズ
            try:
                account_link = page.locator(
                    'a[href*="@906dpbsc"], a:has-text("アップルバイヤーズ")'
                )
                account_link.first.wait_for(timeout=15000)
                account_link.first.click()
                page.wait_for_load_state("domcontentloaded")
            except Exception:
                print("  アカウント選択ページが表示されません。直接アクセスします...")
                page.goto(
                    "https://manager.line.biz/account/@906dpbsc",
                    wait_until="domcontentloaded",
                )

            # メッセージ配信 → メッセージリスト
            page.locator('a:has-text("メッセージ配信")').first.wait_for(
                timeout=10000
            )
            page.locator('a:has-text("メッセージ配信")').first.click()
            page.wait_for_load_state("domcontentloaded")

            msg_list = page.locator(
                'a:has-text("メッセージリスト"), '
                'span:has-text("メッセージリスト")'
            )
            msg_list.first.wait_for(timeout=10000)
            msg_list.first.click()
            page.wait_for_load_state("domcontentloaded")

            # 「配信済み」タブ
            delivered_tab = page.locator(
                'button:has-text("配信済み"), '
                'a:has-text("配信済み"), '
                '[role="tab"]:has-text("配信済み")'
            )
            delivered_tab.first.wait_for(timeout=10000)
            delivered_tab.first.click()
            page.wait_for_load_state("domcontentloaded")

            # 配信リストの読み込みを待つ
            page.wait_for_timeout(2000)  # リスト描画を待つ

            # 前日の配信を探す
            yesterday_jp = fmt_date_japanese(YESTERDAY)
            delivery_count = 0

            # ページ全体のテキストから前日の配信を検索
            body_text = page.locator("body").inner_text()
            if yesterday_jp in body_text:
                # 配信人数を探す（「X,XXX人」パターン）
                # 前日の日付付近のテキストから抽出
                lines = body_text.split("\n")
                found_date = False
                for line in lines:
                    if yesterday_jp in line:
                        found_date = True
                    if found_date:
                        match = re.search(r"([\d,]+)\s*人", line)
                        if match:
                            delivery_count = int(
                                match.group(1).replace(",", "")
                            )
                            break
                if not found_date or delivery_count == 0:
                    # 配信がなかった場合
                    print(f"  {yesterday_jp}の配信履歴がありません。配信数: 0")
            else:
                print(f"  {yesterday_jp}の配信履歴がありません。配信数: 0")

            print(f"  ✓ LINE配信数（{yesterday_jp}）: {delivery_count}")
            self.collected_data["line_delivery"] = delivery_count

            save_session(context, "line")
            return delivery_count

        except Exception as e:
            print(f"  ✗ LINE配信数取得エラー: {e}")
            # エラー時は手動入力を促す
            try:
                val = input("  手動でLINE配信数を入力してください（0の場合はそのままEnter）: ")
                delivery_count = int(val) if val.strip() else 0
                self.collected_data["line_delivery"] = delivery_count
                return delivery_count
            except ValueError:
                self.collected_data["line_delivery"] = 0
                return 0
        finally:
            page.close()
            context.close()

    # ========== 2. Google広告 ==========
    def get_google_ads_data(self) -> dict:
        """Google広告データを概要ページから直接取得（F,G,H列用）"""
        print("\n" + "=" * 50)
        print("STEP 2: Google広告データの取得")
        print("=" * 50)

        context = load_session(self.browser, "google")
        page = context.new_page()
        # Google広告はリソースブロックするとUIが壊れる可能性があるのでブロックしない

        try:
            # Google広告の概要ページにアクセス
            page.goto(GOOGLE_ADS_OVERVIEW_URL, wait_until="domcontentloaded")

            # Googleログインが必要な場合
            if "accounts.google.com" in page.url:
                print("  Googleにログインします...")
                email = os.getenv("GOOGLE_EMAIL", "")
                password = os.getenv("GOOGLE_PASSWORD", "")

                if not email or not password:
                    print("  GOOGLE_EMAIL / GOOGLE_PASSWORD が設定されていません")
                    wait_for_user("手動でGoogleにログインしてください")
                else:
                    try:
                        email_input = page.locator('input[type="email"]')
                        email_input.wait_for(timeout=10000)
                        email_input.fill(email)
                        page.locator(
                            'button:has-text("次へ"), button:has-text("Next")'
                        ).first.click()
                        page.wait_for_load_state("domcontentloaded")

                        pw_input = page.locator('input[type="password"]')
                        pw_input.wait_for(timeout=10000)
                        pw_input.fill(password)
                        page.locator(
                            'button:has-text("次へ"), button:has-text("Next")'
                        ).first.click()
                        page.wait_for_load_state("domcontentloaded")
                    except Exception:
                        wait_for_user("手動でGoogleにログインしてください")

                # 2FA待ち
                try:
                    twofa = page.locator(
                        'text=/2段階認証|本人確認|Verify/'
                    )
                    twofa.wait_for(timeout=5000)
                    wait_for_user("Google 2段階認証を完了してください")
                except Exception:
                    pass

                # 概要ページへの遷移を待つ
                try:
                    page.wait_for_url("**/ads.google.com/**", timeout=30000)
                except Exception:
                    pass

                # 概要ページに再アクセス
                page.goto(
                    GOOGLE_ADS_OVERVIEW_URL, wait_until="domcontentloaded"
                )

            save_session(context, "google")

            # 日付ピッカーで前日を設定
            print("  日付を前日に設定中...")
            try:
                # 日付ピッカーをクリック
                date_picker = page.locator(
                    '[class*="date-picker"], '
                    '[class*="DatePicker"], '
                    'button[aria-label*="期間"], '
                    'button[aria-label*="date"], '
                    '[class*="period-selector"]'
                )
                date_picker.first.wait_for(timeout=15000)
                date_picker.first.click()
                page.wait_for_timeout(1000)

                # カレンダーが表示されたら前日を選択
                yesterday_str = str(YESTERDAY.day)

                # カスタム期間の入力フィールドを探す
                start_input = page.locator(
                    'input[aria-label*="開始"], input[aria-label*="Start"], '
                    'input[placeholder*="開始"]'
                )
                end_input = page.locator(
                    'input[aria-label*="終了"], input[aria-label*="End"], '
                    'input[placeholder*="終了"]'
                )

                if start_input.count() > 0 and end_input.count() > 0:
                    # 入力フィールドがある場合
                    yesterday_formatted = YESTERDAY.strftime("%Y/%m/%d")
                    start_input.first.fill(yesterday_formatted)
                    end_input.first.fill(yesterday_formatted)
                    apply_btn = page.locator(
                        'button:has-text("適用"), button:has-text("Apply")'
                    )
                    apply_btn.first.click()
                else:
                    # カレンダーから直接選択
                    print("  カレンダーUIから日付を選択してください")
                    wait_for_user(
                        f"日付ピッカーで前日（{YESTERDAY.strftime('%Y-%m-%d')}）を"
                        "開始日・終了日の両方に設定し、「適用」をクリックしてください"
                    )

                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(3000)  # データ再読み込み待ち

            except Exception as e:
                print(f"  日付ピッカー操作エラー: {e}")
                wait_for_user(
                    f"手動で日付を前日（{YESTERDAY.strftime('%Y-%m-%d')}）に設定してください"
                )

            # 概要ページからデータを読み取り
            print("  概要ページからデータを読み取り中...")
            page.wait_for_timeout(2000)

            body_text = page.locator("body").inner_text()

            # コンバージョン数を取得
            conversions = 0
            cost_per_conv = 0
            cost = 0

            # テキスト全体からデータを抽出
            # Google広告概要ページのパターン: "コンバージョン" の近くに数値がある
            conv_match = re.search(
                r"コンバージョン[^\d]*?([\d,.]+)", body_text
            )
            if conv_match:
                try:
                    conv_val = conv_match.group(1).replace(",", "")
                    conversions = round(float(conv_val))
                except ValueError:
                    pass

            # コンバージョン単価
            cost_conv_match = re.search(
                r"コンバージョン単価[^\d¥￥]*?[¥￥]?([\d,.万]+)", body_text
            )
            if cost_conv_match:
                cost_per_conv = parse_number(cost_conv_match.group(1))

            # 費用
            cost_match = re.search(
                r"費用[^\d¥￥]*?[¥￥]?([\d,.万]+)", body_text
            )
            if cost_match:
                cost = parse_number(cost_match.group(1))

            # データが取れなかった場合は手動入力
            if conversions == 0 and cost == 0:
                print("  自動取得できませんでした。画面を確認して手動入力してください。")
                print("  概要ページに表示されているデータを入力してください:")
                try:
                    val = input("  コンバージョン数（成約数）: ")
                    conversions = int(val) if val.strip() else 0
                    val = input("  コンバージョン単価（成約単価、整数）: ")
                    cost_per_conv = int(val) if val.strip() else 0
                    val = input("  費用（整数）: ")
                    cost = int(val) if val.strip() else 0
                except ValueError:
                    pass

            print(f"  ✓ Google広告 成約数: {conversions}")
            print(f"  ✓ Google広告 成約単価: {cost_per_conv}")
            print(f"  ✓ Google広告 費用: {cost}")

            self.collected_data["google_conversions"] = conversions
            self.collected_data["google_cost_per_conv"] = cost_per_conv
            self.collected_data["google_cost"] = cost

            save_session(context, "google")
            return {
                "conversions": conversions,
                "cost_per_conv": cost_per_conv,
                "cost": cost,
            }

        except Exception as e:
            print(f"  ✗ Google広告データ取得エラー: {e}")
            print("  手動入力に切り替えます:")
            try:
                val = input("  コンバージョン数（成約数）: ")
                conversions = int(val) if val.strip() else 0
                val = input("  コンバージョン単価（整数）: ")
                cost_per_conv = int(val) if val.strip() else 0
                val = input("  費用（整数）: ")
                cost = int(val) if val.strip() else 0
            except ValueError:
                conversions = cost_per_conv = cost = 0

            self.collected_data["google_conversions"] = conversions
            self.collected_data["google_cost_per_conv"] = cost_per_conv
            self.collected_data["google_cost"] = cost
            return {
                "conversions": conversions,
                "cost_per_conv": cost_per_conv,
                "cost": cost,
            }
        finally:
            page.close()
            context.close()

    # ========== 3. Yahoo広告 ==========
    def get_yahoo_ads_data(self) -> dict:
        """Yahoo広告データを取得（I,J,K列用）"""
        print("\n" + "=" * 50)
        print("STEP 3: Yahoo広告データの取得")
        print("=" * 50)

        context = load_session(self.browser, "yahoo")
        page = context.new_page()

        try:
            page.goto(
                "https://ads.yahoo.co.jp/", wait_until="domcontentloaded"
            )

            # ログインが必要な場合
            if "login.yahoo.co.jp" in page.url or page.locator(
                'a:has-text("ログイン")'
            ).count() > 0:
                print("  Yahoo!にログインします...")

                # ログインボタンがある場合はクリック
                login_btn = page.locator('a:has-text("ログイン")')
                if login_btn.count() > 0:
                    login_btn.first.click()
                    page.wait_for_load_state("domcontentloaded")

                email = os.getenv("YAHOO_EMAIL", "")
                password = os.getenv("YAHOO_PASSWORD", "")

                if not email:
                    print("  YAHOO_EMAIL が設定されていません")
                    wait_for_user("手動でYahoo!にログインしてください")
                else:
                    try:
                        # Yahoo! JAPAN IDでログイン
                        email_input = page.locator(
                            'input[name="login"], input[id="username"], '
                            'input[name="username"]'
                        )
                        email_input.first.wait_for(timeout=10000)
                        email_input.first.fill(email)

                        next_btn = page.locator(
                            'button:has-text("次へ"), button[id="btnNext"]'
                        )
                        next_btn.first.click()
                        page.wait_for_load_state("domcontentloaded")

                        # SMS認証 or パスワード入力
                        # SMS認証が表示されるかチェック
                        try:
                            sms_prompt = page.locator(
                                'text=/確認コード|SMS|認証/'
                            )
                            sms_prompt.wait_for(timeout=5000)
                            wait_for_user(
                                "SMSに届いた認証コードを入力してください"
                            )
                        except Exception:
                            # パスワード入力
                            if password:
                                pw_input = page.locator(
                                    'input[name="passwd"], '
                                    'input[type="password"]'
                                )
                                if pw_input.count() > 0:
                                    pw_input.first.fill(password)
                                    login_submit = page.locator(
                                        'button:has-text("ログイン"), '
                                        'button[type="submit"]'
                                    )
                                    login_submit.first.click()
                                    page.wait_for_load_state(
                                        "domcontentloaded"
                                    )
                    except Exception:
                        wait_for_user("手動でYahoo!にログインしてください")

                # ログイン完了を待つ
                try:
                    page.wait_for_url(
                        "**/ads.yahoo.co.jp/**", timeout=30000
                    )
                except Exception:
                    wait_for_user("ログインが完了するまで待ってください")

            save_session(context, "yahoo")

            # アカウント「株式会社ecot」を選択
            try:
                ecot_link = page.locator(
                    'a:has-text("ecot"), '
                    'td:has-text("ecot"), '
                    'span:has-text("ecot")'
                )
                ecot_link.first.wait_for(timeout=10000)
                ecot_link.first.click()
                page.wait_for_load_state("domcontentloaded")
            except Exception:
                print("  アカウント選択ページが表示されない場合、すでに選択済みかもしれません")

            # レポートメニューへ
            print("  レポートを生成中...")
            try:
                report_menu = page.locator(
                    'a:has-text("レポート"), '
                    'button:has-text("レポート"), '
                    '[role="menuitem"]:has-text("レポート")'
                )
                report_menu.first.wait_for(timeout=10000)
                report_menu.first.click()
                page.wait_for_load_state("domcontentloaded")
            except Exception:
                wait_for_user("レポートメニューを開いてください")

            # テンプレート「yahoo KPI」を選択
            try:
                template = page.locator(
                    'text="yahoo KPI", '
                    'a:has-text("yahoo KPI"), '
                    'td:has-text("yahoo KPI")'
                )
                template.first.wait_for(timeout=10000)
                template.first.click()
                page.wait_for_load_state("domcontentloaded")
            except Exception:
                wait_for_user('テンプレート「yahoo KPI」を選択してください')

            # レポートをダウンロード
            csv_path = None
            try:
                with page.expect_download(timeout=30000) as download_info:
                    # ダウンロードボタンを探してクリック
                    dl_btn = page.locator(
                        'button:has-text("ダウンロード"), '
                        'a:has-text("ダウンロード"), '
                        'button:has-text("CSV"), '
                        '[aria-label*="ダウンロード"]'
                    )
                    dl_btn.first.click()

                    # CSV選択が必要な場合
                    try:
                        csv_option = page.locator(
                            'button:has-text("CSV"), '
                            'a:has-text("CSV"), '
                            'li:has-text("CSV")'
                        )
                        csv_option.first.wait_for(timeout=3000)
                        csv_option.first.click()
                    except Exception:
                        pass

                download = download_info.value
                csv_path = (
                    DOWNLOADS_DIR
                    / f"yahoo_ads_{TODAY.strftime('%Y%m%d')}.csv"
                )
                download.save_as(str(csv_path))
                print(f"  CSVダウンロード完了: {csv_path.name}")
            except Exception:
                print("  自動ダウンロードに失敗しました。")
                wait_for_user(
                    "レポートをCSVでダウンロードし、以下のパスに保存してください:\n"
                    f"  {DOWNLOADS_DIR / f'yahoo_ads_{TODAY.strftime(chr(37) + chr(89) + chr(37) + chr(109) + chr(37) + chr(100))}.csv'}"
                )
                csv_path = (
                    DOWNLOADS_DIR
                    / f"yahoo_ads_{TODAY.strftime('%Y%m%d')}.csv"
                )

            # CSVパース
            conversions = 0
            cost_per_conv = 0
            cost = 0

            if csv_path and csv_path.exists():
                print("  CSVを解析中...")
                try:
                    with open(csv_path, "r", encoding="utf-8-sig") as f:
                        reader = csv.reader(f)
                        rows = list(reader)

                    # 前日の行を探す
                    yesterday_str = YESTERDAY.strftime("%Y/%m/%d")
                    yesterday_str2 = YESTERDAY.strftime("%Y-%m-%d")

                    for row in rows:
                        if not row:
                            continue
                        row_text = ",".join(row)
                        if yesterday_str in row_text or yesterday_str2 in row_text:
                            # CSVの列構成: 日付, 成約数, 成約単価, 費用 (想定)
                            try:
                                if len(row) >= 4:
                                    conversions = parse_number(row[1])
                                    cost_per_conv = parse_number(row[2])
                                    cost = parse_number(row[3])
                                elif len(row) >= 2:
                                    # 列構成が異なる場合
                                    for i, cell in enumerate(row):
                                        print(f"    列{i}: {cell}")
                                    print("  列構成を確認して手動入力してください")
                            except (IndexError, ValueError):
                                pass
                            break
                except Exception as e:
                    print(f"  CSV解析エラー: {e}")

            # データが取れなかった場合は手動入力
            if conversions == 0 and cost == 0:
                print("  CSVからデータを自動抽出できませんでした。")
                print("  ダウンロードしたCSVの内容を確認して入力してください:")
                try:
                    val = input("  成約数: ")
                    conversions = int(val) if val.strip() else 0
                    val = input("  成約単価（整数、四捨五入）: ")
                    cost_per_conv = int(val) if val.strip() else 0
                    val = input("  費用（整数）: ")
                    cost = int(val) if val.strip() else 0
                except ValueError:
                    pass

            print(f"  ✓ Yahoo広告 成約数: {conversions}")
            print(f"  ✓ Yahoo広告 成約単価: {cost_per_conv}")
            print(f"  ✓ Yahoo広告 費用: {cost}")

            self.collected_data["yahoo_conversions"] = conversions
            self.collected_data["yahoo_cost_per_conv"] = cost_per_conv
            self.collected_data["yahoo_cost"] = cost

            save_session(context, "yahoo")
            return {
                "conversions": conversions,
                "cost_per_conv": cost_per_conv,
                "cost": cost,
            }

        except Exception as e:
            print(f"  ✗ Yahoo広告データ取得エラー: {e}")
            print("  手動入力に切り替えます:")
            try:
                val = input("  成約数: ")
                conversions = int(val) if val.strip() else 0
                val = input("  成約単価（整数）: ")
                cost_per_conv = int(val) if val.strip() else 0
                val = input("  費用（整数）: ")
                cost = int(val) if val.strip() else 0
            except ValueError:
                conversions = cost_per_conv = cost = 0

            self.collected_data["yahoo_conversions"] = conversions
            self.collected_data["yahoo_cost_per_conv"] = cost_per_conv
            self.collected_data["yahoo_cost"] = cost
            return {
                "conversions": conversions,
                "cost_per_conv": cost_per_conv,
                "cost": cost,
            }
        finally:
            page.close()
            context.close()

    # ========== 4. LINE友達数・リーチ ==========
    def get_line_friends_data(self) -> tuple[int, int]:
        """LINE友達数とターゲットリーチを取得（R,S列用）"""
        print("\n" + "=" * 50)
        print("STEP 4: LINE友達数・ターゲットリーチの取得")
        print("=" * 50)

        context = load_session(self.browser, "line")
        page = context.new_page()
        block_resources(page)

        try:
            # LINE Official Account Manager のホームへ
            page.goto(
                "https://manager.line.biz/account/@906dpbsc",
                wait_until="domcontentloaded",
            )

            # ログインが必要な場合（セッション切れ）
            if "login" in page.url.lower() or "account.line.biz" in page.url:
                print("  LINEセッションが切れています。再ログインが必要です。")
                wait_for_user("LINEにログインしてください")
                page.goto(
                    "https://manager.line.biz/account/@906dpbsc",
                    wait_until="domcontentloaded",
                )

            # ホームページの「友だち」セクションからデータを取得
            # テーブルの読み込みを待つ
            page.wait_for_timeout(3000)

            yesterday_jp = fmt_date_japanese(YESTERDAY)
            friends_count = 0
            reach_count = 0

            # ホームのダッシュボードからテーブルを探す
            try:
                # テーブルが表示されるまで待つ
                page.wait_for_selector("table", timeout=10000)
                rows = page.locator("table tbody tr").all()

                for row in rows:
                    text = row.inner_text()
                    if yesterday_jp in text or fmt_date_short(YESTERDAY) in text:
                        cells = row.locator("td").all()
                        if len(cells) >= 3:
                            friends_count = parse_number(
                                cells[1].inner_text()
                            )
                            reach_count = parse_number(
                                cells[2].inner_text()
                            )
                        break
            except Exception:
                pass

            # テーブルからデータが取れなかった場合、ページ全体から探す
            if friends_count == 0 and reach_count == 0:
                body_text = page.locator("body").inner_text()
                # 「友だち追加」「ターゲットリーチ」のラベル付近の数値を探す
                friends_match = re.search(
                    r"友だち追加[^\d]*?([\d,]+)", body_text
                )
                reach_match = re.search(
                    r"ターゲットリーチ[^\d]*?([\d,]+)", body_text
                )
                if friends_match:
                    friends_count = int(
                        friends_match.group(1).replace(",", "")
                    )
                if reach_match:
                    reach_count = int(
                        reach_match.group(1).replace(",", "")
                    )

            # それでも取れなかった場合は手動入力
            if friends_count == 0 and reach_count == 0:
                print("  自動取得できませんでした。画面を確認して入力してください:")
                try:
                    val = input("  友だち追加（累計）: ")
                    friends_count = int(val) if val.strip() else 0
                    val = input("  ターゲットリーチ（累計）: ")
                    reach_count = int(val) if val.strip() else 0
                except ValueError:
                    pass

            print(f"  ✓ LINE友だち追加: {friends_count}")
            print(f"  ✓ LINEターゲットリーチ: {reach_count}")

            self.collected_data["line_friends"] = friends_count
            self.collected_data["line_reach"] = reach_count

            save_session(context, "line")
            return friends_count, reach_count

        except Exception as e:
            print(f"  ✗ LINE友達数取得エラー: {e}")
            try:
                val = input("  友だち追加（累計）: ")
                friends_count = int(val) if val.strip() else 0
                val = input("  ターゲットリーチ（累計）: ")
                reach_count = int(val) if val.strip() else 0
            except ValueError:
                friends_count = reach_count = 0

            self.collected_data["line_friends"] = friends_count
            self.collected_data["line_reach"] = reach_count
            return friends_count, reach_count
        finally:
            page.close()
            context.close()

    # ========== 5. スプレッドシート入力 ==========
    def _find_row_number(self, page: Page) -> int:
        """スプレッドシートで前日の行番号を特定"""
        print("  前日の行番号を検索中...")

        # 検索用の日付文字列（例: "1/29"）
        search_date = fmt_date_short(YESTERDAY)
        # スプレッドシートの日付形式（例: "26/01/29"）
        search_date_full = fmt_date_spreadsheet(YESTERDAY)

        # Ctrl+F で検索ダイアログを開く
        page.keyboard.press("Control+f")
        page.wait_for_timeout(1000)

        # 検索ボックスに日付を入力
        search_input = page.locator(
            'input[aria-label*="検索"], input[aria-label*="Find"], '
            'input[class*="search"], input[type="text"]'
        ).last
        try:
            search_input.wait_for(timeout=5000)
            search_input.fill(search_date)
            page.keyboard.press("Enter")
            page.wait_for_timeout(1000)
        except Exception:
            print(f"  検索ボックスが見つかりません。")
            wait_for_user(
                f"Ctrl+F で「{search_date}」を検索し、正しい年（26/{YESTERDAY.strftime('%m/%d')}）の行を見つけてください"
            )

        # 検索結果から行番号を取得
        # 名前ボックス（セル参照表示）から現在のセル位置を読み取る
        page.keyboard.press("Escape")  # 検索ダイアログを閉じる
        page.wait_for_timeout(500)

        # 名前ボックスの値を取得
        name_box = page.locator(
            'input[aria-label*="名前ボックス"], '
            'input[aria-label*="Name Box"], '
            'input[class*="name-box"], '
            '#cell-input, '
            'input.jfk-textinput'
        )

        row_num = None
        try:
            name_box_value = name_box.first.input_value()
            # "A1151" → 1151
            match = re.search(r"[A-Z]+(\d+)", name_box_value)
            if match:
                row_num = int(match.group(1))
                print(f"  検索結果のセル: {name_box_value} → 行番号: {row_num}")
        except Exception:
            pass

        # 行番号が特定できなかった場合は手動入力
        if not row_num:
            print(
                f"  行番号を自動取得できませんでした。"
            )
            print(
                f"  スプレッドシートで前日（{search_date_full}）の行を確認してください。"
            )
            val = input("  行番号を入力してください（例: 1151）: ")
            try:
                row_num = int(val.strip())
            except ValueError:
                print("  無効な行番号です。中断します。")
                raise ValueError("行番号が特定できません")

        return row_num

    def _input_cell(self, page: Page, cell_ref: str, value: int):
        """名前ボックスを使ってセルに値を入力"""
        # 名前ボックスをクリックして選択
        name_box = page.locator(
            'input[aria-label*="名前ボックス"], '
            'input[aria-label*="Name Box"], '
            'input[class*="name-box"], '
            '#cell-input, '
            'input.jfk-textinput'
        )

        try:
            name_box.first.click()
            page.wait_for_timeout(300)
            # 名前ボックスにセル参照を入力
            name_box.first.fill(cell_ref)
            page.keyboard.press("Enter")
            page.wait_for_timeout(500)

            # 値を入力
            page.keyboard.type(str(value))
            page.keyboard.press("Enter")
            page.wait_for_timeout(300)

            print(f"    {cell_ref} ← {value}")
        except Exception as e:
            print(f"    {cell_ref} 入力エラー: {e}")
            print(f"    手動で {cell_ref} に {value} を入力してください")
            wait_for_user(f"{cell_ref} に {value} を入力してください")

    def input_to_spreadsheet(self):
        """収集したデータをスプレッドシートに入力"""
        print("\n" + "=" * 50)
        print("STEP 5: スプレッドシートへの入力")
        print("=" * 50)

        # 収集データのサマリー表示
        print("\n📊 収集データサマリー:")
        print(f"  対象日: {YESTERDAY.strftime('%Y-%m-%d')} ({fmt_date_japanese(YESTERDAY)})")
        print(f"  B列  LINE配信数:       {self.collected_data['line_delivery']}")
        print(f"  F列  Google 成約数:    {self.collected_data['google_conversions']}")
        print(f"  G列  Google 成約単価:  {self.collected_data['google_cost_per_conv']}")
        print(f"  H列  Google 費用:      {self.collected_data['google_cost']}")
        print(f"  I列  Yahoo 成約数:     {self.collected_data['yahoo_conversions']}")
        print(f"  J列  Yahoo 成約単価:   {self.collected_data['yahoo_cost_per_conv']}")
        print(f"  K列  Yahoo 費用:       {self.collected_data['yahoo_cost']}")
        print(f"  R列  LINE友だち追加:   {self.collected_data['line_friends']}")
        print(f"  S列  LINEリーチ:       {self.collected_data['line_reach']}")

        if self.dry_run:
            print("\n[ドライラン] 実際の入力はスキップしました")
            return

        # 確認
        if not self.auto_confirm:
            confirm = input("\n上記の内容でスプレッドシートに入力しますか？ (y/n): ")
            if confirm.lower() != "y":
                print("入力をキャンセルしました")
                return

        context = load_session(self.browser, "spreadsheet")
        page = context.new_page()
        # スプレッドシートはリソースブロックしない（UIが壊れる）

        try:
            spreadsheet_url = os.getenv("SPREADSHEET_URL", "")
            if not spreadsheet_url:
                spreadsheet_url = (
                    "https://docs.google.com/spreadsheets/d/"
                    "1Gg4Lvvlx25GGk-LdEnr8apUO2Q4e2ZOYovaAlBfV7os/"
                    "edit?pli=1&gid=888185656#gid=888185656"
                )

            page.goto(spreadsheet_url, wait_until="domcontentloaded")

            # Googleログインが必要な場合
            if "accounts.google.com" in page.url:
                print("  Googleにログインが必要です。")
                wait_for_user("Googleにログインしてください")
                page.goto(spreadsheet_url, wait_until="domcontentloaded")

            # スプレッドシートの読み込みを待つ
            page.wait_for_timeout(5000)

            # 「金額KPI」シートタブをクリック
            try:
                kpi_tab = page.locator(
                    'span:has-text("金額KPI"), '
                    'a:has-text("金額KPI"), '
                    '[role="tab"]:has-text("金額KPI")'
                )
                kpi_tab.first.wait_for(timeout=15000)
                kpi_tab.first.click()
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(3000)
            except Exception:
                print("  「金額KPI」タブが見つかりません。")
                wait_for_user("「金額KPI」シートタブを選択してください")

            # 行番号を特定
            row = self._find_row_number(page)
            self.target_row = row
            print(f"\n  対象行: {row}")

            # バックアップ作成
            backup_info = {
                "timestamp": TODAY.strftime("%Y-%m-%d %H:%M:%S"),
                "target_date": YESTERDAY.strftime("%Y-%m-%d"),
                "target_row": row,
                "data": self.collected_data,
            }
            backup_file = (
                BACKUP_DIR
                / f"backup_{TODAY.strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
            print(f"  バックアップ保存: {backup_file.name}")

            # 各セルに入力
            print("\n  セルに値を入力中...")

            # B列: LINE配信数
            if self.collected_data["line_delivery"] is not None:
                self._input_cell(
                    page, f"B{row}", self.collected_data["line_delivery"]
                )

            # F列: Google広告 成約数
            if self.collected_data["google_conversions"] is not None:
                self._input_cell(
                    page, f"F{row}", self.collected_data["google_conversions"]
                )

            # G列: Google広告 成約単価
            if self.collected_data["google_cost_per_conv"] is not None:
                self._input_cell(
                    page,
                    f"G{row}",
                    self.collected_data["google_cost_per_conv"],
                )

            # H列: Google広告 費用
            if self.collected_data["google_cost"] is not None:
                self._input_cell(
                    page, f"H{row}", self.collected_data["google_cost"]
                )

            # I列: Yahoo広告 成約数
            if self.collected_data["yahoo_conversions"] is not None:
                self._input_cell(
                    page, f"I{row}", self.collected_data["yahoo_conversions"]
                )

            # J列: Yahoo広告 成約単価
            if self.collected_data["yahoo_cost_per_conv"] is not None:
                self._input_cell(
                    page,
                    f"J{row}",
                    self.collected_data["yahoo_cost_per_conv"],
                )

            # K列: Yahoo広告 費用
            if self.collected_data["yahoo_cost"] is not None:
                self._input_cell(
                    page, f"K{row}", self.collected_data["yahoo_cost"]
                )

            # R列: LINE友だち追加
            if self.collected_data["line_friends"] is not None:
                self._input_cell(
                    page, f"R{row}", self.collected_data["line_friends"]
                )

            # S列: LINEターゲットリーチ
            if self.collected_data["line_reach"] is not None:
                self._input_cell(
                    page, f"S{row}", self.collected_data["line_reach"]
                )

            # 保存確認（Google Sheetsは自動保存）
            page.wait_for_timeout(2000)
            print("\n  ✓ 全データの入力が完了しました（自動保存済み）")

            save_session(context, "spreadsheet")

        except Exception as e:
            print(f"\n  ✗ スプレッドシート入力エラー: {e}")
            print("  手動でスプレッドシートにデータを入力してください")
            raise
        finally:
            page.close()
            context.close()

    # ========== メイン実行 ==========
    def run(self):
        """全工程を実行"""
        mode_parts = []
        if self.dry_run:
            mode_parts.append("ドライラン")
        if self.auto_confirm:
            mode_parts.append("自動確認")
        mode_str = f"[{', '.join(mode_parts)}] " if mode_parts else ""

        print(f"\n{'=' * 60}")
        print(f"  {mode_str}朝の金額KPI入力自動化（高速版）")
        print(f"  実行日時: {TODAY.strftime('%Y-%m-%d %H:%M')}")
        print(f"  対象日:   {YESTERDAY.strftime('%Y-%m-%d')} ({fmt_date_japanese(YESTERDAY)})")
        print(f"{'=' * 60}")

        if self.dry_run:
            print("\n※ ドライランモード: データ収集のみ行い、スプレッドシートへの入力は行いません")

        try:
            self.start()

            # 1. LINE配信数
            self.get_line_delivery_count()

            # 2. Google広告
            self.get_google_ads_data()

            # 3. Yahoo広告
            self.get_yahoo_ads_data()

            # 4. LINE友達数・リーチ
            self.get_line_friends_data()

            # 5. スプレッドシート入力
            self.input_to_spreadsheet()

            print(f"\n{'=' * 60}")
            print("  ✓ 全工程完了")
            print(f"{'=' * 60}")

        except KeyboardInterrupt:
            print("\n\n中断されました")
            sys.exit(1)
        except Exception as e:
            print(f"\nエラーが発生しました: {e}")
            raise
        finally:
            self.stop()


def main():
    parser = argparse.ArgumentParser(
        description="朝の金額KPI入力自動化（高速版）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="ドライラン（データ収集のみ、入力は行わない）",
    )
    parser.add_argument(
        "--auto-confirm",
        action="store_true",
        help="確認プロンプトをスキップ",
    )

    args = parser.parse_args()

    automation = MorningKPIFast(
        dry_run=args.dry_run,
        auto_confirm=args.auto_confirm,
    )
    automation.run()


if __name__ == "__main__":
    main()
