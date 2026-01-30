"""
朝の金額KPI入力自動化スクリプト（高速版・CLI/API対応）

実行モード:
- auto (デフォルト): 環境変数に応じてAPI版/Playwright版を自動選択
- api: API版を強制使用（未設定の場合エラー）
- browser: Playwright版を強制使用（従来動作）

使用方法:
    uv run python scripts/morning_kpi_fast.py              # 通常実行（自動選択）
    uv run python scripts/morning_kpi_fast.py --mode api   # API版で実行
    uv run python scripts/morning_kpi_fast.py --dry-run    # データ収集のみ
    uv run python scripts/morning_kpi_fast.py --setup      # 認証セットアップガイド表示

環境変数(.env):
    # Playwright版（従来）
    LINE_EMAIL, LINE_PASSWORD, GOOGLE_EMAIL, GOOGLE_PASSWORD,
    YAHOO_EMAIL, YAHOO_PASSWORD, SPREADSHEET_URL

    # API版（CLI化）
    LINE_CHANNEL_ACCESS_TOKEN        - LINE Messaging API
    GOOGLE_SERVICE_ACCOUNT_JSON      - Google Sheets サービスアカウント
    SPREADSHEET_KEY                  - スプレッドシートID
    YAHOO_ADS_CLIENT_ID              - Yahoo広告 OAuth
    YAHOO_ADS_CLIENT_SECRET
    YAHOO_ADS_REFRESH_TOKEN
    YAHOO_ADS_ACCOUNT_ID
"""

import argparse
import csv
import io
import json
import os
import platform
import re
import sys
import time as time_module
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

# Playwrightは必要な場合のみインポート
try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# gspreadは必要な場合のみインポート
try:
    import gspread
    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False

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


# ========== APIクライアント群 ==========


class LineAPIClient:
    """LINE Messaging API経由のデータ取得（ブラウザ不要）"""

    BASE_URL = "https://api.line.me/v2/bot"

    def __init__(self, channel_access_token: str):
        self.headers = {"Authorization": f"Bearer {channel_access_token}"}

    def get_delivery_count(self, target_date: datetime) -> int:
        """配信数を取得。データ未準備の場合は -1 を返す"""
        date_str = target_date.strftime("%Y%m%d")
        url = f"{self.BASE_URL}/insight/message/delivery?date={date_str}"
        resp = requests.get(url, headers=self.headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "ready":
            # broadcast + targeting の合計
            return data.get("broadcast", 0) + data.get("targeting", 0)
        return -1  # データ未準備

    def get_followers(self, target_date: datetime) -> tuple[int, int]:
        """友だち追加数とターゲットリーチを取得。未準備の場合は (-1, -1)"""
        date_str = target_date.strftime("%Y%m%d")
        url = f"{self.BASE_URL}/insight/followers?date={date_str}"
        resp = requests.get(url, headers=self.headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "ready":
            return data.get("followers", 0), data.get("targetedReaches", 0)
        return -1, -1


class YahooAdsAPIClient:
    """Yahoo広告REST API経由のデータ取得（ブラウザ不要）"""

    TOKEN_URL = "https://biz-oauth.yahoo.co.jp/oauth/v1/token"
    API_BASE = "https://ads-search.yahooapis.jp/api/v18"
    MCC_ACCOUNT_ID = "1002703435"

    def __init__(self, client_id: str, client_secret: str, refresh_token: str, account_id: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.account_id = int(account_id)
        self.access_token = self._refresh_access_token()

    def _refresh_access_token(self) -> str:
        resp = requests.post(self.TOKEN_URL, data={
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
        }, timeout=30)
        resp.raise_for_status()
        return resp.json()["access_token"]

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "x-z-base-account-id": self.MCC_ACCOUNT_ID,
        }

    def get_report(self, target_date: datetime) -> dict:
        """前日のコンバージョン・単価・費用を取得"""
        date_str = target_date.strftime("%Y%m%d")

        # 1. レポート定義作成
        body = {
            "accountId": self.account_id,
            "operand": [{
                "reportName": f"KPI_{date_str}",
                "reportType": "ACCOUNT",
                "reportDateRangeType": "CUSTOM_DATE",
                "dateRange": {
                    "startDate": date_str,
                    "endDate": date_str,
                },
                "fields": ["CONVERSIONS", "COST_PER_CONV", "COST"],
                "reportDownloadFormat": "CSV",
                "reportDownloadEncode": "UTF8",
            }],
        }
        create_resp = requests.post(
            f"{self.API_BASE}/ReportDefinitionService/add",
            json=body, headers=self._headers(), timeout=30,
        )
        create_resp.raise_for_status()
        create_data = create_resp.json()
        report_id = create_data["rval"]["values"][0]["reportDefinition"]["reportJobId"]

        # 2. ポーリング（完了まで待機）
        for _ in range(30):
            status_resp = requests.post(
                f"{self.API_BASE}/ReportDefinitionService/get",
                json={
                    "accountId": self.account_id,
                    "reportJobIds": [report_id],
                },
                headers=self._headers(), timeout=30,
            )
            status_resp.raise_for_status()
            status = status_resp.json()["rval"]["values"][0]["reportDefinition"]["reportJobStatus"]
            if status == "COMPLETED":
                break
            time_module.sleep(2)
        else:
            raise TimeoutError("Yahoo広告レポート生成がタイムアウトしました")

        # 3. ダウンロード
        dl_resp = requests.post(
            f"{self.API_BASE}/ReportDefinitionService/download",
            json={"accountId": self.account_id, "reportJobId": report_id},
            headers=self._headers(), timeout=30,
        )
        dl_resp.raise_for_status()

        # CSVパース
        reader = csv.reader(io.StringIO(dl_resp.text))
        rows = list(reader)
        # ヘッダー行を探す
        conversions = 0
        cost_per_conv = 0
        cost = 0
        for i, row in enumerate(rows):
            if not row:
                continue
            # ヘッダー行の次がデータ行
            row_joined = ",".join(row).lower()
            if "conversions" in row_joined or "コンバージョン" in row_joined:
                if i + 1 < len(rows):
                    data_row = rows[i + 1]
                    if len(data_row) >= 3:
                        conversions = parse_number(data_row[0])
                        cost_per_conv = parse_number(data_row[1])
                        cost = parse_number(data_row[2])
                break

        return {
            "conversions": conversions,
            "cost_per_conv": cost_per_conv,
            "cost": cost,
        }


class GspreadWriter:
    """gspread経由のスプレッドシート書き込み（ブラウザ不要）"""

    def __init__(self, service_account_path: str, spreadsheet_key: str):
        self.gc = gspread.service_account(filename=service_account_path)
        self.spreadsheet = self.gc.open_by_key(spreadsheet_key)
        self.worksheet = self.spreadsheet.worksheet("金額KPI")
        print("  [Sheets API] スプレッドシートに接続しました")

    def find_row_by_date(self, target_date: datetime) -> int:
        """A列から対象日付の行番号を検索"""
        date_str = fmt_date_spreadsheet(target_date)  # "26/01/29"
        col_a = self.worksheet.col_values(1)  # A列全取得
        for i, val in enumerate(col_a, start=1):
            if date_str in str(val):
                return i
        raise ValueError(f"日付 {date_str} がA列に見つかりません")

    def write_batch(self, cells: dict[str, int]):
        """複数セルを一括更新"""
        cell_list = [{"range": ref, "values": [[val]]} for ref, val in cells.items()]
        self.worksheet.batch_update(cell_list)
        print(f"  [Sheets API] {len(cells)}セルを一括更新しました")

    def write_cell(self, cell_ref: str, value: int):
        """単一セル更新"""
        self.worksheet.update_acell(cell_ref, value)


def print_setup_guide():
    """各APIの認証セットアップガイドを表示"""
    print("""
========================================
 朝のKPI入力 API認証セットアップガイド
========================================

[1/3] Google Sheets (gspread + サービスアカウント) ← 最も効果大
  1. Google Cloud Console (https://console.cloud.google.com) でプロジェクト作成
  2. 「APIとサービス」→「ライブラリ」→ Google Sheets API を有効化
  3. 「認証情報」→「サービスアカウント作成」→ JSONキーをダウンロード
  4. JSONキーを scripts/auth/service_account.json に配置
  5. スプレッドシートにサービスアカウントのメール (xxx@xxx.iam.gserviceaccount.com) を「編集者」で共有
  6. .env に以下を追加:
     GOOGLE_SERVICE_ACCOUNT_JSON=scripts/auth/service_account.json
     SPREADSHEET_KEY=1Gg4Lvvlx25GGk-LdEnr8apUO2Q4e2ZOYovaAlBfV7os

[2/3] LINE Messaging API
  1. LINE Developers Console (https://developers.line.biz) にログイン
  2. プロバイダー → Messaging API チャネルを選択（なければ作成）
  3. 「Messaging API設定」→「チャネルアクセストークン（長期）」を発行
  4. .env に追加: LINE_CHANNEL_ACCESS_TOKEN=xxxxx

[3/3] Yahoo広告 REST API
  1. Yahoo!広告API アプリケーションの登録
     https://ads-developers.yahoo.co.jp/ja/ads-api/startup-guide/
  2. OAuth 2.0 認証フローで refresh_token を取得
  3. .env に以下を追加:
     YAHOO_ADS_CLIENT_ID=xxxxx
     YAHOO_ADS_CLIENT_SECRET=xxxxx
     YAHOO_ADS_REFRESH_TOKEN=xxxxx
     YAHOO_ADS_ACCOUNT_ID=xxxxx

※ Google Ads はDeveloper Token申請が必要（審査に数日〜数週間）のため、当面Playwright版を使用
""")


# ========== Playwrightユーティリティ ==========


def block_resources(page):
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
    print(f"\n[WAIT] {message}")
    try:
        input("  -> 完了したらEnterを押してください: ")
    except EOFError:
        print("  (非対話モード: 自動続行)")


def safe_input(prompt: str, default: str = "") -> str:
    """EOF安全なinput"""
    try:
        return input(prompt)
    except EOFError:
        print(f"  (非対話モード: デフォルト値 '{default}' を使用)")
        return default


# ========== メインクラス ==========


class MorningKPIFast:
    """朝の金額KPI入力自動化（高速版・CLI/API対応）"""

    def __init__(self, dry_run: bool = False, auto_confirm: bool = False, mode: str = "auto"):
        self.dry_run = dry_run
        self.auto_confirm = auto_confirm
        self.mode = mode  # "auto", "api", "browser"
        self.browser = None
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
        self.target_row: int = None

        # APIクライアント初期化
        self.line_api: LineAPIClient = None
        self.yahoo_api: YahooAdsAPIClient = None
        self.gspread_writer: GspreadWriter = None

        # 環境変数に応じてAPIクライアントを初期化
        self._init_api_clients()

    def _init_api_clients(self):
        """環境変数の有無に応じてAPIクライアントを初期化"""
        # LINE Messaging API
        line_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
        if line_token:
            try:
                self.line_api = LineAPIClient(line_token)
                print("  [API] LINE Messaging API: 有効")
            except Exception as e:
                print(f"  [API] LINE Messaging API: 初期化エラー ({e})")
        else:
            print("  [API] LINE Messaging API: 未設定 (LINE_CHANNEL_ACCESS_TOKEN)")

        # Yahoo広告 REST API
        yahoo_id = os.getenv("YAHOO_ADS_CLIENT_ID", "")
        yahoo_secret = os.getenv("YAHOO_ADS_CLIENT_SECRET", "")
        yahoo_token = os.getenv("YAHOO_ADS_REFRESH_TOKEN", "")
        yahoo_account = os.getenv("YAHOO_ADS_ACCOUNT_ID", "")
        if all([yahoo_id, yahoo_secret, yahoo_token, yahoo_account]):
            try:
                self.yahoo_api = YahooAdsAPIClient(yahoo_id, yahoo_secret, yahoo_token, yahoo_account)
                print("  [API] Yahoo広告 REST API: 有効")
            except Exception as e:
                print(f"  [API] Yahoo広告 REST API: 初期化エラー ({e})")
        else:
            print("  [API] Yahoo広告 REST API: 未設定")

        # Google Sheets (gspread)
        sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
        ss_key = os.getenv("SPREADSHEET_KEY", "")
        if sa_json and ss_key and HAS_GSPREAD:
            # 相対パスの場合、SKILL_DIRからの相対に変換
            sa_path = Path(sa_json)
            if not sa_path.is_absolute():
                sa_path = SKILL_DIR / sa_json
            if sa_path.exists():
                try:
                    self.gspread_writer = GspreadWriter(str(sa_path), ss_key)
                    print("  [API] Google Sheets API: 有効")
                except Exception as e:
                    print(f"  [API] Google Sheets API: 初期化エラー ({e})")
            else:
                print(f"  [API] Google Sheets API: JSONキー未配置 ({sa_path})")
        else:
            if not HAS_GSPREAD:
                print("  [API] Google Sheets API: gspreadライブラリ未インストール")
            else:
                print("  [API] Google Sheets API: 未設定 (GOOGLE_SERVICE_ACCOUNT_JSON, SPREADSHEET_KEY)")

    def _use_api(self, service: str) -> bool:
        """指定サービスでAPI版を使うかどうか"""
        if self.mode == "browser":
            return False
        if self.mode == "api":
            return True
        # auto: クライアントが初期化済みならAPI版を使う
        if service == "line":
            return self.line_api is not None
        if service == "yahoo":
            return self.yahoo_api is not None
        if service == "spreadsheet":
            return self.gspread_writer is not None
        return False

    @property
    def needs_browser(self) -> bool:
        """Playwrightが必要かどうか"""
        if self.mode == "browser":
            return True
        # Google Adsは常にPlaywright
        needs = True
        # LINE APIが使えない場合もPlaywright必要
        if not self._use_api("line"):
            needs = True
        # Yahoo APIが使えない場合もPlaywright必要
        if not self._use_api("yahoo"):
            needs = True
        # Sheets APIが使えない場合もPlaywright必要
        if not self._use_api("spreadsheet"):
            needs = True
        return needs

    def start(self):
        """ブラウザ起動（必要な場合のみ）"""
        if not self.needs_browser:
            print("ブラウザ不要（全てAPI経由で処理）")
            return
        if not HAS_PLAYWRIGHT:
            print("[WARNING] Playwrightが未インストールです。API版のみ使用します。")
            return
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

        # API版を試行
        if self._use_api("line"):
            try:
                print("  [API] LINE Messaging API で配信数を取得中...")
                count = self.line_api.get_delivery_count(YESTERDAY)
                if count >= 0:
                    print(f"  [OK] LINE配信数（API）: {count}")
                    self.collected_data["line_delivery"] = count
                    return count
                else:
                    print("  [API] データ未準備（統計反映待ち）→ Playwrightにフォールバック")
            except Exception as e:
                print(f"  [API] LINE APIエラー: {e} → Playwrightにフォールバック")

        if not self.browser:
            print("  [SKIP] ブラウザ未起動のためスキップ")
            self.collected_data["line_delivery"] = 0
            return 0

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
                            'input[name="tpasswd"], '
                            'input[type="password"]:visible, '
                            'input[name="password"]:not([type="hidden"])'
                        )
                        pw_input.first.wait_for(state="visible", timeout=10000)
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

            # メッセージリストに直接アクセス（サイドメニューが折りたたまれている場合対策）
            page.goto(
                "https://manager.line.biz/account/@906dpbsc/message/list",
                wait_until="domcontentloaded",
            )
            page.wait_for_timeout(2000)

            # 「配信済み」タブ（複数のセレクタパターンを試行）
            try:
                delivered_tab = page.locator(
                    'button:has-text("配信済み"), '
                    'a:has-text("配信済み"), '
                    '[role="tab"]:has-text("配信済み"), '
                    'li:has-text("配信済み"), '
                    'div:has-text("配信済み")'
                )
                delivered_tab.first.wait_for(timeout=10000)
                delivered_tab.first.click()
                page.wait_for_load_state("domcontentloaded")
            except Exception:
                # 配信済みタブが見つからない場合、URLに直接パラメータを付ける
                print("  配信済みタブを直接クリックできません。ページ内を検索します...")
                # メッセージリストページのURLにstatusパラメータを追加
                current_url = page.url
                if "?" in current_url:
                    page.goto(current_url + "&status=sent", wait_until="domcontentloaded")
                else:
                    page.goto(current_url + "?status=sent", wait_until="domcontentloaded")
                page.wait_for_timeout(2000)

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

            print(f"  [OK] LINE配信数（{yesterday_jp}）: {delivery_count}")
            self.collected_data["line_delivery"] = delivery_count

            save_session(context, "line")
            return delivery_count

        except Exception as e:
            print(f"  [NG] LINE配信数取得エラー: {e}")
            # エラー時は手動入力を促す
            try:
                val = safe_input("  手動でLINE配信数を入力してください（0の場合はそのままEnter）: ", "0")
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
                    val = safe_input("  コンバージョン数（成約数）: ")
                    conversions = int(val) if val.strip() else 0
                    val = safe_input("  コンバージョン単価（成約単価、整数）: ")
                    cost_per_conv = int(val) if val.strip() else 0
                    val = safe_input("  費用（整数）: ")
                    cost = int(val) if val.strip() else 0
                except ValueError:
                    pass

            print(f"  [OK] Google広告 成約数: {conversions}")
            print(f"  [OK] Google広告 成約単価: {cost_per_conv}")
            print(f"  [OK] Google広告 費用: {cost}")

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
            print(f"  [NG] Google広告データ取得エラー: {e}")
            print("  手動入力に切り替えます:")
            try:
                val = safe_input("  コンバージョン数（成約数）: ")
                conversions = int(val) if val.strip() else 0
                val = safe_input("  コンバージョン単価（整数）: ")
                cost_per_conv = int(val) if val.strip() else 0
                val = safe_input("  費用（整数）: ")
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

        # API版を試行
        if self._use_api("yahoo"):
            try:
                print("  [API] Yahoo広告 REST API でデータ取得中...")
                result = self.yahoo_api.get_report(YESTERDAY)
                print(f"  [OK] Yahoo広告 成約数（API）: {result['conversions']}")
                print(f"  [OK] Yahoo広告 成約単価（API）: {result['cost_per_conv']}")
                print(f"  [OK] Yahoo広告 費用（API）: {result['cost']}")
                self.collected_data["yahoo_conversions"] = result["conversions"]
                self.collected_data["yahoo_cost_per_conv"] = result["cost_per_conv"]
                self.collected_data["yahoo_cost"] = result["cost"]
                return result
            except Exception as e:
                print(f"  [API] Yahoo APIエラー: {e} → Playwrightにフォールバック")

        if not self.browser:
            print("  [SKIP] ブラウザ未起動のためスキップ")
            self.collected_data["yahoo_conversions"] = 0
            self.collected_data["yahoo_cost_per_conv"] = 0
            self.collected_data["yahoo_cost"] = 0
            return {"conversions": 0, "cost_per_conv": 0, "cost": 0}

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
                        # Yahoo! JAPAN IDでログイン（SMS認証のみ）
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

                        # SMS認証コードの入力を待つ
                        wait_for_user(
                            "SMSに届いた認証コードをブラウザに入力し、ログインを完了してください"
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
                    val = safe_input("  成約数: ")
                    conversions = int(val) if val.strip() else 0
                    val = safe_input("  成約単価（整数、四捨五入）: ")
                    cost_per_conv = int(val) if val.strip() else 0
                    val = safe_input("  費用（整数）: ")
                    cost = int(val) if val.strip() else 0
                except ValueError:
                    pass

            print(f"  [OK] Yahoo広告 成約数: {conversions}")
            print(f"  [OK] Yahoo広告 成約単価: {cost_per_conv}")
            print(f"  [OK] Yahoo広告 費用: {cost}")

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
            print(f"  [NG] Yahoo広告データ取得エラー: {e}")
            print("  手動入力に切り替えます:")
            try:
                val = safe_input("  成約数: ")
                conversions = int(val) if val.strip() else 0
                val = safe_input("  成約単価（整数）: ")
                cost_per_conv = int(val) if val.strip() else 0
                val = safe_input("  費用（整数）: ")
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

        # API版を試行
        if self._use_api("line"):
            try:
                print("  [API] LINE Messaging API で友だちデータ取得中...")
                friends, reach = self.line_api.get_followers(YESTERDAY)
                if friends >= 0 and reach >= 0:
                    print(f"  [OK] LINE友だち追加（API）: {friends}")
                    print(f"  [OK] LINEターゲットリーチ（API）: {reach}")
                    self.collected_data["line_friends"] = friends
                    self.collected_data["line_reach"] = reach
                    return friends, reach
                else:
                    print("  [API] データ未準備（統計反映待ち）→ Playwrightにフォールバック")
            except Exception as e:
                print(f"  [API] LINE APIエラー: {e} → Playwrightにフォールバック")

        if not self.browser:
            print("  [SKIP] ブラウザ未起動のためスキップ")
            self.collected_data["line_friends"] = 0
            self.collected_data["line_reach"] = 0
            return 0, 0

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

            friends_count = 0
            reach_count = 0

            # ホームのダッシュボードの「友だち」テーブルからデータを取得
            # テーブル構造: ヘッダー行に日付列、データ行に項目名（友だち追加、ターゲットリーチ等）
            # 例: 項目 | 01/23 | 01/29 | 増減
            #     友だち追加 | 168,571 | 169,173 | +602
            #     ターゲットリーチ | 82,418 | 82,674 | +256
            try:
                page.wait_for_selector("table", timeout=10000)
                tables = page.locator("table").all()

                for table in tables:
                    table_text = table.inner_text()
                    if "友だち追加" not in table_text:
                        continue

                    # ヘッダーから最新日付の列インデックスを特定
                    headers = table.locator("th").all()
                    # 最新日付列 = 増減の1つ前の列（通常、右から2番目のデータ列）
                    # ヘッダー: [項目, 旧日付, 新日付, 増減]
                    # 新日付列のインデックスは headers.length - 2
                    target_col_idx = len(headers) - 2  # 増減の前 = 最新日付列
                    print(f"  テーブルヘッダー数: {len(headers)}, 対象列index: {target_col_idx}")
                    if target_col_idx >= 1:
                        header_text = headers[target_col_idx].inner_text().strip()
                        print(f"  対象列ヘッダー: {header_text}")

                    # データ行を読み取り
                    data_rows = table.locator("tbody tr").all()
                    for row in data_rows:
                        row_text = row.inner_text()
                        cells = row.locator("td").all()
                        if len(cells) < target_col_idx + 1:
                            continue

                        if "友だち追加" in row_text:
                            friends_count = parse_number(
                                cells[target_col_idx].inner_text()
                            )
                            print(f"  友だち追加（列{target_col_idx}）: {friends_count}")
                        elif "ターゲットリーチ" in row_text:
                            reach_count = parse_number(
                                cells[target_col_idx].inner_text()
                            )
                            print(f"  ターゲットリーチ（列{target_col_idx}）: {reach_count}")

                    if friends_count > 0 or reach_count > 0:
                        break
            except Exception as e:
                print(f"  テーブル解析エラー: {e}")

            # それでも取れなかった場合は手動入力
            if friends_count == 0 and reach_count == 0:
                print("  自動取得できませんでした。画面を確認して入力してください:")
                try:
                    val = safe_input("  友だち追加（累計）: ")
                    friends_count = int(val) if val.strip() else 0
                    val = safe_input("  ターゲットリーチ（累計）: ")
                    reach_count = int(val) if val.strip() else 0
                except ValueError:
                    pass

            print(f"  [OK] LINE友だち追加: {friends_count}")
            print(f"  [OK] LINEターゲットリーチ: {reach_count}")

            self.collected_data["line_friends"] = friends_count
            self.collected_data["line_reach"] = reach_count

            save_session(context, "line")
            return friends_count, reach_count

        except Exception as e:
            print(f"  [NG] LINE友達数取得エラー: {e}")
            try:
                val = safe_input("  友だち追加（累計）: ")
                friends_count = int(val) if val.strip() else 0
                val = safe_input("  ターゲットリーチ（累計）: ")
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
        name_box = page.locator('#t-name-box')

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
            val = safe_input("  行番号を入力してください（例: 1151）: ")
            try:
                row_num = int(val.strip())
            except ValueError:
                print("  無効な行番号です。中断します。")
                raise ValueError("行番号が特定できません")

        return row_num

    def _navigate_to_cell(self, page: Page, cell_ref: str):
        """URLのrangeパラメータでセルに移動（最も確実な方法）"""
        # 現在のURLからベースを取得し、rangeパラメータを付与
        current_url = page.url
        # 既存のrange=やselection=パラメータを除去
        base_url = re.sub(r'[&?](range|selection)=[^&]*', '', current_url)
        separator = '&' if '?' in base_url else '?'
        nav_url = f"{base_url}{separator}range={cell_ref}"
        page.goto(nav_url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

    def _get_name_box(self, page: Page):
        """Google Sheetsの名前ボックス要素を取得"""
        # 最優先: id="t-name-box" (Google Sheets固有のID)
        name_box = page.locator('#t-name-box')
        if name_box.count() > 0:
            return name_box.first

        # 次: class="waffle-name-box"
        name_box = page.locator('input.waffle-name-box')
        if name_box.count() > 0:
            return name_box.first

        # フォールバック: waffle-name-box-container(クラス名)内のinput
        name_box = page.locator('.waffle-name-box-container input')
        if name_box.count() > 0:
            return name_box.first

        raise Exception("名前ボックスが見つかりません")

    def _input_cell(self, page: Page, cell_ref: str, value: int):
        """セルに値を入力"""
        try:
            name_box = self._get_name_box(page)

            # 名前ボックスをクリック
            name_box.click()
            page.wait_for_timeout(300)

            # 全選択してセル参照を入力
            name_box.click(click_count=3)
            page.wait_for_timeout(200)
            name_box.fill(cell_ref)
            page.wait_for_timeout(200)

            # Enterでセルに移動
            page.keyboard.press("Enter")
            page.wait_for_timeout(1500)

            # セルに値を入力
            page.keyboard.type(str(value), delay=50)
            page.wait_for_timeout(300)

            # Tabで確定（Enterだと下に移動してしまう）
            page.keyboard.press("Tab")
            page.wait_for_timeout(800)

            print(f"    {cell_ref} <- {value}")

        except Exception as e:
            print(f"    {cell_ref} 名前ボックス方式エラー: {e}")
            print(f"    方法2: URL rangeパラメータで移動を試みます...")
            try:
                self._navigate_to_cell(page, cell_ref)
                page.keyboard.type(str(value), delay=50)
                page.wait_for_timeout(300)
                page.keyboard.press("Tab")
                page.wait_for_timeout(800)
                print(f"    {cell_ref} <- {value} (URL方式)")
            except Exception as e2:
                print(f"    {cell_ref} 入力エラー: {e2}")
                print(f"    手動で {cell_ref} に {value} を入力してください")
                wait_for_user(f"{cell_ref} に {value} を入力してください")

    def _input_via_gspread(self):
        """gspread API経由でスプレッドシートに入力（ブラウザ不要）"""
        print("\n  [API] gspread でスプレッドシートに入力中...")

        writer = self.gspread_writer

        # 行番号を特定
        if self.target_row:
            row = self.target_row
            print(f"  行番号（事前指定）: {row}")
        else:
            row = writer.find_row_by_date(YESTERDAY)
            self.target_row = row
        print(f"  対象行: {row}")

        # バックアップ作成
        backup_info = {
            "timestamp": TODAY.strftime("%Y-%m-%d %H:%M:%S"),
            "target_date": YESTERDAY.strftime("%Y-%m-%d"),
            "target_row": row,
            "data": self.collected_data,
            "method": "gspread_api",
        }
        backup_file = BACKUP_DIR / f"backup_{TODAY.strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(backup_info, f, ensure_ascii=False, indent=2)
        print(f"  バックアップ保存: {backup_file.name}")

        # 入力するセルを構築
        cells = {}
        if self.collected_data["line_delivery"] is not None:
            cells[f"B{row}"] = self.collected_data["line_delivery"]
        if self.collected_data["google_conversions"] is not None:
            cells[f"F{row}"] = self.collected_data["google_conversions"]
        if self.collected_data["google_cost_per_conv"] is not None:
            cells[f"G{row}"] = self.collected_data["google_cost_per_conv"]
        if self.collected_data["google_cost"] is not None:
            cells[f"H{row}"] = self.collected_data["google_cost"]
        if self.collected_data["yahoo_conversions"] is not None:
            cells[f"I{row}"] = self.collected_data["yahoo_conversions"]
        if self.collected_data["yahoo_cost_per_conv"] is not None:
            cells[f"J{row}"] = self.collected_data["yahoo_cost_per_conv"]
        if self.collected_data["yahoo_cost"] is not None:
            cells[f"K{row}"] = self.collected_data["yahoo_cost"]
        if self.collected_data["line_friends"] is not None:
            cells[f"R{row}"] = self.collected_data["line_friends"]
        if self.collected_data["line_reach"] is not None:
            cells[f"S{row}"] = self.collected_data["line_reach"]

        if not cells:
            print("  入力するデータがありません")
            return

        # バッチ更新
        writer.write_batch(cells)
        for ref, val in cells.items():
            print(f"    {ref} <- {val}")

        print("\n  [OK] 全データの入力が完了しました（gspread API経由）")

    def input_to_spreadsheet(self):
        """収集したデータをスプレッドシートに入力"""
        print("\n" + "=" * 50)
        print("STEP 5: スプレッドシートへの入力")
        print("=" * 50)

        # 収集データのサマリー表示
        print("\n[DATA] 収集データサマリー:")
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
            confirm = safe_input("\n上記の内容でスプレッドシートに入力しますか？ (y/n): ", "y")
            if confirm.lower() != "y":
                print("入力をキャンセルしました")
                return

        # gspread API版を試行
        if self._use_api("spreadsheet"):
            try:
                self._input_via_gspread()
                return
            except Exception as e:
                print(f"  [API] gspreadエラー: {e} → Playwrightにフォールバック")

        if not self.browser:
            print("  [ERROR] ブラウザ未起動かつgspread未設定のため、スプレッドシート入力できません")
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

            # 行番号を特定（--row で事前指定されていればスキップ）
            if self.target_row:
                row = self.target_row
                print(f"  行番号（事前指定）: {row}")
            else:
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
            print("\n  [OK] 全データの入力が完了しました（自動保存済み）")

            save_session(context, "spreadsheet")

        except Exception as e:
            print(f"\n  [NG] スプレッドシート入力エラー: {e}")
            print("  手動でスプレッドシートにデータを入力してください")
            raise
        finally:
            page.close()
            context.close()

    # ========== メイン実行 ==========
    def run(self, skip_steps: list[str] = None):
        """全工程を実行"""
        skip_steps = skip_steps or []

        mode_parts = []
        if self.dry_run:
            mode_parts.append("ドライラン")
        if self.auto_confirm:
            mode_parts.append("自動確認")
        if skip_steps:
            mode_parts.append(f"スキップ: {','.join(skip_steps)}")
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
            if "line_delivery" not in skip_steps and self.collected_data["line_delivery"] is None:
                self.get_line_delivery_count()
            else:
                print(f"\n  [SKIP] LINE配信数 (値: {self.collected_data['line_delivery']})")

            # 2. Google広告
            if "google" not in skip_steps and self.collected_data["google_conversions"] is None:
                self.get_google_ads_data()
            else:
                print(f"\n  [SKIP] Google広告 (値: conv={self.collected_data['google_conversions']}, cpc={self.collected_data['google_cost_per_conv']}, cost={self.collected_data['google_cost']})")

            # 3. Yahoo広告
            if "yahoo" not in skip_steps and self.collected_data["yahoo_conversions"] is None:
                self.get_yahoo_ads_data()
            else:
                print(f"\n  [SKIP] Yahoo広告 (値: conv={self.collected_data['yahoo_conversions']}, cpc={self.collected_data['yahoo_cost_per_conv']}, cost={self.collected_data['yahoo_cost']})")

            # 4. LINE友達数・リーチ
            if "line_friends" not in skip_steps and self.collected_data["line_friends"] is None:
                self.get_line_friends_data()
            else:
                print(f"\n  [SKIP] LINE友達 (値: friends={self.collected_data['line_friends']}, reach={self.collected_data['line_reach']})")

            # 5. スプレッドシート入力
            if "spreadsheet" not in skip_steps:
                self.input_to_spreadsheet()
            else:
                print("\n  [SKIP] スプレッドシート入力")

            print(f"\n{'=' * 60}")
            print("  [OK] 全工程完了")
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
        description="朝の金額KPI入力自動化（高速版・CLI/API対応）"
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
    parser.add_argument(
        "--mode",
        choices=["auto", "api", "browser"],
        default="auto",
        help="実行モード: auto=環境変数に応じて自動選択, api=API強制, browser=Playwright強制",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="各APIの認証セットアップガイドを表示",
    )
    parser.add_argument(
        "--preset",
        type=str,
        metavar="JSON",
        help='事前収集データをJSON文字列で渡す。例: \'{"yahoo_conversions":3,"yahoo_cost_per_conv":5000,"yahoo_cost":15000}\'',
    )
    parser.add_argument(
        "--skip",
        type=str,
        nargs="*",
        metavar="STEP",
        help="スキップするステップ名: line_delivery, google, yahoo, line_friends, spreadsheet",
    )
    parser.add_argument(
        "--row",
        type=int,
        metavar="ROW",
        help="スプレッドシートの対象行番号を直接指定（例: --row 1159）",
    )

    args = parser.parse_args()

    # セットアップガイド表示
    if args.setup:
        print_setup_guide()
        return

    automation = MorningKPIFast(
        dry_run=args.dry_run,
        auto_confirm=args.auto_confirm,
        mode=args.mode,
    )

    # プリセットデータがある場合は事前にセット
    if args.preset:
        preset_data = json.loads(args.preset)
        for key, value in preset_data.items():
            if key in automation.collected_data:
                automation.collected_data[key] = value
                print(f"  [PRESET] {key} = {value}")

    # 行番号が指定されている場合は事前にセット
    if args.row:
        automation.target_row = args.row
        print(f"  [PRESET] target_row = {args.row}")

    automation.run(skip_steps=args.skip or [])


if __name__ == "__main__":
    main()
