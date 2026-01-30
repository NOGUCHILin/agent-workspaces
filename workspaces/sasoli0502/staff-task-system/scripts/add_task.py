#!/usr/bin/env python3
"""
タスク追加ツール

使用例:
  uv run python scripts/add_task.py --type 査定 --desc "iPhone 14 Pro" --staff 細谷
  uv run python scripts/add_task.py --type 修理 --desc "画面修理" --staff 雜賀 --priority high
  uv run python scripts/add_task.py --type 検品 --desc "在庫10台" --device BULK-002
"""

import sys
import argparse
from pathlib import Path
from datetime import date, datetime

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from models import DailyTaskList, Task, TaskType, TaskPriority, TaskStatus


def generate_task_id(task_list: DailyTaskList, target_date: str) -> str:
    """新しいタスクIDを生成"""
    date_part = target_date.replace("-", "")
    existing_ids = [t.id for t in task_list.tasks if t.id.startswith(f"T{date_part}")]

    if not existing_ids:
        return f"T{date_part}-001"

    # 最後のIDから番号を抽出
    last_id = sorted(existing_ids)[-1]
    last_num = int(last_id.split("-")[1])
    new_num = last_num + 1

    return f"T{date_part}-{new_num:03d}"


def add_task(
    target_date: str,
    task_type: TaskType,
    description: str,
    staff: str = None,
    device_id: str = None,
    priority: TaskPriority = TaskPriority.MEDIUM,
    estimated_minutes: int = None,
    notes: str = ""
):
    """タスクを追加"""
    filepath = project_root / "tasks" / "active" / f"{target_date}.yaml"

    # ファイル存在チェック
    if not filepath.exists():
        print(f"エラー: {target_date} のタスクファイルが見つかりません")
        return False

    # タスクリスト読み込み
    try:
        task_list = DailyTaskList.from_yaml(str(filepath))
    except Exception as e:
        print(f"エラー: タスクファイルの読み込みに失敗しました: {e}")
        return False

    # デフォルト見積時間（task-types.yamlから取得すべきだが、簡易的に）
    if estimated_minutes is None:
        default_durations = {
            TaskType.SATEI: 15,
            TaskType.KENPIN: 20,
            TaskType.SHUPPIN: 10,
            TaskType.SHURI: 60,
        }
        estimated_minutes = default_durations.get(task_type, 15)

    # 新規タスクID生成
    task_id = generate_task_id(task_list, target_date)

    # 新規タスク作成
    new_task = Task(
        id=task_id,
        type=task_type,
        description=description,
        device_id=device_id,
        assigned_to=staff,
        status=TaskStatus.PENDING,
        priority=priority,
        estimated_minutes=estimated_minutes,
        notes=notes
    )

    # タスクリストに追加
    task_list.tasks.append(new_task)

    # 保存
    try:
        task_list.to_yaml(str(filepath))
        print(f"✅ タスク追加成功")
        print(f"  ID: {task_id}")
        print(f"  種別: {task_type.value}")
        print(f"  内容: {description}")
        print(f"  担当: {staff or '未割当'}")
        print(f"  優先度: {priority.value}")
        return True
    except Exception as e:
        print(f"エラー: タスクの保存に失敗しました: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="タスク追加")
    parser.add_argument(
        "--date",
        default=date.today().strftime("%Y-%m-%d"),
        help="追加先の日付 (YYYY-MM-DD形式、デフォルト: 今日)"
    )
    parser.add_argument(
        "--type",
        required=True,
        choices=["査定", "検品", "出品", "修理"],
        help="タスク種別"
    )
    parser.add_argument(
        "--desc",
        required=True,
        help="タスク内容"
    )
    parser.add_argument(
        "--staff",
        help="担当者名"
    )
    parser.add_argument(
        "--device",
        help="端末管理番号"
    )
    parser.add_argument(
        "--priority",
        default="medium",
        choices=["low", "medium", "high"],
        help="優先度 (デフォルト: medium)"
    )
    parser.add_argument(
        "--minutes",
        type=int,
        help="見積時間（分）"
    )
    parser.add_argument(
        "--notes",
        default="",
        help="備考"
    )

    args = parser.parse_args()

    # Enum変換
    task_type = TaskType(args.type)
    priority = TaskPriority(args.priority)

    # タスク追加
    success = add_task(
        target_date=args.date,
        task_type=task_type,
        description=args.desc,
        staff=args.staff,
        device_id=args.device,
        priority=priority,
        estimated_minutes=args.minutes,
        notes=args.notes
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
