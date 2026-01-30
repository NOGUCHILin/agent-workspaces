#!/usr/bin/env python3
"""
タスク一括作成スクリプト

役割分担決定後、複数のタスクを一括作成
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
import yaml

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from models import TaskType, TaskPriority, TaskStatus


def bulk_create_tasks(assignments, date_str=None):
    """
    タスクを一括作成
    
    assignments: [
        {"staff": "細谷", "type": "査定", "count": 20, "desc": "iPhone"},
        {"staff": "江口", "type": "査定", "count": 15, "desc": "Android"},
        ...
    ]
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
    
    # 既存のタスクIDから次の番号を取得
    existing_ids = [t.get('id', '') for t in tasks]
    max_num = 0
    for task_id in existing_ids:
        if task_id.startswith(f"T{date_str.replace('-', '')}-"):
            try:
                num = int(task_id.split('-')[1])
                max_num = max(max_num, num)
            except:
                pass
    
    next_num = max_num + 1
    
    created_tasks = []
    
    for assignment in assignments:
        staff = assignment['staff']
        task_type = assignment['type']
        count = assignment['count']
        desc_base = assignment.get('desc', task_type)
        priority = assignment.get('priority', 'medium')
        estimated_minutes = assignment.get('estimated_minutes', 15)
        
        for i in range(count):
            task_id = f"T{date_str.replace('-', '')}-{next_num:03d}"
            
            new_task = {
                'id': task_id,
                'type': task_type,
                'description': f"{desc_base} #{i+1}",
                'assigned_to': staff,
                'status': 'pending',
                'priority': priority,
                'estimated_minutes': estimated_minutes,
                'created_at': datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00")
            }
            
            tasks.append(new_task)
            created_tasks.append(new_task)
            next_num += 1
    
    # YAMLファイルに保存
    data['tasks'] = tasks
    
    with open(task_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    print("=" * 60)
    print(f"✅ タスクを一括作成しました ({len(created_tasks)}件)")
    print("=" * 60)
    print()
    
    # スタッフごとに集計
    staff_counts = {}
    for task in created_tasks:
        staff = task['assigned_to']
        if staff not in staff_counts:
            staff_counts[staff] = []
        staff_counts[staff].append(task)
    
    for staff, staff_tasks in sorted(staff_counts.items()):
        task_ids = [t['id'] for t in staff_tasks]
        print(f"👤 {staff}: {len(staff_tasks)}件")
        print(f"   {task_ids[0]} ~ {task_ids[-1]}")
        print()
    
    print("=" * 60)
    print("「今日のタスク教えて」で確認できます")
    print("=" * 60)
    
    return created_tasks


def main():
    parser = argparse.ArgumentParser(description="タスクを一括作成")
    parser.add_argument('--date', help='対象日 (YYYY-MM-DD形式、省略時は今日)')
    parser.add_argument('--json', help='割り当てJSON')
    
    args = parser.parse_args()
    
    # テスト用
    if args.json:
        import json
        assignments = json.loads(args.json)
    else:
        # デモ: 朝の集計に基づいて自動生成
        assignments = [
            {"staff": "細谷", "type": "査定", "count": 5, "desc": "査定業務", "priority": "high", "estimated_minutes": 15},
        ]
    
    bulk_create_tasks(assignments, args.date)


if __name__ == "__main__":
    main()
