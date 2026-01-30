#!/usr/bin/env python3
"""
チェックポイント進捗確認スクリプト

14:00 / 17:00 のチェックポイントで進捗を分析
"""

import sys
import argparse
from datetime import datetime, time
from pathlib import Path
from collections import defaultdict
import yaml

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from models import DailyTaskList, TaskStatus


def calculate_progress(tasks, staff_name, checkpoint_time):
    """スタッフの進捗を計算"""
    
    staff_tasks = [t for t in tasks if t.get('assigned_to') == staff_name]
    
    if not staff_tasks:
        return None
    
    total = len(staff_tasks)
    completed = sum(1 for t in staff_tasks if t.get('status') == 'completed')
    in_progress = sum(1 for t in staff_tasks if t.get('status') == 'in_progress')
    pending = sum(1 for t in staff_tasks if t.get('status') == 'pending')
    
    progress_rate = (completed / total * 100) if total > 0 else 0
    
    # 平均処理時間の計算
    completed_tasks_with_time = [
        t for t in staff_tasks 
        if t.get('status') == 'completed' and t.get('actual_minutes')
    ]
    
    avg_actual_time = None
    avg_estimated_time = None
    
    if completed_tasks_with_time:
        avg_actual_time = sum(t.get('actual_minutes', 0) for t in completed_tasks_with_time) / len(completed_tasks_with_time)
        avg_estimated_time = sum(t.get('estimated_minutes', 15) for t in completed_tasks_with_time) / len(completed_tasks_with_time)
    
    # 作業種別の確認
    task_types = set(t.get('type') for t in staff_tasks)
    current_types = set(t.get('type') for t in staff_tasks if t.get('status') in ['in_progress', 'completed'])
    
    type_mismatch = len(task_types) > 1 and len(current_types) > len(task_types) - 1
    
    return {
        'staff_name': staff_name,
        'total': total,
        'completed': completed,
        'in_progress': in_progress,
        'pending': pending,
        'progress_rate': progress_rate,
        'avg_actual_time': avg_actual_time,
        'avg_estimated_time': avg_estimated_time,
        'type_mismatch': type_mismatch,
        'task_types': list(task_types),
        'current_types': list(current_types)
    }


def analyze_checkpoint(checkpoint_name, date_str=None):
    """チェックポイントの分析"""
    
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    task_file = project_root / "tasks" / "active" / f"{date_str}.yaml"
    
    if not task_file.exists():
        print(f"❌ エラー: タスクファイルが見つかりません: {task_file}")
        sys.exit(1)
    
    with open(task_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    tasks = data.get('tasks', [])
    
    if not tasks:
        print("⚠️ タスクが登録されていません")
        return
    
    # スタッフ一覧を取得
    staff_list = set(t.get('assigned_to') for t in tasks if t.get('assigned_to'))
    
    print("=" * 60)
    print(f"⏰ {checkpoint_name}チェックポイント - {date_str}")
    print("=" * 60)
    print()
    
    feedback_needed = []
    
    for staff in sorted(staff_list):
        progress = calculate_progress(tasks, staff, checkpoint_name)
        
        if progress is None:
            continue
        
        print(f"👤 {staff} ({', '.join(progress['task_types'])})")
        print(f"  ✅ 完了: {progress['completed']}件 / 予定: {progress['total']}件 ({progress['progress_rate']:.0f}%)")
        
        # 進捗状況の判定
        expected_rate = 50 if checkpoint_name == "14:00" else 100
        
        if progress['progress_rate'] < expected_rate * 0.3:
            print(f"  ❌ 大幅遅延 - 確認推奨")
            feedback_needed.append((staff, "大幅遅延"))
        elif progress['progress_rate'] < expected_rate * 0.7:
            print(f"  ⚠️ 進捗やや遅れ")
            if progress['avg_actual_time'] and progress['avg_estimated_time']:
                if progress['avg_actual_time'] > progress['avg_estimated_time'] * 1.2:
                    print(f"     平均処理時間: {progress['avg_actual_time']:.0f}分 vs 予定: {progress['avg_estimated_time']:.0f}分")
        else:
            print(f"  ✅ 順調")
        
        # 作業種別の不一致チェック
        if progress['type_mismatch']:
            print(f"  ⚠️ 複数の作業種別を実施中: {', '.join(progress['current_types'])}")
            feedback_needed.append((staff, f"作業種別混在: {', '.join(progress['current_types'])}"))
        
        print()
    
    # フィードバック推奨
    if feedback_needed:
        print("=" * 60)
        print("【要フィードバック】")
        print("=" * 60)
        for staff, reason in feedback_needed:
            print(f"- {staff}: {reason}")
        print()
    else:
        print("=" * 60)
        print("✅ 全スタッフ順調に進捗しています")
        print("=" * 60)
        print()


def main():
    parser = argparse.ArgumentParser(description="チェックポイント進捗確認")
    parser.add_argument('--time', choices=['14:00', '17:00'], required=True, help='チェックポイント時刻')
    parser.add_argument('--date', help='対象日 (YYYY-MM-DD形式、省略時は今日)')
    
    args = parser.parse_args()
    
    analyze_checkpoint(args.time, args.date)


if __name__ == "__main__":
    main()
