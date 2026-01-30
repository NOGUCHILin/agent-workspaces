#!/usr/bin/env python3
"""
staff.yamlを簡素化して全スタッフを追加

既存: スキル情報を削除
新規: CSVから基本情報のみ追加
"""

import csv
import yaml
from pathlib import Path
from typing import Dict, Any

# スタッフの正式名称マッピング（CSVから取得）
STAFF_FULL_NAMES = {
    "江口": "江口 那都",
    "雜賀": "雜賀 晴士",
    "野口": "野口 器",
    "佐々木": "佐々木 悠斗",
    "須加尾": "須加尾 蓮",
    "高橋": "高橋 諒",
    "島田": "島田 博文",
    "平山": "平山 優大",
    "細谷": "細谷 尚央",
    "NANT": "NANT YOON THIRI ZAW OO",
    "原": "原 紅映",
    "本間": "本間 久隆",
}

# 既存スタッフのemployee_id
EXISTING_STAFF = {
    "細谷": "EMP001",
    "江口": "EMP002",
    "シャシャ": "EMP003",
    "佐々木": "EMP004",
    "雜賀": "EMP005",
}


def load_existing_staff() -> Dict[str, Any]:
    """既存のstaff.yamlを読み込み"""
    with open("config/staff.yaml", 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_all_staff_from_skills() -> list:
    """staff-skills.yamlから全スタッフ名を取得"""
    with open("config/staff-skills.yaml", 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return list(data['staff_skills'].keys())


def generate_simplified_staff_yaml() -> Dict[str, Any]:
    """簡素化されたstaff.yamlデータを生成"""
    existing_data = load_existing_staff()
    all_staff_names = load_all_staff_from_skills()

    new_staff_data = {}
    next_emp_id = 6  # EMP006から開始

    for staff_name in all_staff_names:
        # 正式名称
        full_name = STAFF_FULL_NAMES.get(staff_name, staff_name)

        if staff_name in EXISTING_STAFF:
            # 既存スタッフ → constraintsとnotesを保持、skillsを削除
            old_data = existing_data['staff'][staff_name]
            new_staff_data[staff_name] = {
                "full_name": full_name,
                "employee_id": EXISTING_STAFF[staff_name],
                "constraints": old_data.get('constraints', {
                    "max_tasks_per_day": 20,
                    "preferred_task_types": [],
                    "unavailable_dates": []
                }),
                "notes": old_data.get('notes', '')
            }
        else:
            # 新規スタッフ → デフォルト値
            new_staff_data[staff_name] = {
                "full_name": full_name,
                "employee_id": f"EMP{next_emp_id:03d}",
                "constraints": {
                    "max_tasks_per_day": 20,
                    "preferred_task_types": [],
                    "unavailable_dates": []
                },
                "notes": ""
            }
            next_emp_id += 1

    # シャシャ（NANT）の特別処理
    if "シャシャ" in existing_data['staff'] and "NANT" not in new_staff_data:
        # シャシャのデータをNANTとして登録
        new_staff_data["NANT"] = {
            "full_name": "NANT YOON THIRI ZAW OO",
            "employee_id": "EMP003",
            "constraints": existing_data['staff']['シャシャ'].get('constraints', {
                "max_tasks_per_day": 20,
                "preferred_task_types": ["出品"],
                "unavailable_dates": []
            }),
            "notes": existing_data['staff']['シャシャ'].get('notes', '出品作業のスペシャリスト。')
        }

    # グローバル設定を保持
    settings = existing_data.get('settings', {
        "working_hours": {
            "start": "09:00",
            "lunch_start": "12:00",
            "lunch_end": "13:00",
            "end": "18:00"
        },
        "default_task_duration": {
            "査定": 15,
            "検品": 20,
            "出品": 10,
            "修理": 60
        }
    })

    return {
        "staff": new_staff_data,
        "settings": settings
    }


def save_yaml(data: Dict[str, Any], output_path: str) -> None:
    """YAMLファイルに保存"""
    with open(output_path, 'w', encoding='utf-8') as f:
        # ヘッダーコメント
        f.write("# スタッフマスタデータ（簡素版）\n")
        f.write("# スキル情報は config/staff-skills.yaml に分離\n")
        f.write("# 最終更新: 2025-10-21\n\n")

        # YAMLデータ
        yaml.dump(
            data,
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            indent=2
        )


def main():
    print("📋 既存のstaff.yamlを読み込み中...")
    print("\n🔨 簡素化されたstaff.yamlを生成中...")

    simplified_data = generate_simplified_staff_yaml()

    print(f"✓ {len(simplified_data['staff'])}名のスタッフを処理しました")

    # バックアップを作成
    import shutil
    import datetime
    backup_path = f"config/staff.yaml.backup.{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy("config/staff.yaml", backup_path)
    print(f"📦 バックアップを作成: {backup_path}")

    # 保存
    save_yaml(simplified_data, "config/staff.yaml")
    print(f"✅ config/staff.yaml を更新しました")

    print("\n📊 スタッフ一覧:")
    for staff_name, staff_info in simplified_data['staff'].items():
        emp_id = staff_info['employee_id']
        full_name = staff_info['full_name']
        print(f"  {emp_id}: {full_name} ({staff_name})")


if __name__ == "__main__":
    main()
