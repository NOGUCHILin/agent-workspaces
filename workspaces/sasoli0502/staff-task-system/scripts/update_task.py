#!/usr/bin/env python3
"""
タスク更新ツール

使用例:
  # 進行中にする
  uv run python scripts/update_task.py T20251015-001 --status in_progress

  # 完了にする（実績時間も設定）
  uv run python scripts/update_task.py T20251015-001 --status completed --actual 12

  # 担当者変更
  uv run python scripts/update_task.py T20251015-002 --staff 江口

  # 優先度変更
  uv run python scripts/update_task.py T20251015-003 --priority high
"""

import sys
import argparse
from pathlib import Path
from datetime import date, datetime

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from models import DailyTaskList, TaskStatus, TaskPriority


def update_task(
    task_id: str,
    target_date: str = None,
    status: TaskStatus = None,
    staff: str = None,
    priority: TaskPriority = None,
    actual_minutes: int = None,
    notes: str = None
):
    """タスクを更新"""
    # 日付を推定（タスクIDから）
    if not target_date:
        # T20251015-001 → 2025-10-15
        date_part = task_id[1:9]  # 20251015
        target_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"

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

    # タスクを検索
    task = None
    for t in task_list.tasks:
        if t.id == task_id:
            task = t
            break

    if not task:
        print(f"エラー: タスクID {task_id} が見つかりません")
        return False

    print(f"📝 タスク更新: {task_id}")
    print(f"  現在: {task.status.value} | {task.assigned_to or '未割当'}")

    # 更新処理
    changes = []

    if status:
        old_status = task.status
        task.status = status
        changes.append(f"状態: {old_status.value} → {status.value}")

        # 状態変更に伴う自動設定
        if status == TaskStatus.IN_PROGRESS and not task.started_at:
            task.started_at = datetime.now()
            changes.append(f"開始時刻: {task.started_at.strftime('%H:%M')}")

        if status == TaskStatus.COMPLETED:
            if not task.started_at:
                task.started_at = datetime.now()
            task.completed_at = datetime.now()
            changes.append(f"完了時刻: {task.completed_at.strftime('%H:%M')}")

            # 実績時間が未設定なら計算
            if not task.actual_minutes and actual_minutes:
                task.actual_minutes = actual_minutes
                changes.append(f"実績時間: {actual_minutes}分")

    if staff is not None:
        old_staff = task.assigned_to or "未割当"
        task.assigned_to = staff
        changes.append(f"担当: {old_staff} → {staff}")

    if priority:
        old_priority = task.priority
        task.priority = priority
        changes.append(f"優先度: {old_priority.value} → {priority.value}")

    if actual_minutes is not None:
        task.actual_minutes = actual_minutes
        if "実績時間" not in str(changes):
            changes.append(f"実績時間: {actual_minutes}分")

    if notes is not None:
        task.notes = notes
        changes.append(f"備考: {notes[:30]}...")

    if not changes:
        print("  変更なし")
        return True

    # バリデーション＆保存
    try:
        task_list.to_yaml(str(filepath))
        print(f"✅ 更新完了")
        for change in changes:
            print(f"  - {change}")
        return True
    except Exception as e:
        print(f"エラー: タスクの保存に失敗しました")
        print(f"詳細: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="タスク更新")
    parser.add_argument(
        "task_id",
        help="タスクID (例: T20251015-001)"
    )
    parser.add_argument(
        "--date",
        help="タスクの日付 (YYYY-MM-DD形式、省略時はタスクIDから推定)"
    )
    parser.add_argument(
        "--status",
        choices=["pending", "in_progress", "completed", "cancelled"],
        help="新しい状態"
    )
    parser.add_argument(
        "--staff",
        help="新しい担当者"
    )
    parser.add_argument(
        "--priority",
        choices=["low", "medium", "high"],
        help="新しい優先度"
    )
    parser.add_argument(
        "--actual",
        type=int,
        help="実績時間（分）"
    )
    parser.add_argument(
        "--notes",
        help="備考"
    )

    args = parser.parse_args()

    # Enum変換
    status = TaskStatus(args.status) if args.status else None
    priority = TaskPriority(args.priority) if args.priority else None

    # タスク更新
    success = update_task(
        task_id=args.task_id,
        target_date=args.date,
        status=status,
        staff=args.staff,
        priority=priority,
        actual_minutes=args.actual,
        notes=args.notes
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
