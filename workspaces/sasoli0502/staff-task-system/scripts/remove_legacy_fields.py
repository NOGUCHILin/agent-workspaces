#!/usr/bin/env python3
"""
staff-skills.yamlからlevelとspeed_factorを削除するマイグレーションスクリプト

処理能力情報（time_per_task, tasks_per_hour, tasks_per_day）のみに統一します。
"""

import yaml
import sys
from pathlib import Path
from datetime import datetime

# プロジェクトルートをパスに追加
project_root = Path(__file__).resolve().parent.parent


def backup_file(filepath: Path) -> Path:
    """ファイルをバックアップ"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = filepath.with_suffix(f".yaml.backup.{timestamp}")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return backup_path


def remove_legacy_fields(staff_skills_path: Path, dry_run: bool = False) -> None:
    """
    staff-skills.yamlからlevelとspeed_factorを削除

    Args:
        staff_skills_path: staff-skills.yamlのパス
        dry_run: Trueの場合は変更を保存しない
    """
    print("=" * 60)
    print("レガシーフィールド削除マイグレーション")
    print("=" * 60)
    print()

    # staff-skills.yamlを読み込み
    print("📖 スタッフスキルデータを読み込み中...")
    with open(staff_skills_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    staff_skills = data.get('staff_skills', {})
    print(f"   ✅ {len(staff_skills)}名のスタッフデータを読み込みました")
    print()

    # 各スタッフの各スキルからlevelとspeed_factorを削除
    print("🔄 レガシーフィールドを削除中...")
    removed_count = 0
    skipped_count = 0

    for staff_name, skills in staff_skills.items():
        print(f"\n👤 {staff_name}")

        for skill_name, skill_info in skills.items():
            # 空の辞書（拡張スキル）はスキップ
            if not skill_info:
                continue

            # level, speed_factor がない場合はスキップ
            if 'level' not in skill_info and 'speed_factor' not in skill_info:
                print(f"   ⏭️  {skill_name}: レガシーフィールドなし（スキップ）")
                skipped_count += 1
                continue

            # 処理能力情報がない場合はエラー
            if 'time_per_task' not in skill_info or 'tasks_per_day' not in skill_info:
                print(f"   ❌ {skill_name}: 処理能力情報がありません！")
                continue

            # レガシーフィールドを削除
            removed_fields = []
            if 'level' in skill_info:
                del skill_info['level']
                removed_fields.append('level')
            if 'speed_factor' in skill_info:
                del skill_info['speed_factor']
                removed_fields.append('speed_factor')

            print(f"   ✅ {skill_name}: {', '.join(removed_fields)} を削除")
            removed_count += 1

    print()
    print("=" * 60)
    print(f"📊 処理結果")
    print("=" * 60)
    print(f"   削除: {removed_count}件")
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
        description="staff-skills.yamlからlevelとspeed_factorを削除"
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

    # ファイル存在確認
    if not staff_skills_path.exists():
        print(f"❌ エラー: {staff_skills_path} が見つかりません")
        sys.exit(1)

    # マイグレーション実行
    remove_legacy_fields(staff_skills_path, args.dry_run)


if __name__ == "__main__":
    main()
