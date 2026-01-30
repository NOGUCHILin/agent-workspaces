#!/usr/bin/env python3
"""
午後の集計データ入力スクリプト（非対話式）

時間帯別（13時/14時）にデータをコマンドライン引数で受け取り、派生タスク数を自動計算

使用例:
  uv run python scripts/input_afternoon_summary.py --time 13:00 --hassou-junbi 30
  uv run python scripts/input_afternoon_summary.py --time 14:00 --konpou-kit 25
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
import yaml

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from models import AfternoonSummary


def input_afternoon_summary(time_slot: str, hassou_junbi: int = None, konpou_kit: int = None, target_date: str = None):
    """午後の集計データを入力（非対話式）

    Args:
        time_slot: "13:00" | "14:00"
        hassou_junbi: 発送準備件数（13:00の場合）
        konpou_kit: 梱包キット作成件数（14:00の場合）
        target_date: 対象日（省略時は今日）
    """

    print("=" * 60)
    print(f"📊 午後の集計データ入力（非対話式・{time_slot}）")
    print("=" * 60)
    print()

    # 日付確認
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    print(f"📅 対象日: {target_date}")
    print()

    afternoon_summary_data = {
        'time_slot': time_slot,
        'input_at': datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00")
    }

    if time_slot == "13:00":
        if hassou_junbi is None:
            print("❌ エラー: 13:00の場合、--hassou-junbi が必要です")
            sys.exit(1)

        # 自動計算: 発送梱包作成は発送準備と同数
        hassou_konpou = hassou_junbi

        print("=" * 60)
        print("📊 入力内容（自動計算含む）")
        print("=" * 60)
        print()
        print("【入力した基準値】")
        print(f"  発送準備: {hassou_junbi}件")
        print()
        print("【自動計算された派生タスク】")
        print(f"  送り状作成: {hassou_konpou}件 （発送準備と同数）")
        print()

        afternoon_summary_data['hassou_junbi_count'] = hassou_junbi
        afternoon_summary_data['hassou_konpou_count'] = hassou_konpou

    elif time_slot == "14:00":
        if konpou_kit is None:
            print("❌ エラー: 14:00の場合、--konpou-kit が必要です")
            sys.exit(1)

        print("=" * 60)
        print("📊 入力内容")
        print("=" * 60)
        print()
        print(f"  梱包キット作成: {konpou_kit}件")
        print(f"  ⏰ タスク追加予定時刻: 16:00")
        print()

        afternoon_summary_data['konpou_kit_count'] = konpou_kit
        afternoon_summary_data['scheduled_addition_time'] = "16:00"

    else:
        print(f"❌ エラー: 無効な時間帯です: {time_slot}")
        print("   有効な時間帯: 13:00, 14:00")
        sys.exit(1)

    # YAMLファイルの読み込み
    task_file = project_root / "tasks" / "active" / f"{target_date}.yaml"

    if not task_file.exists():
        print(f"❌ エラー: タスクファイルが見つかりません: {task_file}")
        print(f"   先に `uv run python scripts/input_morning_summary.py` を実行してください")
        sys.exit(1)

    with open(task_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # バリデーション
    try:
        AfternoonSummary(**afternoon_summary_data)
    except Exception as e:
        print(f"❌ データバリデーションエラー: {e}")
        sys.exit(1)

    # afternoon_summariesセクションに追加
    if 'afternoon_summaries' not in data:
        data['afternoon_summaries'] = []

    data['afternoon_summaries'].append(afternoon_summary_data)

    # YAMLファイルに保存
    with open(task_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print()
    print("=" * 60)
    print("✅ 午後の集計を保存しました")
    print("=" * 60)
    print()

    if time_slot == "13:00":
        print(f"💡 次のステップ: `uv run python scripts/add_scheduled_tasks.py --time 13:00`")
        print(f"   で13時の時間帯タスクを追加できます")
    elif time_slot == "14:00":
        print(f"💡 16時になったら: `uv run python scripts/add_scheduled_tasks.py --time 16:00`")
        print(f"   で梱包キット作成タスクを追加できます")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="午後の集計データを入力",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 13時の発送準備データ入力
  uv run python scripts/input_afternoon_summary.py --time 13:00 --hassou-junbi 30

  # 14時の梱包キット作成データ入力
  uv run python scripts/input_afternoon_summary.py --time 14:00 --konpou-kit 25

  # 特定日のデータ入力
  uv run python scripts/input_afternoon_summary.py --time 13:00 --hassou-junbi 30 --date 2025-10-30
"""
    )
    parser.add_argument(
        '--time',
        required=True,
        choices=['13:00', '14:00'],
        help='時間帯（13:00 または 14:00）'
    )
    parser.add_argument('--hassou-junbi', type=int, help='発送準備件数（13:00の場合に必須）')
    parser.add_argument('--konpou-kit', type=int, help='梱包キット作成件数（14:00の場合に必須）')
    parser.add_argument('--date', help='対象日 (YYYY-MM-DD形式、省略時は今日)')

    args = parser.parse_args()

    input_afternoon_summary(
        time_slot=args.time,
        hassou_junbi=args.hassou_junbi,
        konpou_kit=args.konpou_kit,
        target_date=args.date
    )


if __name__ == "__main__":
    main()
