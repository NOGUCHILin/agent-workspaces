#!/usr/bin/env python3
"""
夜の金額KPI入力自動化スクリプト

Notion APIとSlack検索から当日のKPIデータを取得し、
Googleスプレッドシートに自動入力する。
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# スキルのベースディレクトリ
SKILL_DIR = Path(__file__).parent.parent
AUTH_DIR = SKILL_DIR / "auth"
AUTH_DIR.mkdir(exist_ok=True)

# スプレッドシート情報
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Gg4Lvvlx25GGk-LdEnr8apUO2Q4e2ZOYovaAlBfV7os/edit?pli=1&gid=888185656#gid=888185656"
SLACK_URL = "https://app.slack.com/client/T5CF8BCDP/C04LSUMKDCK"

# リソースブロック設定
BLOCKED_RESOURCES = ['image', 'stylesheet', 'font', 'media']


def block_resources(page):
    """不要なリソースをブロックして高速化"""
    def handler(route):
        if route.request.resource_type in BLOCKED_RESOURCES:
            route.abort()
        else:
            route.continue_()
    page.route('**/*', handler)


def get_notion_data(target_date):
    """Notion APIから当日のKPIデータを取得"""
    print(f"\n[Notion] {target_date}のデータを取得中...")

    script_path = SKILL_DIR / "scripts" / "test-notion-fetch.js"
    try:
        result = subprocess.run(
            ["node", str(script_path), target_date],
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )

        # JSON出力部分を抽出
        output = result.stdout
        json_start = output.find('{')
        json_end = output.rfind('}') + 1

        if json_start >= 0 and json_end > json_start:
            json_str = output[json_start:json_end]
            data = json.loads(json_str)
            print(f"[OK] Notionデータ取得完了")
            print(f"   到着数(AW): {data['AW']}件")
            print(f"   査定数(AY): {data['AY']}件")
            print(f"   修理数(BY): {data['BY']}件")
            print(f"   出品数BM(CB): {data['CB']}件")
            print(f"   出品数ムスビ(CV): {data['CV']}件")
            return data
        else:
            print("[ERROR] JSON出力が見つかりませんでした")
            return None

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Notionデータ取得失敗: {e}")
        print(f"出力: {e.stdout}")
        print(f"エラー: {e.stderr}")
        return None


def get_slack_kit_count(page, target_date):
    """Slackから当日のキット数を取得"""
    print(f"\n[Slack] Slackから{target_date}のキット数を取得中...")

    try:
        # Slack検索ページへ移動
        page.goto(SLACK_URL)
        page.wait_for_load_state('domcontentloaded')

        # 検索ボックスを探してクリック
        page.wait_for_selector('[data-qa="top_nav_search"]', timeout=10000)
        page.click('[data-qa="top_nav_search"]')

        # 検索クエリを入力
        search_query = "in:#roboco ネコポス"
        page.fill('[data-qa="search_input"]', search_query)
        page.press('[data-qa="search_input"]', 'Enter')

        # 検索結果の読み込みを待つ
        page.wait_for_selector('[data-qa="search_results"]', timeout=10000)

        # 当日の投稿を探してキット数をカウント
        # 日付フォーマット: 1/28 (月/日)
        date_parts = target_date.split('-')
        search_date = f"{int(date_parts[1])}/{int(date_parts[2])}"  # "1/28"

        print(f"   検索日付: {search_date}")

        # 検索結果から当日の「作成済」をカウント
        messages = page.locator('[data-qa="search_result_item"]').all()
        kit_count = 0

        for message in messages:
            message_text = message.inner_text()

            # 当日の投稿かチェック
            if search_date in message_text and 'ネコポス送状作成情報' in message_text:
                # 「作成済」の行数をカウント
                lines = message_text.split('\n')
                for line in lines:
                    if '作成済' in line:
                        kit_count += 1

        print(f"[OK] キット数取得完了: {kit_count}件")
        return kit_count

    except PlaywrightTimeout as e:
        print(f"[ERROR] Slack検索タイムアウト: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Slackデータ取得失敗: {e}")
        return None


def find_row_number(page, target_date):
    """スプレッドシートで対象日付の行番号を検索"""
    print(f"\n[Search] {target_date}の行番号を検索中...")

    try:
        # Ctrl+F で検索
        page.keyboard.press('Control+F')
        page.wait_for_selector('[aria-label="検索"]', timeout=5000)

        # 日付フォーマット: 26/01/28
        date_parts = target_date.split('-')
        search_date = f"{date_parts[0][2:]}/{date_parts[1]}/{date_parts[2]}"

        page.fill('[aria-label="検索"]', search_date)
        page.wait_for_timeout(1000)  # 検索結果を待つ

        # アクティブセルの位置から行番号を取得
        # 名前ボックスのテキストを読む (例: "A1154")
        name_box = page.locator('[aria-label="名前ボックス"]').first
        cell_ref = name_box.input_value()

        # 行番号を抽出 (例: "A1154" -> "1154")
        row_number = ''.join(filter(str.isdigit, cell_ref))

        # 検索ダイアログを閉じる
        page.keyboard.press('Escape')

        print(f"[OK] 行番号検出: {row_number}")
        return row_number

    except Exception as e:
        print(f"[ERROR] 行番号検索失敗: {e}")
        return None


def input_to_cell(page, cell_ref, value):
    """指定セルに値を入力"""
    try:
        # 名前ボックスにセル参照を入力
        name_box = page.locator('[aria-label="名前ボックス"]').first
        name_box.click()
        name_box.fill(cell_ref)
        page.keyboard.press('Enter')

        # 値を入力
        page.wait_for_timeout(500)
        page.keyboard.type(str(value))
        page.keyboard.press('Enter')

        print(f"   {cell_ref}: {value}")
        return True

    except Exception as e:
        print(f"   ❌ {cell_ref}への入力失敗: {e}")
        return False


def input_to_spreadsheet(page, row_number, notion_data, kit_count):
    """スプレッドシートに全データを入力"""
    print(f"\n[Input] スプレッドシートに入力中...")

    # 入力データマッピング
    data_map = {
        'AG': kit_count,        # キット数
        'AW': notion_data['AW'],  # 到着数
        'AY': notion_data['AY'],  # 査定数
        'BY': notion_data['BY'],  # 修理数
        'CB': notion_data['CB'],  # 出品数(BM)
        'CV': notion_data['CV'],  # 出品数(ムスビ)
    }

    success = True
    for col, value in data_map.items():
        cell_ref = f"{col}{row_number}"
        if not input_to_cell(page, cell_ref, value):
            success = False

    if success:
        print("✅ 全データ入力完了")
    else:
        print("⚠️ 一部のデータ入力に失敗しました")

    return success


def main():
    # 引数から日付を取得（デフォルトは今日）
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    else:
        target_date = datetime.now().strftime('%Y-%m-%d')

    print(f"=== 夜の金額KPI入力 ===")
    print(f"対象日付: {target_date}")

    # Step 1: Notionからデータ取得
    notion_data = get_notion_data(target_date)
    if not notion_data:
        print("\n❌ Notionデータの取得に失敗しました")
        return 1

    # Step 2 & 3: Playwrightでブラウザ操作
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        # セッション再利用
        state_file = AUTH_DIR / "google_state.json"
        context = browser.new_context(
            storage_state=str(state_file) if state_file.exists() else None
        )

        page = context.new_page()
        block_resources(page)

        # Step 2: Slackからキット数取得
        page.goto(SLACK_URL)
        page.wait_for_load_state('domcontentloaded')

        kit_count = get_slack_kit_count(page, target_date)
        if kit_count is None:
            print("\n❌ Slackデータの取得に失敗しました")
            browser.close()
            return 1

        # Slackセッション保存
        slack_state_file = AUTH_DIR / "slack_state.json"
        context.storage_state(path=str(slack_state_file))

        # Step 3: スプレッドシートに入力
        page.goto(SPREADSHEET_URL)
        page.wait_for_load_state('domcontentloaded')

        # 行番号を検索
        row_number = find_row_number(page, target_date)
        if not row_number:
            print("\n❌ 行番号の検出に失敗しました")
            browser.close()
            return 1

        # データ入力
        success = input_to_spreadsheet(page, row_number, notion_data, kit_count)

        # Googleセッション保存
        context.storage_state(path=str(state_file))

        browser.close()

    if success:
        print("\n[SUCCESS] KPI入力が完了しました！")
        return 0
    else:
        print("\n[WARNING] KPI入力は完了しましたが、一部エラーがありました")
        return 1


if __name__ == "__main__":
    sys.exit(main())
