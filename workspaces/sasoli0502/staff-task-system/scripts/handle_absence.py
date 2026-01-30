#!/usr/bin/env python3
"""
欠勤対応スクリプト

スタッフが欠勤した場合、そのスタッフのタスクを抽出し、再割り当て候補を提案
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
import yaml

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent


def load_staff_skills():
    """スタッフのスキル情報を読み込み"""
    staff_file = project_root / "config" / "staff.yaml"
    
    with open(staff_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    return data.get('staff', {})


def find_reassignment_candidates(task_type, absent_staff, staff_skills):
    """再割り当て候補を探す"""
    candidates = []

    for staff_name, info in staff_skills.items():
        if staff_name == absent_staff:
            continue

        skills = info.get('skills', {})
        if task_type in skills:
            skill_info = skills[task_type]
            # time_per_taskの存在確認でスキル保持を判定
            if 'time_per_task' in skill_info:
                candidates.append({
                    'name': staff_name,
                    'tasks_per_day': skill_info.get('tasks_per_day', 0),
                    'certification': skill_info.get('certification', False)
                })

    # 処理能力でソート（高い順）
    candidates.sort(key=lambda x: x['tasks_per_day'], reverse=True)

    return candidates


def handle_absence(staff_name, reason=None, date_str=None, auto_reassign=False):
    """欠勤対応を実行（非対話式）

    Args:
        staff_name: 欠勤スタッフ名
        reason: 欠勤理由
        date_str: 対象日（省略時は今日）
        auto_reassign: Trueの場合、確認なしで再割り当てを実行
    """

    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    task_file = project_root / "tasks" / "active" / f"{date_str}.yaml"
    
    if not task_file.exists():
        print(f"❌ エラー: タスクファイルが見つかりません: {task_file}")
        sys.exit(1)
    
    with open(task_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    tasks = data.get('tasks', [])
    
    # 欠勤スタッフのタスクを抽出
    absent_tasks = [t for t in tasks if t.get('assigned_to') == staff_name]
    
    if not absent_tasks:
        print("=" * 60)
        print(f"⚠️ {staff_name}さんには本日のタスクがありません")
        print("=" * 60)
        return
    
    # 未完了タスクのみ対象
    pending_tasks = [t for t in absent_tasks if t.get('status') in ['pending', 'in_progress']]
    completed_tasks = [t for t in absent_tasks if t.get('status') == 'completed']
    
    print("=" * 60)
    print(f"🚨 {staff_name}さんの欠勤対応")
    print("=" * 60)
    print()
    
    if reason:
        print(f"📝 理由: {reason}")
        print()
    
    print(f"📊 タスク状況:")
    print(f"  完了済み: {len(completed_tasks)}件")
    print(f"  未完了: {len(pending_tasks)}件（再割り当て対象）")
    print()
    
    if not pending_tasks:
        print("✅ 再割り当てが必要なタスクはありません")
        print()
        return
    
    # タスク種別ごとに集計
    task_types = {}
    for task in pending_tasks:
        task_type = task.get('type')
        if task_type not in task_types:
            task_types[task_type] = []
        task_types[task_type].append(task)
    
    print("📋 未完了タスクの内訳:")
    for task_type, type_tasks in task_types.items():
        print(f"  {task_type}: {len(type_tasks)}件")
    print()
    
    # スキルシートを読み込み
    staff_skills = load_staff_skills()
    
    # 再割り当て提案
    print("=" * 60)
    print("💡 再割り当て提案")
    print("=" * 60)
    print()
    
    reassignments = {}
    
    for task_type, type_tasks in task_types.items():
        candidates = find_reassignment_candidates(task_type, staff_name, staff_skills)
        
        print(f"【{task_type}】{len(type_tasks)}件")
        
        if not candidates:
            print(f"  ⚠️ 対応可能なスタッフがいません")
            print()
            continue
        
        print(f"  推奨スタッフ:")
        for i, candidate in enumerate(candidates[:3], 1):  # 上位3名まで表示
            tasks_per_day = candidate['tasks_per_day']
            cert = " 📜" if candidate['certification'] else ""
            print(f"    {i}. {candidate['name']} ({tasks_per_day}件/日){cert}")

        # 最上位候補に自動割り当て提案
        best_candidate = candidates[0]
        reassignments[task_type] = {
            'tasks': type_tasks,
            'to_staff': best_candidate['name'],
            'reason': f"処理能力: {best_candidate['tasks_per_day']}件/日"
        }
        print()
    
    # 再割り当て実行の確認
    print("=" * 60)
    print("🔄 再割り当て案")
    print("=" * 60)
    print()
    
    for task_type, info in reassignments.items():
        count = len(info['tasks'])
        to_staff = info['to_staff']
        reason_text = info['reason']
        print(f"📌 {task_type} {count}件 → {to_staff}")
        print(f"   理由: {reason_text}")
        print()

    # 再割り当て実行
    if auto_reassign:
        print("🔄 再割り当てを実行します...")
        print()

        for task_type, info in reassignments.items():
            for task in info['tasks']:
                task['assigned_to'] = info['to_staff']
                task['reassigned_from'] = staff_name
                task['reassigned_at'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00")
                task['reassignment_reason'] = reason if reason else "欠勤"

        # YAMLファイルに保存
        with open(task_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        print("=" * 60)
        print("✅ 再割り当て完了")
        print("=" * 60)
        print()

        total_reassigned = sum(len(info['tasks']) for info in reassignments.values())
        print(f"📊 {total_reassigned}件のタスクを再割り当てしました")
        print()
        print("「今日のタスク教えて」で確認できます")
        print()
    else:
        print("💡 再割り当てを実行する場合は --auto-reassign フラグを追加してください")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="欠勤対応（非対話式）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 欠勤対応の提案のみ（再割り当ては実行しない）
  uv run python scripts/handle_absence.py 雜賀 --reason "体調不良"

  # 欠勤対応と自動再割り当て
  uv run python scripts/handle_absence.py 雜賀 --reason "体調不良" --auto-reassign

  # 特定日の欠勤対応
  uv run python scripts/handle_absence.py 細谷 --date 2025-10-30 --auto-reassign
"""
    )
    parser.add_argument('staff', help='欠勤スタッフ名')
    parser.add_argument('--reason', help='欠勤理由（例: 体調不良）')
    parser.add_argument('--date', help='対象日 (YYYY-MM-DD形式、省略時は今日)')
    parser.add_argument('--auto-reassign', action='store_true', help='確認なしで再割り当てを実行')

    args = parser.parse_args()

    handle_absence(args.staff, args.reason, args.date, args.auto_reassign)


if __name__ == "__main__":
    main()
