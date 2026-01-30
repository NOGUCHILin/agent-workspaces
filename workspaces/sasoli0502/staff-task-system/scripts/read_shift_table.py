#!/usr/bin/env python3
"""
シフト表読み込みスクリプト

シフト表を確認して出勤スタッフを入力し、タスク割り振りコマンドを生成する。

使用方法:
    uv run python scripts/read_shift_table.py                    # 今日の出勤者を入力
    uv run python scripts/read_shift_table.py --date 2026-01-21  # 指定日の出勤者を入力
    uv run python scripts/read_shift_table.py --staff "細谷,江口,シャシャ"  # 直接指定

シフト表URL: https://docs.google.com/spreadsheets/d/17j75NtzOjnDDc8ffr2nQzTmw5tU_nLm0h5pGGvIB0OA/edit
"""

import argparse
import os
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# 環境変数読み込み
env_path = Path(__file__).parent.parent.parent / "kpi-automation" / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

# プロジェクトルート
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scripts"))

try:
    from utils import resolve_staff_names, format_staff_name, load_staff_info
except ImportError:
    def resolve_staff_names(names):
        return names
    def format_staff_name(name, include_nickname=False):
        return name
    def load_staff_info():
        return {}


# シフト表の設定
SHIFT_SPREADSHEET_URL = os.getenv(
    "SHIFT_SPREADSHEET_URL",
    "https://docs.google.com/spreadsheets/d/17j75NtzOjnDDc8ffr2nQzTmw5tU_nLm0h5pGGvIB0OA/edit"
)

# 事務所勤務を示すキーワード
OFFICE_KEYWORDS = ["裏", "レ"]
# 店舗勤務を示すキーワード
STORE_KEYWORDS = ["店"]


def get_sheet_name_for_date(target_date: datetime) -> str:
    """日付からシート名を生成"""
    return f"{target_date.year}/{target_date.month}"


def open_shift_spreadsheet(target_date: datetime):
    """シフト表をブラウザで開く"""
    sheet_name = get_sheet_name_for_date(target_date)
    print(f"\n📋 シフト表をブラウザで開きます...")
    print(f"   URL: {SHIFT_SPREADSHEET_URL}")
    print(f"   シート名: {sheet_name}")
    print(f"   確認する日付: {target_date.day}日（{target_date.strftime('%A')}）")
    print()

    try:
        webbrowser.open(SHIFT_SPREADSHEET_URL)
    except Exception as e:
        print(f"ブラウザを開けませんでした: {e}")
        print(f"手動でURLにアクセスしてください: {SHIFT_SPREADSHEET_URL}")


def input_staff_from_shift(target_date: datetime) -> dict:
    """
    シフト表を確認して出勤スタッフを入力

    Returns:
        {
            "date": "2026-01-21",
            "office_staff": ["江口", "佐々木", ...],
            "store_staff": ["島田", ...],
            "all_staff": [...]
        }
    """
    print("=" * 60)
    print("📅 シフト表からの出勤スタッフ入力")
    print("=" * 60)
    print()
    print(f"対象日: {target_date.strftime('%Y-%m-%d')} ({target_date.strftime('%A')})")
    print(f"シート名: {get_sheet_name_for_date(target_date)}")
    print(f"確認する列: {target_date.day}日目（B列=1日、C列=2日...）")
    print()

    # シフト表の見方を説明
    print("📖 シフト表の見方:")
    print(f"   「裏」または「レ」 = 事務所勤務")
    print(f"   「店」 = 店舗勤務")
    print()

    # 利用可能なスタッフ一覧を表示
    try:
        staff_info = load_staff_info()
        print("👥 登録スタッフ一覧:")
        for staff_key in sorted(staff_info.keys()):
            print(f"   • {format_staff_name(staff_key, include_nickname=True)}")
        print()
    except:
        pass

    print("-" * 60)

    # 入力を求める
    print("シフト表を確認して、出勤スタッフを入力してください。")
    print("（カンマ区切りで入力。ニックネームでもOK）")
    print()

    office_input = input("🏢 事務所勤務スタッフ: ").strip()
    store_input = input("🏪 店舗勤務スタッフ（なければ空欄）: ").strip()

    # パース
    office_staff = [s.strip() for s in office_input.split(",") if s.strip()]
    store_staff = [s.strip() for s in store_input.split(",") if s.strip()]

    # 正規化
    try:
        office_staff = resolve_staff_names(office_staff)
        store_staff = resolve_staff_names(store_staff)
    except:
        pass

    return {
        "date": target_date.strftime("%Y-%m-%d"),
        "office_staff": office_staff,
        "store_staff": store_staff,
        "all_staff": office_staff + store_staff,
    }


def print_result(result: dict, show_commands: bool = True):
    """結果を表示"""
    print()
    print("=" * 60)
    print(f"✅ {result['date']} の出勤スタッフ")
    print("=" * 60)
    print()

    if result["office_staff"]:
        try:
            display_names = [format_staff_name(s, include_nickname=True) for s in result["office_staff"]]
        except:
            display_names = result["office_staff"]

        print(f"🏢 事務所勤務 ({len(result['office_staff'])}名):")
        for name in display_names:
            print(f"   • {name}")
    else:
        print("🏢 事務所勤務: なし")

    print()

    if result["store_staff"]:
        print(f"🏪 店舗勤務 ({len(result['store_staff'])}名):")
        for name in result["store_staff"]:
            print(f"   • {name}")

    print()

    if show_commands and result["office_staff"]:
        print("-" * 60)
        print("💡 次のステップ:")
        print()

        # コマンド生成
        staff_list = ",".join(result["office_staff"])

        print("1. 朝の集計を入力:")
        print(f"   uv run python scripts/input_morning_summary.py --satei [査定待ち] --kaifuu [開封待ち]")
        print()
        print("2. タスクを自動割り振り:")
        print(f'   uv run python scripts/suggest_assignments.py --staff "{staff_list}" --auto-create')
        print()
        print("3. 結果を確認:")
        print(f"   uv run python scripts/show_status.py")


def main():
    parser = argparse.ArgumentParser(
        description="シフト表から出勤スタッフを確認してタスク割り振りの準備をする",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
    # シフト表を開いて出勤者を入力
    uv run python scripts/read_shift_table.py

    # 指定日の出勤者を入力
    uv run python scripts/read_shift_table.py --date 2026-01-21

    # スタッフを直接指定（入力スキップ）
    uv run python scripts/read_shift_table.py --staff "細谷,江口,シャシャ"

    # シフト表をブラウザで開くだけ
    uv run python scripts/read_shift_table.py --open

シフト表の見方:
    - 「裏」または「レ」: 事務所勤務（タスク割り振り対象）
    - 「店」: 店舗勤務
"""
    )
    parser.add_argument('--date', help='対象日（YYYY-MM-DD形式、省略時は今日）')
    parser.add_argument('--staff', help='出勤スタッフを直接指定（カンマ区切り、ニックネーム可）')
    parser.add_argument('--open', action='store_true', help='シフト表をブラウザで開くだけ')
    parser.add_argument('--no-commands', action='store_true', help='コマンド表示を省略')

    args = parser.parse_args()

    # 日付パース
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d")
    else:
        target_date = datetime.now()

    # シフト表を開くだけの場合
    if args.open:
        open_shift_spreadsheet(target_date)
        return

    # スタッフが直接指定された場合
    if args.staff:
        staff_list = [s.strip() for s in args.staff.split(",") if s.strip()]
        try:
            staff_list = resolve_staff_names(staff_list)
        except:
            pass

        result = {
            "date": target_date.strftime("%Y-%m-%d"),
            "office_staff": staff_list,
            "store_staff": [],
            "all_staff": staff_list,
        }
        print_result(result, show_commands=not args.no_commands)
        return

    # 対話形式で入力
    open_shift_spreadsheet(target_date)

    print()
    input("シフト表を確認できたら Enter キーを押してください...")
    print()

    result = input_staff_from_shift(target_date)
    print_result(result, show_commands=not args.no_commands)


if __name__ == "__main__":
    main()
