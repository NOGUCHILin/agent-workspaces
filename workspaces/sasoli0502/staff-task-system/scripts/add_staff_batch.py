#!/usr/bin/env python3
"""
スタッフ一括追加スクリプト（非対話式）

JSON/YAML形式でスタッフ情報を一括登録
- 基本情報（staff.yaml）
- スキル情報（staff-skills.yaml）
を同時に追加
"""

import sys
import argparse
import json
from pathlib import Path
import yaml

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from models import Staff


def get_next_employee_id(staff_data, preferred_id=None):
    """次の社員番号を取得

    Args:
        staff_data: 既存のスタッフデータ
        preferred_id: 希望する社員番号（欠番を埋める場合）

    Returns:
        str: 社員番号（例: EMP003）
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

    # 希望IDが指定されていて、かつ使用されていない場合
    if preferred_id:
        if preferred_id.startswith('EMP'):
            try:
                num = int(preferred_id[3:])
                if num not in existing_ids:
                    return preferred_id
            except ValueError:
                pass

    # 最大番号+1
    if existing_ids:
        next_num = max(existing_ids) + 1
    else:
        next_num = 1

    return f"EMP{next_num:03d}"


def add_staff_batch(data_file, dry_run=False):
    """JSONまたはYAMLファイルからスタッフを一括追加

    Args:
        data_file: スタッフデータファイル（JSON or YAML）
        dry_run: True の場合、実際には保存しない
    """

    print("=" * 60)
    print("👥 スタッフ一括追加（非対話式）")
    print("=" * 60)
    print()

    # データファイル読み込み
    data_path = Path(data_file)
    if not data_path.exists():
        print(f"❌ エラー: {data_file} が見つかりません")
        sys.exit(1)

    with open(data_path, 'r', encoding='utf-8') as f:
        if data_path.suffix == '.json':
            staff_list = json.load(f)
        elif data_path.suffix in ['.yaml', '.yml']:
            staff_list = yaml.safe_load(f)
        else:
            print(f"❌ エラー: 非対応の形式です（JSON/YAMLのみ）")
            sys.exit(1)

    if not isinstance(staff_list, list):
        print(f"❌ エラー: データはリスト形式である必要があります")
        sys.exit(1)

    print(f"📂 データファイル: {data_file}")
    print(f"👤 登録予定: {len(staff_list)}名")
    print()

    # 既存データ読み込み
    staff_file = project_root / "config" / "staff.yaml"
    staff_skills_file = project_root / "config" / "staff-skills.yaml"

    with open(staff_file, 'r', encoding='utf-8') as f:
        staff_config = yaml.safe_load(f)
    staff_data = staff_config.get('staff', {})

    with open(staff_skills_file, 'r', encoding='utf-8') as f:
        skills_config = yaml.safe_load(f)
    staff_skills_data = skills_config.get('staff_skills', {})

    # スタッフ追加処理
    added_count = 0
    skipped_count = 0

    for staff_info in staff_list:
        full_name = staff_info.get('full_name')
        if not full_name:
            print(f"⚠️  スキップ: full_name が必須です")
            skipped_count += 1
            continue

        # YAMLキー決定
        yaml_key = staff_info.get('yaml_key')
        if not yaml_key:
            # 自動生成: フルネームの苗字
            yaml_key = full_name.split()[0] if ' ' in full_name else full_name

        # 既存チェック
        if yaml_key in staff_data:
            print(f"⚠️  スキップ: {yaml_key} は既に登録されています")
            skipped_count += 1
            continue

        # 社員番号決定
        preferred_id = staff_info.get('employee_id')
        employee_id = get_next_employee_id(staff_data, preferred_id)

        # 基本情報作成
        new_staff = {
            'full_name': full_name,
            'nickname': staff_info.get('nickname', ''),
            'employee_id': employee_id,
            'constraints': {
                'max_tasks_per_day': staff_info.get('max_tasks_per_day', 20),
                'preferred_task_types': staff_info.get('preferred_task_types', []),
                'unavailable_dates': []
            },
            'notes': staff_info.get('notes', '')
        }

        # バリデーション
        try:
            Staff(**new_staff)
        except Exception as e:
            print(f"❌ バリデーションエラー ({yaml_key}): {e}")
            skipped_count += 1
            continue

        # スキル情報作成
        skills = staff_info.get('skills', {})

        # 追加
        print(f"✅ 追加: {yaml_key} ({full_name}) - {employee_id}")
        if skills:
            skill_names = list(skills.keys())
            print(f"   スキル: {len(skill_names)}種類 - {', '.join(skill_names[:5])}{('...' if len(skill_names) > 5 else '')}")

        staff_data[yaml_key] = new_staff
        if skills:
            staff_skills_data[yaml_key] = skills

        added_count += 1

    print()
    print("=" * 60)
    print(f"📊 処理結果")
    print("=" * 60)
    print(f"追加: {added_count}名")
    print(f"スキップ: {skipped_count}名")
    print()

    if added_count == 0:
        print("⚠️  追加するスタッフがありませんでした")
        return

    if dry_run:
        print("🔍 Dry-runモード: 実際には保存しません")
        print()
        print("保存予定のデータ:")
        for yaml_key in [k for k in staff_data.keys() if k not in staff_config.get('staff', {})]:
            print(f"  - {yaml_key}: {staff_data[yaml_key]['full_name']}")
        return

    # 保存
    staff_config['staff'] = staff_data
    skills_config['staff_skills'] = staff_skills_data

    with open(staff_file, 'w', encoding='utf-8') as f:
        yaml.dump(staff_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    with open(staff_skills_file, 'w', encoding='utf-8') as f:
        yaml.dump(skills_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print("✅ 保存完了")
    print()
    print("💡 次のステップ: バリデーション実行")
    print("   uv run python scripts/validate.py --all")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="スタッフ一括追加（非対話式）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # JSONファイルから追加
  uv run python scripts/add_staff_batch.py staff_data.json

  # YAMLファイルから追加
  uv run python scripts/add_staff_batch.py staff_data.yaml

  # Dry-run（保存しない）
  uv run python scripts/add_staff_batch.py staff_data.json --dry-run

データフォーマット（JSON）:
  [
    {
      "full_name": "野口 創",
      "nickname": "そう",
      "employee_id": "EMP003",
      "yaml_key": "創",
      "max_tasks_per_day": 20,
      "preferred_task_types": ["査定", "修理"],
      "notes": "査定と修理のエキスパート",
      "skills": {
        "査定": {"level": 3, "speed_factor": 1.0, "certification": false},
        "修理": {"level": 3, "speed_factor": 1.0, "certification": false},
        "返信": {},
        "梱包キット作成": {}
      }
    }
  ]
"""
    )
    parser.add_argument('data_file', help='スタッフデータファイル（JSON or YAML）')
    parser.add_argument('--dry-run', action='store_true', help='Dry-runモード（保存しない）')

    args = parser.parse_args()

    add_staff_batch(args.data_file, args.dry_run)


if __name__ == "__main__":
    main()
