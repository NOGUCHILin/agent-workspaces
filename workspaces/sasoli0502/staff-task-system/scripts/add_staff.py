#!/usr/bin/env python3
"""
スタッフ追加スクリプト

対話形式で新しいスタッフを登録
- config/staff.yaml に基本情報を追加
- config/staff-skills.yaml にスキル情報を追加（オプション）
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
import yaml

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from models import Staff, StaffConstraints


def get_next_employee_id(staff_data):
    """次の社員番号を自動生成

    Args:
        staff_data: 既存のスタッフデータ

    Returns:
        str: 次の社員番号（例: EMP014）
    """
    existing_ids = []
    for staff_info in staff_data.values():
        emp_id = staff_info.get('employee_id', '')
        if emp_id.startswith('EMP'):
            try:
                num = int(emp_id[3:])
                existing_ids.append(num)
            except ValueError:
                pass

    if existing_ids:
        next_num = max(existing_ids) + 1
    else:
        next_num = 1

    return f"EMP{next_num:03d}"


def add_staff():
    """対話形式でスタッフを追加"""

    print("=" * 60)
    print("👤 スタッフ追加")
    print("=" * 60)
    print()

    # config/staff.yaml の読み込み
    staff_file = project_root / "config" / "staff.yaml"

    if not staff_file.exists():
        print(f"❌ エラー: {staff_file} が見つかりません")
        sys.exit(1)

    with open(staff_file, 'r', encoding='utf-8') as f:
        staff_config = yaml.safe_load(f)

    staff_data = staff_config.get('staff', {})

    # 基本情報入力
    print("📝 基本情報を入力してください")
    print()

    full_name = input("フルネーム（例: 山田 太郎）: ").strip()
    if not full_name:
        print("❌ エラー: フルネームは必須です")
        sys.exit(1)

    # YAMLキー（苗字）を自動抽出
    yaml_key = full_name.split()[0] if ' ' in full_name else full_name

    # 既存チェック
    if yaml_key in staff_data:
        print(f"❌ エラー: {yaml_key} は既に登録されています")
        sys.exit(1)

    nickname = input("通称・愛称（例: やまちゃん）: ").strip()

    # 社員番号を自動生成
    employee_id = get_next_employee_id(staff_data)
    print(f"社員番号（自動生成）: {employee_id}")
    print()

    # 制約情報
    print("📋 制約情報（オプション、Enterでスキップ）")
    print()

    max_tasks_input = input("1日最大タスク数（デフォルト: 20）: ").strip()
    max_tasks = int(max_tasks_input) if max_tasks_input else 20

    preferred_tasks_input = input("得意なタスク種別（カンマ区切り、例: 査定,検品）: ").strip()
    preferred_tasks = [t.strip() for t in preferred_tasks_input.split(',')] if preferred_tasks_input else []

    notes = input("備考: ").strip()

    print()
    print("=" * 60)
    print("📊 入力内容の確認")
    print("=" * 60)
    print()
    print(f"YAMLキー: {yaml_key}")
    print(f"フルネーム: {full_name}")
    print(f"通称・愛称: {nickname}")
    print(f"社員番号: {employee_id}")
    print(f"1日最大タスク数: {max_tasks}")
    print(f"得意なタスク: {preferred_tasks}")
    print(f"備考: {notes}")
    print()

    confirm = input("この内容で登録しますか？ (y/n): ")
    if confirm.lower() != 'y':
        print("❌ キャンセルしました")
        sys.exit(0)

    # スタッフデータを作成
    new_staff = {
        'full_name': full_name,
        'nickname': nickname if nickname else None,
        'employee_id': employee_id,
        'constraints': {
            'max_tasks_per_day': max_tasks,
            'preferred_task_types': preferred_tasks,
            'unavailable_dates': []
        },
        'notes': notes if notes else ""
    }

    # バリデーション
    try:
        Staff(**new_staff)
    except Exception as e:
        print(f"❌ データバリデーションエラー: {e}")
        sys.exit(1)

    # staff.yaml に追加
    staff_data[yaml_key] = new_staff
    staff_config['staff'] = staff_data

    with open(staff_file, 'w', encoding='utf-8') as f:
        yaml.dump(staff_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print()
    print("=" * 60)
    print("✅ スタッフを登録しました")
    print("=" * 60)
    print()

    # スキル登録の案内
    print("📋 次のステップ:")
    print()
    print("スキル情報を登録する場合は、以下のコマンドを実行してください:")
    print(f"  uv run python scripts/add_staff_skill.py {yaml_key}")
    print()
    print("または、config/staff-skills.yaml を直接編集してください:")
    print(f"  {project_root / 'config' / 'staff-skills.yaml'}")
    print()


def main():
    parser = argparse.ArgumentParser(description="新しいスタッフを追加")

    args = parser.parse_args()

    add_staff()


if __name__ == "__main__":
    main()
