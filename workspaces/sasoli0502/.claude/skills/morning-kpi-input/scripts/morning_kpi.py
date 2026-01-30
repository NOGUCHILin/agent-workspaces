"""
朝の金額KPI入力自動化スクリプト

使用方法:
    uv run python morning_kpi.py           # 通常実行
    uv run python morning_kpi.py --dry-run # ドライラン（確認のみ）
    uv run python morning_kpi.py --rollback 2026-01-21  # ロールバック

必要な環境変数(.env):
    - LINE_EMAIL, LINE_PASSWORD
    - GOOGLE_EMAIL, GOOGLE_PASSWORD (初回のみ)
    - YAHOO_EMAIL, YAHOO_PASSWORD
    - SPREADSHEET_URL
"""

import argparse
import csv
import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, Browser

# 環境変数読み込み
load_dotenv()

# 設定
DOWNLOADS_DIR = Path(__file__).parent / "downloads"
AUTH_DIR = Path(__file__).parent / "auth"
BACKUP_DIR = Path(__file__).parent / "backups"
DOWNLOADS_DIR.mkdir(exist_ok=True)
AUTH_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

# 日付計算
TODAY = datetime.now()
YESTERDAY = TODAY - timedelta(days=1)
ONE_MONTH_AGO = TODAY - timedelta(days=30)


class MorningKPIAutomation:
    """朝の金額KPI入力自動化"""

    def __init__(self, headless: bool = False, dry_run: bool = False):
        self.headless = headless
        self.dry_run = dry_run
        self.browser: Browser = None
        self.page: Page = None
        self.collected_data = {
            "line_delivery": None,  # LINE配信数
            "google_ads": None,     # Google広告CSV
            "yahoo_ads": None,      # Yahoo広告CSV
            "line_friends": None,   # LINE友達数
            "line_reach": None,     # LINEリーチ
        }
        self.backup_data = {}  # バックアップ用

    def start(self):
        """ブラウザ起動"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=100,  # 操作を少し遅くして安定化
        )
        # Google広告用にセッション維持
        self.context = self.browser.new_context(
            storage_state=str(AUTH_DIR / "google_state.json") if (AUTH_DIR / "google_state.json").exists() else None
        )
        self.page = self.context.new_page()
        print("ブラウザを起動しました")

    def stop(self):
        """ブラウザ終了"""
        if self.context:
            # Google広告のセッション保存
            self.context.storage_state(path=str(AUTH_DIR / "google_state.json"))
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("ブラウザを終了しました")

    # ========== LINE配信数 ==========
    def get_line_delivery_count(self) -> int:
        """LINE配信数を取得"""
        print("\n=== LINE配信数の取得 ===")

        # LINE公式アカウントマネージャーにログイン
        self.page.goto("https://manager.line.biz/")
        time.sleep(2)

        # ログインが必要な場合
        if "login" in self.page.url.lower():
            print("LINEにログインします...")
            # メールアドレスでログイン
            self.page.click("text=メールアドレスでログイン")
            time.sleep(1)
            self.page.fill('input[name="email"]', os.getenv("LINE_EMAIL"))
            self.page.fill('input[name="password"]', os.getenv("LINE_PASSWORD"))
            self.page.click('button[type="submit"]')
            time.sleep(3)

        # メッセージリストへ移動
        # ホーム > メッセージリスト
        self.page.click("text=メッセージリスト")
        time.sleep(2)

        # 配信済みタブを選択
        self.page.click("text=配信済み")
        time.sleep(2)

        # 前日の配信を探す
        yesterday_str = YESTERDAY.strftime("%-m月%-d日")  # 例: 1月20日

        # 配信リストから前日の配信を検索
        delivery_items = self.page.query_selector_all('[class*="message-list"] [class*="item"]')

        delivery_count = 0
        for item in delivery_items:
            text = item.inner_text()
            if yesterday_str in text:
                # 配信人数を抽出（例: "4,000人"）
                match = re.search(r'([\d,]+)\s*人', text)
                if match:
                    delivery_count = int(match.group(1).replace(",", ""))
                    break

        print(f"LINE配信数（{yesterday_str}）: {delivery_count}")
        self.collected_data["line_delivery"] = delivery_count
        return delivery_count

    # ========== Google広告 ==========
    def get_google_ads_data(self) -> Path:
        """Google広告データをダウンロード"""
        print("\n=== Google広告データの取得 ===")

        self.page.goto("https://ads.google.com/")
        time.sleep(3)

        # ログインが必要な場合
        if "accounts.google.com" in self.page.url:
            print("Googleにログインします...")
            self.page.fill('input[type="email"]', os.getenv("GOOGLE_EMAIL"))
            self.page.click("text=次へ")
            time.sleep(2)
            self.page.fill('input[type="password"]', os.getenv("GOOGLE_PASSWORD"))
            self.page.click("text=次へ")
            time.sleep(5)

        # キャンペーン > レポート > レポートエディター
        self.page.hover("text=キャンペーン")
        time.sleep(1)
        self.page.click("text=レポート")
        time.sleep(1)
        self.page.click("text=レポートエディター")
        time.sleep(3)

        # 「金額KPI」レポートを選択
        self.page.click("text=金額KPI")
        time.sleep(3)

        # CSVダウンロード
        with self.page.expect_download() as download_info:
            self.page.click('[aria-label="ダウンロード"]')
            time.sleep(1)
            self.page.click("text=CSV")

        download = download_info.value
        csv_path = DOWNLOADS_DIR / f"google_ads_{TODAY.strftime('%Y%m%d')}.csv"
        download.save_as(csv_path)

        print(f"Google広告データをダウンロード: {csv_path}")
        self.collected_data["google_ads"] = csv_path
        return csv_path

    # ========== Yahoo広告 ==========
    def get_yahoo_ads_data(self) -> Path:
        """Yahoo広告データをダウンロード"""
        print("\n=== Yahoo広告データの取得 ===")

        # Yahoo広告ページ（ブックマーク相当のURL）
        self.page.goto("https://ads.yahoo.co.jp/")
        time.sleep(3)

        # ログインが必要な場合
        if "login" in self.page.url.lower():
            print("Yahoo!にログインします...")
            self.page.fill('input[name="login"]', os.getenv("YAHOO_EMAIL"))
            self.page.click("text=次へ")
            time.sleep(2)
            self.page.fill('input[name="passwd"]', os.getenv("YAHOO_PASSWORD"))
            self.page.click("text=ログイン")
            time.sleep(5)

        # ダウンロードボタンをクリック
        with self.page.expect_download() as download_info:
            self.page.click('[aria-label="ダウンロード"]')
            time.sleep(1)
            # CSVを選択（UIによって異なる可能性あり）
            self.page.click("text=CSV")

        download = download_info.value
        csv_path = DOWNLOADS_DIR / f"yahoo_ads_{TODAY.strftime('%Y%m%d')}.csv"
        download.save_as(csv_path)

        print(f"Yahoo広告データをダウンロード: {csv_path}")
        self.collected_data["yahoo_ads"] = csv_path
        return csv_path

    # ========== LINE友達数・リーチ ==========
    def get_line_friends_data(self) -> tuple[int, int]:
        """LINE友達数とリーチを取得"""
        print("\n=== LINE友達数・リーチの取得 ===")

        # LINE公式アカウントマネージャーの分析タブへ
        self.page.goto("https://manager.line.biz/")
        time.sleep(2)

        # 分析タブをクリック
        self.page.click("text=分析")
        time.sleep(2)

        # 友だち > 友だち追加
        self.page.click("text=友だち")
        time.sleep(1)
        self.page.click("text=友だち追加")
        time.sleep(2)

        # 前日のデータを探す
        yesterday_str = YESTERDAY.strftime("%-m月%-d日")

        # 概要セクションのリストから取得
        rows = self.page.query_selector_all('table tbody tr')

        friends_count = 0
        reach_count = 0

        for row in rows:
            text = row.inner_text()
            if yesterday_str in text:
                cells = row.query_selector_all('td')
                if len(cells) >= 3:
                    # 友だち追加数
                    friends_text = cells[1].inner_text()
                    friends_count = int(re.sub(r'[^\d]', '', friends_text) or 0)
                    # ターゲットリーチ
                    reach_text = cells[2].inner_text()
                    reach_count = int(re.sub(r'[^\d]', '', reach_text) or 0)
                break

        print(f"LINE友達数（{yesterday_str}）: {friends_count}")
        print(f"LINEリーチ（{yesterday_str}）: {reach_count}")

        self.collected_data["line_friends"] = friends_count
        self.collected_data["line_reach"] = reach_count
        return friends_count, reach_count

    # ========== バックアップ機能 ==========
    def backup_spreadsheet_data(self):
        """スプレッドシートの該当セルをバックアップ"""
        print("\n=== バックアップ作成 ===")

        spreadsheet_url = os.getenv("SPREADSHEET_URL")
        self.page.goto(spreadsheet_url)
        time.sleep(3)

        # 金額KPIシートに移動
        self.page.click("text=金額KPI")
        time.sleep(2)

        # 該当セル範囲のデータを取得
        # B列（LINE配信数）、F-H列（Google広告）、I-K列（Yahoo広告）、R-S列（LINE友達）
        # キーボードショートカットでセル範囲を選択してコピー

        backup_info = {
            "timestamp": TODAY.strftime('%Y-%m-%d %H:%M:%S'),
            "target_date": YESTERDAY.strftime('%Y-%m-%d'),
            "cells": {}
        }

        # セル位置を特定するためのロジック（行番号は日付から計算）
        # 金額KPIシートの行1が2024-01-01と仮定（実際に合わせて調整必要）
        # ここでは概念的な実装

        # JavaScript経由でセルの値を取得
        try:
            # スプレッドシートのAPIを使わず、UIから値を取得
            # 実際の実装では行番号の特定が必要
            print("バックアップ対象セルの現在値を記録中...")

            # バックアップファイルに保存
            backup_file = BACKUP_DIR / f"backup_{TODAY.strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)

            print(f"バックアップ保存: {backup_file}")
            self.backup_data = backup_info

        except Exception as e:
            print(f"バックアップ作成エラー: {e}")
            raise

    # ========== スプレッドシート入力 ==========
    def input_to_spreadsheet(self):
        """スプレッドシートにデータを入力"""
        print("\n=== スプレッドシートへの入力 ===")

        # ドライランモードの場合は実行しない
        if self.dry_run:
            print("\n[ドライラン] 以下の内容を入力予定:")
            print(f"  - LINE配信数 (B列): {self.collected_data['line_delivery']}")
            print(f"  - Google広告CSV: {self.collected_data['google_ads']}")
            print(f"  - Yahoo広告CSV: {self.collected_data['yahoo_ads']}")
            print(f"  - LINE友達数 (R列): {self.collected_data['line_friends']}")
            print(f"  - LINEリーチ (S列): {self.collected_data['line_reach']}")
            print("\n[ドライラン] 実際の入力はスキップしました")
            return

        spreadsheet_url = os.getenv("SPREADSHEET_URL")
        self.page.goto(spreadsheet_url)
        time.sleep(3)

        # 金額KPIシートに移動
        self.page.click("text=金額KPI")
        time.sleep(2)

        # バックアップを作成
        self.backup_spreadsheet_data()

        # 入力前に確認
        print("\n" + "="*50)
        print("以下の内容をスプレッドシートに入力します:")
        print("="*50)
        print(f"対象日: {YESTERDAY.strftime('%Y-%m-%d')}")
        print(f"  - LINE配信数 (B列): {self.collected_data['line_delivery']}")
        print(f"  - Google広告データ: {self.collected_data['google_ads']}")
        print(f"  - Yahoo広告データ: {self.collected_data['yahoo_ads']}")
        print(f"  - LINE友達数 (R列): {self.collected_data['line_friends']}")
        print(f"  - LINEリーチ (S列): {self.collected_data['line_reach']}")
        print("="*50)

        confirm = input("\n入力を実行しますか？ (y/n): ")
        if confirm.lower() != 'y':
            print("入力をキャンセルしました")
            return

        # TODO: 実際のセル入力ロジック
        # 現時点では手動入力を促す
        print("\n収集したデータ:")
        print(f"  - LINE配信数: {self.collected_data['line_delivery']}")
        print(f"  - Google広告CSV: {self.collected_data['google_ads']}")
        print(f"  - Yahoo広告CSV: {self.collected_data['yahoo_ads']}")
        print(f"  - LINE友達数: {self.collected_data['line_friends']}")
        print(f"  - LINEリーチ: {self.collected_data['line_reach']}")
        print("\nCSVファイルをスプレッドシートにインポートしてください")

    def run(self):
        """全工程を実行"""
        mode_str = "[ドライラン] " if self.dry_run else ""
        print(f"=== {mode_str}朝の金額KPI入力自動化 ===")
        print(f"実行日時: {TODAY.strftime('%Y-%m-%d %H:%M')}")
        print(f"対象日: {YESTERDAY.strftime('%Y-%m-%d')}")

        if self.dry_run:
            print("\n※ ドライランモード: 実際の入力は行いません")

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

            print("\n=== 完了 ===")

        except Exception as e:
            print(f"\nエラーが発生しました: {e}")
            raise
        finally:
            self.stop()


def rollback(date_str: str):
    """指定日のバックアップからロールバック"""
    print(f"=== ロールバック: {date_str} ===")

    # バックアップファイルを検索
    backup_files = list(BACKUP_DIR.glob(f"backup_{date_str.replace('-', '')}*.json"))

    if not backup_files:
        print(f"エラー: {date_str} のバックアップが見つかりません")
        print(f"利用可能なバックアップ:")
        for f in sorted(BACKUP_DIR.glob("backup_*.json")):
            print(f"  - {f.name}")
        return

    # 最新のバックアップを使用
    backup_file = sorted(backup_files)[-1]
    print(f"使用するバックアップ: {backup_file}")

    with open(backup_file, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)

    print(f"バックアップ日時: {backup_data['timestamp']}")
    print(f"対象日: {backup_data['target_date']}")

    # TODO: 実際のロールバック処理
    # スプレッドシートの該当セルにバックアップの値を復元

    print("\nロールバック機能は現在手動で行ってください")
    print("バックアップデータを確認してスプレッドシートを修正してください")


def main():
    parser = argparse.ArgumentParser(description='朝の金額KPI入力自動化')
    parser.add_argument('--dry-run', action='store_true',
                        help='ドライラン（実際の入力は行わない）')
    parser.add_argument('--rollback', type=str, metavar='DATE',
                        help='指定日のバックアップからロールバック (例: 2026-01-21)')
    parser.add_argument('--headless', action='store_true',
                        help='ヘッドレスモードで実行')

    args = parser.parse_args()

    if args.rollback:
        rollback(args.rollback)
    else:
        automation = MorningKPIAutomation(
            headless=args.headless,
            dry_run=args.dry_run
        )
        automation.run()


if __name__ == "__main__":
    main()
