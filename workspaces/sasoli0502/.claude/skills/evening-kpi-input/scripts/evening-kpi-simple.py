#!/usr/bin/env python3
"""
夜の金額KPI入力（簡易版）

Notionからデータ取得 + Slackキット数は手動入力 + スプレッドシート自動入力
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

SKILL_DIR = Path(__file__).parent.parent
AUTH_DIR = SKILL_DIR / "auth"
AUTH_DIR.mkdir(exist_ok=True)

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Gg4Lvvlx25GGk-LdEnr8apUO2Q4e2ZOYovaAlBfV7os/edit?pli=1&gid=888185656#gid=888185656"
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
        return None


def find_row_number(page, target_date):
    """スプレッドシートで対象日付の行番号を検索"""
    print(f"\n[Search] {target_date}の行番号を検索中...")

    try:
        # Ctrl+F で検索
        page.keyboard.press('Control+F')
        page.wait_for_selector('input[aria-label*="検索"]', timeout=5000)

        # 日付フォーマット: 26/01/28
        date_parts = target_date.split('-')
        search_date = f"{date_parts[0][2:]}/{date_parts[1]}/{date_parts[2]}"
        print(f"   検索文字列: {search_date}")

        page.fill('input[aria-label*="検索"]', search_date)
        page.wait_for_timeout(2000)  # 検索結果を待つ

        # アクティブセルから行番号を取得
        # セルの値を直接取得
        active_cell = page.locator('.active-cell').first
        if active_cell.is_visible():
            # data-row属性から行番号を取得
            row_attr = active_cell.get_attribute('data-row')
            if row_attr:
                row_number = str(int(row_attr) + 1)  # 0-indexedを1-indexedに変換
                print(f"[OK] 行番号検出: {row_number}")
                page.keyboard.press('Escape')
                return row_number

        # フォールバック: URL fragmentから取得
        current_url = page.url
        if 'range=' in current_url:
            range_part = current_url.split('range=')[1].split('&')[0]
            row_number = ''.join(filter(str.isdigit, range_part))
            if row_number:
                print(f"[OK] 行番号検出(URL): {row_number}")
                page.keyboard.press('Escape')
                return row_number

        print("[ERROR] 行番号の検出に失敗しました")
        page.keyboard.press('Escape')
        return None

    except Exception as e:
        print(f"[ERROR] 行番号検索失敗: {e}")
        page.keyboard.press('Escape')
        return None


def input_to_cell(page, cell_ref, value):
    """指定セルに値を入力"""
    try:
        # セル参照で直接移動（Ctrl+G または名前ボックス）
        page.keyboard.press('Control+Home')  # A1に移動
        page.wait_for_timeout(500)

        # 名前ボックスを使用
        page.keyboard.press('Control+KeyG')
        page.wait_for_timeout(500)
        page.keyboard.type(cell_ref)
        page.keyboard.press('Enter')
        page.wait_for_timeout(500)

        # 値を入力
        page.keyboard.type(str(value))
        page.keyboard.press('Enter')
        page.wait_for_timeout(300)

        print(f"   {cell_ref}: {value}")
        return True

    except Exception as e:
        print(f"   [ERROR] {cell_ref}への入力失敗: {e}")
        return False


def input_to_spreadsheet(page, row_number, notion_data, kit_count):
    """スプレッドシートに全データを入力"""
    print(f"\n[Input] スプレッドシートに入力中...")

    data_map = {
        'AG': kit_count,
        'AW': notion_data['AW'],
        'AY': notion_data['AY'],
        'BY': notion_data['BY'],
        'CB': notion_data['CB'],
        'CV': notion_data['CV'],
    }

    success = True
    for col, value in data_map.items():
        cell_ref = f"{col}{row_number}"
        if not input_to_cell(page, cell_ref, value):
            success = False

    if success:
        print("[OK] 全データ入力完了")
    else:
        print("[WARNING] 一部のデータ入力に失敗しました")

    return success


def main():
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    else:
        target_date = datetime.now().strftime('%Y-%m-%d')

    print(f"=== 夜の金額KPI入力 ===")
    print(f"対象日付: {target_date}")

    # Step 1: Notionからデータ取得
    notion_data = get_notion_data(target_date)
    if not notion_data:
        print("\n[ERROR] Notionデータの取得に失敗しました")
        return 1

    # Step 2: Slackキット数を手動入力
    print(f"\n[Input Required] Slackからキット数を確認してください")
    print(f"URL: https://app.slack.com/client/T5CF8BCDP/C04LSUMKDCK")
    print(f"検索: in:#roboco ネコポス")
    print(f"日付: {target_date}")
    print(f"")

    while True:
        try:
            kit_count = int(input("キット数を入力してください: "))
            break
        except ValueError:
            print("[ERROR] 数値を入力してください")

    print(f"[OK] キット数: {kit_count}件")

    # Step 3: スプレッドシートに入力
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        state_file = AUTH_DIR / "google_state.json"
        context = browser.new_context(
            storage_state=str(state_file) if state_file.exists() else None
        )

        page = context.new_page()
        block_resources(page)

        page.goto(SPREADSHEET_URL)
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(3000)  # スプレッドシートの読み込みを待つ

        # 行番号を検索
        row_number = find_row_number(page, target_date)
        if not row_number:
            print("\n[ERROR] 行番号の検出に失敗しました")
            print("[Info] 手動で行番号を入力してください")
            row_number = input("行番号: ")

        # データ入力
        success = input_to_spreadsheet(page, row_number, notion_data, kit_count)

        # セッション保存
        context.storage_state(path=str(state_file))

        print("\n[Info] ブラウザを30秒間開いたままにします。確認してください。")
        page.wait_for_timeout(30000)

        browser.close()

    if success:
        print("\n[SUCCESS] KPI入力が完了しました")
        return 0
    else:
        print("\n[WARNING] KPI入力は完了しましたが、一部エラーがありました")
        return 1


if __name__ == "__main__":
    sys.exit(main())
