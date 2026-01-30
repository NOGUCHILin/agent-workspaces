#!/usr/bin/env python3
"""
古いタスクファイルを自動アーカイブ

指定日数以上前のファイルを tasks/active/ から tasks/archive/YYYY-MM/ へ移動

使い方:
    # 30日以上前をアーカイブ
    python archive_old_tasks.py --days 30

    # dry-run（移動せず確認のみ）
    python archive_old_tasks.py --days 30 --dry-run
"""

import argparse
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import yaml

# パス設定
BASE_DIR = Path(__file__).parent.parent
ACTIVE_DIR = BASE_DIR / "tasks" / "active"
ARCHIVE_DIR = BASE_DIR / "tasks" / "archive"


def get_old_task_files(days: int):
    """指定日数以上前のタスクファイルを取得"""
    cutoff_date = datetime.now() - timedelta(days=days)
    old_files = []

    for task_file in ACTIVE_DIR.glob("*.yaml"):
        if task_file.name == ".gitkeep":
            continue

        # ファイル名から日付を抽出 (YYYY-MM-DD.yaml)
        try:
            file_date_str = task_file.stem  # .yamlを除去
            file_date = datetime.strptime(file_date_str, "%Y-%m-%d")

            if file_date < cutoff_date:
                old_files.append((task_file, file_date))
        except ValueError:
            # 日付形式でないファイルはスキップ
            continue

    return sorted(old_files, key=lambda x: x[1])


def archive_file(task_file: Path, file_date: datetime, dry_run: bool = False):
    """ファイルをアーカイブディレクトリに移動"""
    # アーカイブ先: tasks/archive/YYYY-MM/
    year_month = file_date.strftime("%Y-%m")
    archive_month_dir = ARCHIVE_DIR / year_month

    if not dry_run:
        archive_month_dir.mkdir(parents=True, exist_ok=True)

    dest_file = archive_month_dir / task_file.name

    if dry_run:
        print(f"  [DRY-RUN] {task_file.relative_to(BASE_DIR)} → {dest_file.relative_to(BASE_DIR)}")
    else:
        shutil.move(str(task_file), str(dest_file))
        print(f"  ✅ {task_file.relative_to(BASE_DIR)} → {dest_file.relative_to(BASE_DIR)}")

    return dest_file


def main():
    parser = argparse.ArgumentParser(description="古いタスクファイルを自動アーカイブ")
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="この日数以上前のファイルをアーカイブ（デフォルト: 30日）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際には移動せず、対象ファイルのみ表示"
    )

    args = parser.parse_args()

    print("=" * 70)
    print(f"📦 タスクファイル自動アーカイブ")
    print("=" * 70)
    print()
    print(f"📅 基準日: {args.days}日以上前のファイル")
    print(f"🗓️  カットオフ日: {(datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')}")
    if args.dry_run:
        print("⚠️  モード: DRY-RUN（確認のみ）")
    print()

    # 古いファイルを取得
    old_files = get_old_task_files(args.days)

    if not old_files:
        print("✅ アーカイブ対象のファイルはありません")
        return

    print(f"📂 対象ファイル: {len(old_files)}件")
    print()

    # アーカイブ実行
    archived_count = 0
    for task_file, file_date in old_files:
        archive_file(task_file, file_date, dry_run=args.dry_run)
        archived_count += 1

    print()
    print("=" * 70)
    if args.dry_run:
        print(f"✅ 確認完了: {archived_count}件がアーカイブ対象")
        print()
        print("実際にアーカイブするには --dry-run を外して実行してください")
    else:
        print(f"✅ アーカイブ完了: {archived_count}件")
    print("=" * 70)


if __name__ == "__main__":
    main()
