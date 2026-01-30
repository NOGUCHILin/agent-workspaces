#!/usr/bin/env python3
"""
スキルマトリックス表示スクリプト

全スタッフのスキルを一覧表示
"""

import sys
import argparse
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from models import get_all_staff_with_skills

# コアスキル（詳細表示対象）
CORE_SKILLS = {"査定", "検品", "出品", "修理"}


def show_skill_matrix():
    """スキルマトリックスを表示"""

    staff_dict = get_all_staff_with_skills()

    # コアスキルのみを表示対象とする
    task_types = sorted(CORE_SKILLS)
    staff_names = sorted(staff_dict.keys())
    
    print("=" * 80)
    print("📊 スキルマトリックス")
    print("=" * 80)
    print()
    
    # ヘッダー
    header = "スタッフ".ljust(10)
    for task_type in task_types:
        header += f"| {task_type.center(12)} "
    print(header)
    print("-" * 80)
    
    # 各スタッフの行
    for staff_name in staff_names:
        staff_info = staff_dict[staff_name]
        skills = staff_info.get('skills', {})

        row = staff_name.ljust(10)

        for task_type in task_types:
            if task_type in skills:
                skill = skills[task_type]

                # 空の辞書（拡張スキル）はスキップ
                if not isinstance(skill, dict) or 'time_per_task' not in skill:
                    row += f"| {'-'.center(12)} "
                    continue

                tasks_per_day = skill.get('tasks_per_day')

                # スキル表示（処理能力情報のみ）
                perf_str = f"{tasks_per_day}/日"

                cell = f"{perf_str}".strip()
                row += f"| {cell.center(12)} "
            else:
                row += f"| {'-'.center(12)} "

        print(row)
    
    print()
    print("=" * 80)
    print()
    
    # 凡例
    print("📖 凡例:")
    print("  XX/日 = 1日あたりの処理可能数")
    print("  -     = 対応不可")
    print()
    
    # スタッフごとの詳細サマリー
    print("=" * 80)
    print("👥 スタッフ詳細")
    print("=" * 80)
    print()
    
    for staff_name in staff_names:
        staff_info = staff_dict[staff_name]
        skills = staff_info.get('skills', {})
        constraints = staff_info.get('constraints', {})

        print(f"📛 {staff_name}（{staff_info.get('full_name', staff_name)}）")

        # コアスキル一覧（処理能力情報付き）
        core_skill_list = []
        for task_type in CORE_SKILLS:
            if task_type in skills:
                skill = skills[task_type]

                # 空の辞書（拡張スキル）はスキップ
                if not isinstance(skill, dict) or 'time_per_task' not in skill:
                    continue

                time_per_task = skill.get('time_per_task')
                tasks_per_day = skill.get('tasks_per_day')

                perf_str = f"({time_per_task}分/件, {tasks_per_day}件/日)"

                core_skill_list.append(f"{task_type}: {perf_str}")

        if core_skill_list:
            print(f"  スキル: {' | '.join(core_skill_list)}")
        else:
            print(f"  スキル: なし")

        # 制約
        max_tasks = constraints.get('max_tasks_per_day', '-')
        print(f"  最大タスク数: {max_tasks}件/日")

        preferred = constraints.get('preferred_task_types', [])
        if preferred:
            print(f"  優先業務: {', '.join(preferred)}")

        notes = staff_info.get('notes', '')
        if notes:
            print(f"  備考: {notes}")

        print()


def main():
    parser = argparse.ArgumentParser(description="スキルマトリックスを表示")
    
    args = parser.parse_args()
    
    show_skill_matrix()


if __name__ == "__main__":
    main()
