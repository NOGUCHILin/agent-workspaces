#!/usr/bin/env python3
"""
スタッフ情報表示ツール

使用例:
  uv run python scripts/show_staff.py              # 全員表示
  uv run python scripts/show_staff.py --name 細谷  # 特定スタッフ詳細
  uv run python scripts/show_staff.py --skill 修理 # 特定スキル保持者
  uv run python scripts/show_staff.py --skill 法人販売  # 拡張スキル検索
"""

import sys
import argparse
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from models import get_all_staff_with_skills, load_skills

# コアスキル（詳細管理）
CORE_SKILLS = {"査定", "検品", "出品", "修理"}


def show_all_staff():
    """全スタッフを表示"""
    all_staff = get_all_staff_with_skills()

    print("\n" + "=" * 70)
    print("👥 スタッフ一覧")
    print("=" * 70 + "\n")

    for staff_name, staff_info in all_staff.items():
        print(f"📛 {staff_info['full_name']} ({staff_info['employee_id']})")

        # コアスキル表示
        core_skills = []
        for skill_name, skill_detail in staff_info['skills'].items():
            if skill_name not in CORE_SKILLS:
                continue

            if isinstance(skill_detail, dict) and 'time_per_task' in skill_detail:
                time_per_task = skill_detail.get('time_per_task')
                tasks_per_day = skill_detail.get('tasks_per_day')

                # 処理能力情報を表示
                perf_info = f"{time_per_task}分/件, {tasks_per_day}件/日"
                core_skills.append(f"{skill_name}: {perf_info}")

        if core_skills:
            print(f"  スキル: {' | '.join(core_skills)}")

        # 制約
        constraints = staff_info['constraints']
        print(f"  最大タスク数: {constraints['max_tasks_per_day']}件/日")
        if constraints.get('preferred_task_types'):
            print(f"  優先業務: {', '.join(constraints['preferred_task_types'])}")

        # 備考
        if staff_info.get('notes'):
            print(f"  備考: {staff_info['notes']}")

        print()


def show_staff_detail(name: str):
    """特定スタッフの詳細表示"""
    all_staff = get_all_staff_with_skills()

    # 名前で検索（部分一致）
    staff_info = None
    staff_key = None
    for key, info in all_staff.items():
        if name in key or name in info['full_name']:
            staff_info = info
            staff_key = key
            break

    if not staff_info:
        print(f"エラー: スタッフ '{name}' が見つかりません")
        return False

    print("\n" + "=" * 70)
    print(f"👤 {staff_info['full_name']} の詳細情報")
    print("=" * 70 + "\n")

    print(f"社員番号: {staff_info['employee_id']}")
    if staff_info.get('nickname'):
        print(f"通称: {staff_info['nickname']}")
    print(f"キー: {staff_key}\n")

    # コアスキル詳細
    print("📊 コアスキル:")
    core_found = False
    for skill_name, skill_detail in staff_info['skills'].items():
        if skill_name not in CORE_SKILLS:
            continue

        if isinstance(skill_detail, dict) and 'time_per_task' in skill_detail:
            core_found = True
            print(f"\n  {skill_name}")
            print(f"    処理時間: {skill_detail['time_per_task']}分/件")
            print(f"    処理能力: {skill_detail['tasks_per_hour']}件/時")
            print(f"    1日処理数: {skill_detail['tasks_per_day']}件/日")

    if not core_found:
        print("  なし")

    # 拡張スキル
    print(f"\n🔧 その他のスキル:")
    extended_skills = []
    for skill_name in staff_info['skills'].keys():
        if skill_name not in CORE_SKILLS:
            extended_skills.append(skill_name)

    if extended_skills:
        # カテゴリ分類して表示
        skills_data = load_skills()
        by_category = {}
        for skill_name in extended_skills:
            skill_info = skills_data['skills'].get(skill_name, {})
            category = skill_info.get('category', 'other')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(skill_name)

        for category, skill_list in sorted(by_category.items()):
            category_info = skills_data['categories'].get(category, {})
            category_name = category_info.get('display_name', category)
            print(f"  [{category_name}] {', '.join(skill_list)}")
    else:
        print("  なし")

    # 制約
    constraints = staff_info['constraints']
    print(f"\n⚙️ 制約:")
    print(f"  1日最大タスク数: {constraints['max_tasks_per_day']}件")
    if constraints.get('preferred_task_types'):
        print(f"  優先業務: {', '.join(constraints['preferred_task_types'])}")
    else:
        print(f"  優先業務: なし")

    if constraints.get('unavailable_dates'):
        print(f"  休暇予定:")
        for d in constraints['unavailable_dates']:
            print(f"    - {d}")
    else:
        print(f"  休暇予定: なし")

    if staff_info.get('notes'):
        print(f"\n💡 備考:")
        print(f"  {staff_info['notes']}")

    print()
    return True


def show_skill_holders(skill: str):
    """特定スキル保持者を表示"""
    all_staff = get_all_staff_with_skills()

    holders = []
    for staff_name, staff_info in all_staff.items():
        if skill in staff_info['skills']:
            skill_detail = staff_info['skills'][skill]
            holders.append((staff_info, skill_detail))

    if not holders:
        print(f"\n'{skill}' のスキルを持つスタッフはいません")
        return

    print("\n" + "=" * 70)
    print(f"🔍 '{skill}' スキル保持者")
    print("=" * 70 + "\n")

    # コアスキルの場合は処理能力順にソート（高い方が先）
    if skill in CORE_SKILLS:
        holders.sort(key=lambda x: x[1].get('tasks_per_day', 0) if isinstance(x[1], dict) else 0, reverse=True)

        for staff_info, skill_detail in holders:
            if isinstance(skill_detail, dict) and 'time_per_task' in skill_detail:
                time_per_task = skill_detail.get('time_per_task')
                tasks_per_day = skill_detail.get('tasks_per_day')
                nickname_info = f" ({staff_info['nickname']})" if staff_info.get('nickname') else ""

                # 処理能力情報
                perf_info = f"{time_per_task}分/件, {tasks_per_day}件/日"

                print(f"  {staff_info['full_name']}{nickname_info}: {perf_info}")
    else:
        # 拡張スキルの場合は名前順
        holders.sort(key=lambda x: x[0]['full_name'])
        for staff_info, _ in holders:
            print(f"  {staff_info['full_name']}")

    print()


def main():
    parser = argparse.ArgumentParser(description="スタッフ情報表示")
    parser.add_argument(
        "--name",
        help="特定スタッフの詳細表示"
    )
    parser.add_argument(
        "--skill",
        help="特定スキル保持者を表示（例: 査定, 修理, 法人販売）"
    )

    args = parser.parse_args()

    try:
        # 表示
        if args.name:
            success = show_staff_detail(args.name)
            return 0 if success else 1
        elif args.skill:
            show_skill_holders(args.skill)
        else:
            show_all_staff()

        return 0

    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
