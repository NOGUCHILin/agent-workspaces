#!/usr/bin/env python3
"""
朝の集計データ入力スクリプト（非対話式・拡張版）

コマンドライン引数で基準台数を受け取り、自動計算で派生タスク数を算出

使用例:
  uv run python scripts/input_morning_summary.py --satei 50 --kaifuu 30
  uv run python scripts/input_morning_summary.py --satei 50 --kaifuu 30 --date 2025-10-30
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
import yaml

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from models import DailyTaskList, MorningSummary


def input_morning_summary(satei: int, kaifuu: int, target_date: str = None):
    """朝の集計データを入力（非対話式・自動計算版）

    Args:
        satei: 査定待ちの台数
        kaifuu: 開封台数
        target_date: 対象日（省略時は今日）
    """

    print("=" * 60)
    print("📊 朝の集計データ入力（非対話式）")
    print("=" * 60)
    print()

    # 日付確認
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    print(f"📅 対象日: {target_date}")
    print()

    # 自動計算
    shuri = int(satei * 0.5)
    kenpin = int(satei * 0.5)
    shuppin = int(satei * 0.8)
    activate = kaifuu

    print()
    print("=" * 60)
    print("📊 入力内容の確認（自動計算含む）")
    print("=" * 60)
    print()
    print("【入力した基準値】")
    print(f"  査定待ち: {satei}台")
    print(f"  開封: {kaifuu}台")
    print()
    print("【自動計算された派生タスク】")
    print(f"  修理必要: {shuri}台 （査定の50%）")
    print(f"  検品必要: {kenpin}台 （査定の50%）")
    print(f"  出品可能: {shuppin}台 （査定の80%）")
    print(f"  アクティベート: {activate}台 （開封と同数）")
    print()

    # YAMLファイルの読み込み
    task_file = project_root / "tasks" / "active" / f"{target_date}.yaml"

    if task_file.exists():
        with open(task_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    else:
        # 新規ファイル作成
        data = {
            'metadata': {
                'date': target_date,
                'generated_at': datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00"),
                'total_staff': 0,
                'total_tasks': 0
            },
            'tasks': []
        }

    # morning_summaryセクションを追加（Pydanticモデル準拠）
    morning_summary_data = {
        'input_at': datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        'satei_waiting': satei,
        'kaifuu_count': kaifuu,
        'shuri_needed': shuri,
        'kenpin_needed': kenpin,
        'shuppin_ready': shuppin,
        'activate_count': activate
    }

    # バリデーション
    try:
        MorningSummary(**morning_summary_data)
    except Exception as e:
        print(f"❌ データバリデーションエラー: {e}")
        sys.exit(1)

    data['morning_summary'] = morning_summary_data

    # YAMLファイルに保存
    with open(task_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print()
    print("=" * 60)
    print("✅ 朝の集計を保存しました")
    print("=" * 60)
    print()
    print("📊 本日の作業量:")
    print(f"  査定待ち: {satei}台")
    print(f"  修理必要: {shuri}台")
    print(f"  検品必要: {kenpin}台")
    print(f"  出品可能: {shuppin}台")
    print(f"  開封: {kaifuu}台")
    print(f"  アクティベート: {activate}台")
    print()
    print(f"💡 次のステップ: `uv run python scripts/add_scheduled_tasks.py --time 10:00`")
    print(f"   で10時の時間帯タスクを追加できます")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="朝の集計データを入力（非対話式・自動計算版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  uv run python scripts/input_morning_summary.py --satei 50 --kaifuu 30
  uv run python scripts/input_morning_summary.py --satei 50 --kaifuu 30 --date 2025-10-30
"""
    )
    parser.add_argument('--satei', type=int, required=True, help='査定待ちの台数')
    parser.add_argument('--kaifuu', type=int, required=True, help='開封台数')
    parser.add_argument('--date', help='対象日 (YYYY-MM-DD形式、省略時は今日)')

    args = parser.parse_args()

    input_morning_summary(args.satei, args.kaifuu, args.date)


if __name__ == "__main__":
    main()
