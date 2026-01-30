#!/usr/bin/env python3
"""
定期メンテナンススクリプト

以下を一括実行:
1. 古いタスクファイルのアーカイブ（30日以上前）
2. 古いアーカイブの削除（365日以上前）
3. データ整合性チェック（バリデーション）
4. ディスク使用量レポート

使い方:
    # 通常実行
    python maintenance.py

    # dry-run（確認のみ）
    python maintenance.py --dry-run

    # カスタム設定
    python maintenance.py --archive-days 60 --delete-days 730
"""

import argparse
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import yaml

# パス設定
BASE_DIR = Path(__file__).parent.parent
ACTIVE_DIR = BASE_DIR / "tasks" / "active"
ARCHIVE_DIR = BASE_DIR / "tasks" / "archive"
CONFIG_DIR = BASE_DIR / "config"


def print_header(title: str):
    """セクションヘッダー表示"""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print()


def count_files_and_size(directory: Path):
    """ディレクトリ内のファイル数とサイズを計算"""
    yaml_files = list(directory.rglob("*.yaml"))
    total_size = sum(f.stat().st_size for f in yaml_files if f.is_file())
    return len(yaml_files), total_size


def format_size(bytes_size: int) -> str:
    """バイト数を人間が読みやすい形式に変換"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def archive_old_tasks(days: int, dry_run: bool = False):
    """古いタスクをアーカイブ"""
    print_header(f"📦 タスクアーカイブ（{days}日以上前）")

    cutoff_date = datetime.now() - timedelta(days=days)
    archived_count = 0

    for task_file in ACTIVE_DIR.glob("*.yaml"):
        if task_file.name == ".gitkeep":
            continue

        try:
            file_date = datetime.strptime(task_file.stem, "%Y-%m-%d")
            if file_date < cutoff_date:
                year_month = file_date.strftime("%Y-%m")
                archive_month_dir = ARCHIVE_DIR / year_month

                if not dry_run:
                    archive_month_dir.mkdir(parents=True, exist_ok=True)
                    dest_file = archive_month_dir / task_file.name
                    shutil.move(str(task_file), str(dest_file))
                    print(f"  ✅ {task_file.name} → archive/{year_month}/")
                else:
                    print(f"  [DRY-RUN] {task_file.name} → archive/{year_month}/")

                archived_count += 1
        except ValueError:
            continue

    if archived_count == 0:
        print("  ℹ️  アーカイブ対象のファイルはありません")
    else:
        print(f"\n  📊 合計: {archived_count}件")

    return archived_count


def delete_old_archives(days: int, dry_run: bool = False):
    """古いアーカイブを削除"""
    print_header(f"🗑️  古いアーカイブ削除（{days}日以上前）")

    cutoff_date = datetime.now() - timedelta(days=days)
    deleted_count = 0

    for archive_file in ARCHIVE_DIR.rglob("*.yaml"):
        try:
            file_date = datetime.strptime(archive_file.stem, "%Y-%m-%d")
            if file_date < cutoff_date:
                if not dry_run:
                    archive_file.unlink()
                    print(f"  🗑️  {archive_file.relative_to(ARCHIVE_DIR)}")
                else:
                    print(f"  [DRY-RUN] {archive_file.relative_to(ARCHIVE_DIR)}")

                deleted_count += 1
        except ValueError:
            continue

    # 空のディレクトリを削除
    if not dry_run:
        for month_dir in ARCHIVE_DIR.iterdir():
            if month_dir.is_dir() and not any(month_dir.iterdir()):
                month_dir.rmdir()
                print(f"  📂 空のディレクトリを削除: {month_dir.name}")

    if deleted_count == 0:
        print("  ℹ️  削除対象のファイルはありません")
    else:
        print(f"\n  📊 合計: {deleted_count}件")

    return deleted_count


def validate_data():
    """データ整合性チェック"""
    print_header("✅ データ整合性チェック")

    try:
        result = subprocess.run(
            ["uv", "run", "python", str(BASE_DIR / "scripts" / "validate.py"), "--all"],
            capture_output=True,
            text=True,
            cwd=BASE_DIR
        )

        print(result.stdout)

        if result.returncode == 0:
            print("  ✅ すべてのデータファイルは正常です")
            return True
        else:
            print("  ⚠️  バリデーションエラーが検出されました")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"  ❌ バリデーション実行エラー: {e}")
        return False


def disk_usage_report():
    """ディスク使用量レポート"""
    print_header("💾 ディスク使用量レポート")

    # Active
    active_count, active_size = count_files_and_size(ACTIVE_DIR)
    print(f"  📂 tasks/active/")
    print(f"     ファイル数: {active_count}件")
    print(f"     使用容量: {format_size(active_size)}")
    print()

    # Archive
    archive_count, archive_size = count_files_and_size(ARCHIVE_DIR)
    print(f"  📦 tasks/archive/")
    print(f"     ファイル数: {archive_count}件")
    print(f"     使用容量: {format_size(archive_size)}")
    print()

    # Config
    config_count, config_size = count_files_and_size(CONFIG_DIR)
    print(f"  ⚙️  config/")
    print(f"     ファイル数: {config_count}件")
    print(f"     使用容量: {format_size(config_size)}")
    print()

    # Total
    total_size = active_size + archive_size + config_size
    total_count = active_count + archive_count + config_count
    print(f"  📊 合計")
    print(f"     ファイル数: {total_count}件")
    print(f"     使用容量: {format_size(total_size)}")


def main():
    parser = argparse.ArgumentParser(description="定期メンテナンス実行")
    parser.add_argument(
        "--archive-days",
        type=int,
        default=30,
        help="この日数以上前のファイルをアーカイブ（デフォルト: 30日）"
    )
    parser.add_argument(
        "--delete-days",
        type=int,
        default=365,
        help="この日数以上前のアーカイブを削除（デフォルト: 365日）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際には変更せず、確認のみ"
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="バリデーションをスキップ"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("🛠️  スタッフタスクシステム - 定期メンテナンス")
    print("=" * 70)
    print()
    print(f"📅 実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.dry_run:
        print("⚠️  モード: DRY-RUN（確認のみ）")

    # 1. アーカイブ
    archived = archive_old_tasks(args.archive_days, dry_run=args.dry_run)

    # 2. 削除
    deleted = delete_old_archives(args.delete_days, dry_run=args.dry_run)

    # 3. バリデーション
    if not args.skip_validation and not args.dry_run:
        validation_ok = validate_data()
    else:
        validation_ok = True

    # 4. ディスク使用量
    disk_usage_report()

    # サマリー
    print()
    print("=" * 70)
    print("📊 メンテナンスサマリー")
    print("=" * 70)
    print(f"  📦 アーカイブ: {archived}件")
    print(f"  🗑️  削除: {deleted}件")
    print(f"  ✅ バリデーション: {'OK' if validation_ok else 'NG'}")
    print("=" * 70)
    print()

    if args.dry_run:
        print("ℹ️  実際に実行するには --dry-run を外してください")
    else:
        print("✅ メンテナンス完了")


if __name__ == "__main__":
    main()
