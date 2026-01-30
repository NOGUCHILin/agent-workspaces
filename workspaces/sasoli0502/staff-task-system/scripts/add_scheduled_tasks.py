#!/usr/bin/env python3
"""
時間帯別タスク追加スクリプト（新規）

指定時間帯のタスクを自動計算で一括追加
10:00, 13:00, 16:00 の3つの時間帯に対応
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
import yaml

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from models import load_task_types, TaskCategory


def calculate_task_count(formula: str, context: dict) -> int:
    """計算式を評価してタスク数を算出

    Args:
        formula: 計算式（例: "satei_waiting * 0.5"）
        context: 変数コンテキスト（morning_summary, afternoon_summariesの値）

    Returns:
        計算結果（整数）
    """
    try:
        # 安全な評価のため、許可された変数のみを使用
        result = eval(formula, {"__builtins__": {}}, context)
        return int(result)
    except Exception as e:
        print(f"❌ 計算式のエラー: {formula}")
        print(f"   {e}")
        return 0


def add_scheduled_tasks(time_slot: str, target_date: str = None):
    """指定時間帯のタスクを追加

    Args:
        time_slot: "10:00" | "13:00" | "16:00"
        target_date: 対象日（省略時は今日）
    """

    print("=" * 60)
    print(f"⏰ 時間帯別タスク追加（{time_slot}）")
    print("=" * 60)
    print()

    # 日付確認
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    print(f"📅 対象日: {target_date}")
    print()

    # YAMLファイルの読み込み
    task_file = project_root / "tasks" / "active" / f"{target_date}.yaml"

    if not task_file.exists():
        print(f"❌ エラー: タスクファイルが見つかりません: {task_file}")
        print(f"   先に `uv run python scripts/input_morning_summary.py` を実行してください")
        sys.exit(1)

    with open(task_file, 'r', encoding='utf-8') as f:
        task_data = yaml.safe_load(f)

    # 集計データの読み込み
    morning_summary = task_data.get('morning_summary', {})
    afternoon_summaries = task_data.get('afternoon_summaries', [])

    # 変数コンテキストの作成
    context = {}
    if morning_summary:
        context.update(morning_summary)

    for afternoon in afternoon_summaries:
        # afternoon_summariesの各項目を追加
        for key, value in afternoon.items():
            if key not in ['time_slot', 'input_at', 'scheduled_addition_time']:
                context[key] = value

    print("📊 利用可能な集計データ:")
    for key, value in context.items():
        if isinstance(value, int):
            print(f"  {key}: {value}")
    print()

    # タスク種別マスタを読み込み
    task_types = load_task_types()

    # 該当時間帯のタスクを抽出
    tasks_to_add = []
    for task_name, config in task_types.items():
        if config.category != TaskCategory.QUANTITY_BASED:
            continue

        if not config.quantity_management:
            continue

        qm = config.quantity_management

        # 時間帯判定
        if qm.available_at == time_slot:
            # タスク数を計算
            if qm.source == "morning_input":
                # 朝の集計から直接取得
                if qm.base_quantity_field and qm.base_quantity_field in context:
                    count = context[qm.base_quantity_field]
                else:
                    print(f"⚠️  {task_name}: 基準フィールド '{qm.base_quantity_field}' が見つかりません")
                    continue

            elif qm.source == "calculated":
                # 計算式で算出
                if qm.formula:
                    count = calculate_task_count(qm.formula, context)
                else:
                    print(f"⚠️  {task_name}: 計算式が定義されていません")
                    continue

            elif qm.source == "afternoon_input":
                # 午後の集計から取得
                if qm.base_quantity_field and qm.base_quantity_field in context:
                    count = context[qm.base_quantity_field]
                else:
                    print(f"⚠️  {task_name}: 基準フィールド '{qm.base_quantity_field}' が見つかりません")
                    continue

            else:
                # manual など
                continue

            if count > 0:
                tasks_to_add.append({
                    'name': task_name,
                    'count': count,
                    'config': config
                })

    if not tasks_to_add:
        print(f"⚠️  {time_slot} に追加するタスクが見つかりませんでした")
        print()
        return

    # 追加内容の確認
    print("=" * 60)
    print("📋 追加予定のタスク")
    print("=" * 60)
    print()

    total_tasks = 0
    for task_info in tasks_to_add:
        print(f"  {task_info['name']}: {task_info['count']}件")
        total_tasks += task_info['count']

    print()
    print(f"  合計: {total_tasks}件")
    print()

    # タスクID生成のための連番取得
    existing_tasks = task_data.get('tasks', [])
    next_seq = len(existing_tasks) + 1

    # タスク追加
    added_count = 0
    for task_info in tasks_to_add:
        task_name = task_info['name']
        count = task_info['count']
        config = task_info['config']

        for i in range(count):
            task_id = f"T{target_date.replace('-', '')}-{next_seq:03d}"
            next_seq += 1

            task = {
                'id': task_id,
                'type': task_name,
                'description': f"{config.display_name} #{i+1}",
                'assigned_to': None,
                'status': 'pending',
                'priority': ['low', 'medium', 'high'][config.priority_base - 1],
                'estimated_minutes': config.default_duration_minutes,
                'actual_minutes': None,
                'started_at': None,
                'completed_at': None,
                'notes': f"{time_slot}に自動追加"
            }

            existing_tasks.append(task)
            added_count += 1

    # メタデータ更新
    task_data['metadata']['total_tasks'] = len(existing_tasks)
    task_data['tasks'] = existing_tasks

    # YAMLファイルに保存
    with open(task_file, 'w', encoding='utf-8') as f:
        yaml.dump(task_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print()
    print("=" * 60)
    print("✅ タスクを追加しました")
    print("=" * 60)
    print()
    print(f"📊 追加したタスク: {added_count}件")
    print(f"📊 合計タスク数: {len(existing_tasks)}件")
    print()
    print(f"💡 次のステップ: `uv run python scripts/show_status.py`")
    print(f"   でタスク一覧を確認できます")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="時間帯別タスク追加",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 10時のタスク追加
  uv run python scripts/add_scheduled_tasks.py --time 10:00

  # 13時のタスク追加
  uv run python scripts/add_scheduled_tasks.py --time 13:00

  # 16時のタスク追加（特定日）
  uv run python scripts/add_scheduled_tasks.py --time 16:00 --date 2025-10-30
"""
    )
    parser.add_argument(
        '--time',
        required=True,
        choices=['10:00', '13:00', '16:00'],
        help='時間帯（10:00, 13:00, または 16:00）'
    )
    parser.add_argument('--date', help='対象日 (YYYY-MM-DD形式、省略時は今日)')

    args = parser.parse_args()

    add_scheduled_tasks(args.time, args.date)


if __name__ == "__main__":
    main()
