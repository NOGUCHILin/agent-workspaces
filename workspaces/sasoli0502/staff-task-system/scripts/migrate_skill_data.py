#!/usr/bin/env python3
"""
既存のstaff-skills.yamlに処理能力情報を自動計算して追加するマイグレーションスクリプト

新規追加フィールド:
- time_per_task: 1タスクあたりの処理時間（分）
- tasks_per_hour: 1時間あたりの処理数
- tasks_per_day: 1日あたりの処理数（8時間想定）
"""

import yaml
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# プロジェクトルートをパスに追加
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from scripts.models import load_task_types


def backup_file(filepath: Path) -> Path:
    """ファイルをバックアップ"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = filepath.with_suffix(f".yaml.backup.{timestamp}")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return backup_path


def calculate_performance_metrics(
    task_name: str,
    speed_factor: float,
    task_types_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    処理能力指標を計算

    Args:
        task_name: タスク名（査定、修理など）
        speed_factor: 速度係数
        task_types_config: タスク種別設定

    Returns:
        {
            "time_per_task": int,      # 分/件
            "tasks_per_hour": float,   # 件/時
            "tasks_per_day": int       # 件/日（8時間）
        }
    """
    # タスク種別設定から基本所要時間を取得
    if task_name not in task_types_config:
        return {}

    default_duration = task_types_config[task_name].default_duration_minutes

    # time_per_task = 基本所要時間 / 速度係数
    time_per_task = round(default_duration / speed_factor, 1)

    # tasks_per_hour = 60分 / time_per_task
    tasks_per_hour = round(60 / time_per_task, 2)

    # tasks_per_day = tasks_per_hour * 8時間
    tasks_per_day = int(tasks_per_hour * 8)

    return {
        "time_per_task": int(time_per_task) if time_per_task == int(time_per_task) else time_per_task,
        "tasks_per_hour": tasks_per_hour,
        "tasks_per_day": tasks_per_day
    }


def migrate_staff_skills(
    staff_skills_path: Path,
    task_types_path: Path,
    dry_run: bool = False
) -> None:
    """
    staff-skills.yamlに処理能力情報を追加

    Args:
        staff_skills_path: staff-skills.yamlのパス
        task_types_path: task-types.yamlのパス
        dry_run: Trueの場合は変更を保存しない
    """
    print("=" * 60)
    print("スキルデータマイグレーション")
    print("=" * 60)
    print()

    # タスク種別設定を読み込み
    print("📖 タスク種別設定を読み込み中...")
    task_types_config = load_task_types(str(task_types_path))
    print(f"   ✅ {len(task_types_config)}種類のタスク定義を読み込みました")
    print()

    # staff-skills.yamlを読み込み
    print("📖 スタッフスキルデータを読み込み中...")
    with open(staff_skills_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    staff_skills = data.get('staff_skills', {})
    print(f"   ✅ {len(staff_skills)}名のスタッフデータを読み込みました")
    print()

    # 各スタッフの各スキルに新フィールドを追加
    print("🔄 処理能力情報を計算中...")
    updated_count = 0
    skipped_count = 0

    for staff_name, skills in staff_skills.items():
        print(f"\n👤 {staff_name}")

        for skill_name, skill_info in skills.items():
            # 空の辞書（拡張スキル）はスキップ
            if not skill_info:
                continue

            # 既に新フィールドがある場合はスキップ
            if 'time_per_task' in skill_info:
                print(f"   ⏭️  {skill_name}: 既に処理能力情報あり（スキップ）")
                skipped_count += 1
                continue

            # level, speed_factor がない場合はスキップ
            if 'level' not in skill_info or 'speed_factor' not in skill_info:
                print(f"   ⚠️  {skill_name}: level/speed_factor がありません（スキップ）")
                skipped_count += 1
                continue

            speed_factor = skill_info['speed_factor']

            # 処理能力指標を計算
            metrics = calculate_performance_metrics(
                skill_name,
                speed_factor,
                task_types_config
            )

            if metrics:
                # 新フィールドを追加
                skill_info.update(metrics)
                print(f"   ✅ {skill_name}: {metrics['time_per_task']}分/件, {metrics['tasks_per_hour']}件/時, {metrics['tasks_per_day']}件/日")
                updated_count += 1
            else:
                print(f"   ⚠️  {skill_name}: タスク種別設定が見つかりません（スキップ）")
                skipped_count += 1

    print()
    print("=" * 60)
    print(f"📊 処理結果")
    print("=" * 60)
    print(f"   更新: {updated_count}件")
    print(f"   スキップ: {skipped_count}件")
    print()

    # 保存
    if not dry_run:
        # バックアップ作成
        backup_path = backup_file(staff_skills_path)
        print(f"💾 バックアップ作成: {backup_path}")

        # 保存
        with open(staff_skills_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                data,
                f,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False
            )
        print(f"✅ 保存完了: {staff_skills_path}")
    else:
        print("⚠️  dry-run モード: 変更は保存されませんでした")

    print()
    print("=" * 60)
    print("マイグレーション完了")
    print("=" * 60)


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(
        description="staff-skills.yamlに処理能力情報を追加"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="変更を保存せずに確認のみ"
    )
    args = parser.parse_args()

    # パス設定
    config_dir = project_root / 'config'
    staff_skills_path = config_dir / 'staff-skills.yaml'
    task_types_path = config_dir / 'task-types.yaml'

    # ファイル存在確認
    if not staff_skills_path.exists():
        print(f"❌ エラー: {staff_skills_path} が見つかりません")
        sys.exit(1)

    if not task_types_path.exists():
        print(f"❌ エラー: {task_types_path} が見つかりません")
        sys.exit(1)

    # マイグレーション実行
    migrate_staff_skills(staff_skills_path, task_types_path, args.dry_run)


if __name__ == "__main__":
    main()
