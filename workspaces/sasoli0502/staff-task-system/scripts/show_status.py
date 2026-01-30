#!/usr/bin/env python3
"""
タスク状況表示ツール

使用例:
  uv run python scripts/show_status.py                    # 今日のタスク
  uv run python scripts/show_status.py --date 2025-10-15  # 指定日
  uv run python scripts/show_status.py --staff 細谷       # スタッフ別
"""

import sys
import argparse
from pathlib import Path
from datetime import date, datetime
from typing import List, Dict

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from models import DailyTaskList, Task, TaskStatus


def format_time(dt: datetime) -> str:
    """日時を HH:MM 形式にフォーマット"""
    return dt.strftime("%H:%M") if dt else "-"


def format_duration(minutes: int) -> str:
    """分を時間表記にフォーマット"""
    if minutes is None:
        return "-"
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}時間{mins}分"
    return f"{mins}分"


def print_task(task: Task, show_details: bool = False):
    """タスクを1行で表示"""
    status_icon = {
        TaskStatus.COMPLETED: "✅",
        TaskStatus.IN_PROGRESS: "🔄",
        TaskStatus.PENDING: "⏳",
        TaskStatus.CANCELLED: "❌",
    }

    icon = status_icon.get(task.status, "❓")
    assigned = task.assigned_to or "未割当"

    # 基本情報
    print(f"  {icon} {task.id} | {task.type.value} | {task.description[:30]}")
    print(f"     担当: {assigned} | 優先度: {task.priority.value}", end="")

    # 時間情報
    if task.status == TaskStatus.COMPLETED:
        print(f" | 完了: {format_time(task.completed_at)} ({format_duration(task.actual_minutes)})")
    elif task.status == TaskStatus.IN_PROGRESS:
        print(f" | 開始: {format_time(task.started_at)}")
    else:
        print(f" | 予定: {format_duration(task.estimated_minutes)}")

    # 詳細情報
    if show_details and task.notes:
        print(f"     備考: {task.notes}")


def show_all_tasks(task_list: DailyTaskList, verbose: bool = False):
    """全タスクを表示"""
    metadata = task_list.metadata

    print("\n" + "=" * 70)
    print(f"📅 {metadata['date']} ({metadata.get('weekday', '')})")
    print("=" * 70 + "\n")

    # 統計サマリー
    stats = task_list.statistics
    if stats:
        print("📊 進捗サマリー")
        print(f"  完了: {stats.by_status.get('completed', 0)}件")
        print(f"  進行中: {stats.by_status.get('in_progress', 0)}件")
        print(f"  未着手: {stats.by_status.get('pending', 0)}件")
        print(f"  合計: {len(task_list.tasks)}タスク")

        if stats.total_actual_minutes > 0:
            completion_rate = (stats.total_actual_minutes / stats.total_estimated_minutes * 100)
            print(f"  実績/予定: {format_duration(stats.total_actual_minutes)} / {format_duration(stats.total_estimated_minutes)} ({completion_rate:.0f}%)")
        print()

    # 状態別にタスク表示
    completed = [t for t in task_list.tasks if t.status == TaskStatus.COMPLETED]
    in_progress = [t for t in task_list.tasks if t.status == TaskStatus.IN_PROGRESS]
    pending = [t for t in task_list.tasks if t.status == TaskStatus.PENDING]

    if completed:
        print("✅ 完了済み")
        for task in completed:
            print_task(task, verbose)
        print()

    if in_progress:
        print("🔄 進行中")
        for task in in_progress:
            print_task(task, verbose)
        print()

    if pending:
        print("⏳ 未着手")
        for task in pending:
            print_task(task, verbose)
        print()


def show_staff_tasks(task_list: DailyTaskList, staff_name: str):
    """特定スタッフのタスクを表示"""
    staff_tasks = [t for t in task_list.tasks if t.assigned_to == staff_name]

    if not staff_tasks:
        print(f"\n{staff_name}さんに割り当てられたタスクはありません")
        return

    print("\n" + "=" * 70)
    print(f"👤 {staff_name}さんのタスク ({task_list.metadata['date']})")
    print("=" * 70 + "\n")

    completed = [t for t in staff_tasks if t.status == TaskStatus.COMPLETED]
    in_progress = [t for t in staff_tasks if t.status == TaskStatus.IN_PROGRESS]
    pending = [t for t in staff_tasks if t.status == TaskStatus.PENDING]

    print(f"📊 進捗: 完了 {len(completed)} / 進行中 {len(in_progress)} / 未着手 {len(pending)}\n")

    if completed:
        print("✅ 完了済み")
        for task in completed:
            print_task(task)
        print()

    if in_progress:
        print("🔄 進行中")
        for task in in_progress:
            print_task(task)
        print()

    if pending:
        print("⏳ 未着手")
        for task in pending:
            print_task(task)
        print()


def main():
    parser = argparse.ArgumentParser(description="タスク状況表示")
    parser.add_argument(
        "--date",
        help="表示する日付 (YYYY-MM-DD形式、デフォルト: 今日)"
    )
    parser.add_argument(
        "--staff",
        help="特定スタッフのタスクのみ表示"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="詳細情報を表示"
    )

    args = parser.parse_args()

    # 日付決定
    target_date = args.date if args.date else date.today().strftime("%Y-%m-%d")
    filepath = project_root / "tasks" / "active" / f"{target_date}.yaml"

    # ファイル存在チェック
    if not filepath.exists():
        print(f"エラー: {target_date} のタスクファイルが見つかりません")
        print(f"パス: {filepath}")
        return 1

    # タスクリスト読み込み
    try:
        task_list = DailyTaskList.from_yaml(str(filepath))
    except Exception as e:
        print(f"エラー: タスクファイルの読み込みに失敗しました")
        print(f"詳細: {e}")
        return 1

    # 表示
    if args.staff:
        show_staff_tasks(task_list, args.staff)
    else:
        show_all_tasks(task_list, args.verbose)

    return 0


if __name__ == "__main__":
    sys.exit(main())
