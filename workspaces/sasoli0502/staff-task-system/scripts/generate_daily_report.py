#!/usr/bin/env python3
"""
日報自動生成スクリプト

1日の作業サマリーを自動作成
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import yaml

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent


def generate_daily_report(date_str=None):
    """日報を自動生成"""
    
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    task_file = project_root / "tasks" / "active" / f"{date_str}.yaml"
    
    if not task_file.exists():
        print(f"❌ エラー: タスクファイルが見つかりません: {task_file}")
        sys.exit(1)
    
    with open(task_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    tasks = data.get('tasks', [])
    morning_summary = data.get('morning_summary', {})
    feedbacks = data.get('feedbacks', [])
    
    # 日報ヘッダー
    print("=" * 70)
    print(f"📋 日報 - {date_str}")
    print("=" * 70)
    print()
    
    # 1. 朝の計画
    if morning_summary:
        print("## 📊 朝の計画")
        print()
        print(f"  査定待ち: {morning_summary.get('satei_waiting', 0)}台")
        print(f"  修理必要: {morning_summary.get('shuri_needed', 0)}台")
        print(f"  出品可能: {morning_summary.get('shuppin_ready', 0)}台")
        print(f"  未返信: {morning_summary.get('hensin_pending', 0)}件")
        print(f"  **計画作業量: {morning_summary.get('total_workload', 0)}件**")
        print()
    
    # 2. 全体実績
    completed_tasks = [t for t in tasks if t.get('status') == 'completed']
    in_progress_tasks = [t for t in tasks if t.get('status') == 'in_progress']
    pending_tasks = [t for t in tasks if t.get('status') == 'pending']
    
    total_actual_minutes = sum(t.get('actual_minutes', 0) for t in completed_tasks)
    total_estimated_minutes = sum(t.get('estimated_minutes', 0) for t in tasks)
    
    completion_rate = len(completed_tasks) / len(tasks) * 100 if tasks else 0
    
    print("## 📈 全体実績")
    print()
    print(f"  完了: {len(completed_tasks)}件")
    print(f"  進行中: {len(in_progress_tasks)}件")
    print(f"  未着手: {len(pending_tasks)}件")
    print(f"  **合計: {len(tasks)}タスク**")
    print()
    print(f"  完了率: {completion_rate:.1f}%")
    print(f"  実績時間: {total_actual_minutes}分 ({total_actual_minutes // 60}時間{total_actual_minutes % 60}分)")
    print()
    
    # 3. スタッフ別実績
    staff_stats = defaultdict(lambda: {
        'completed': 0,
        'in_progress': 0,
        'pending': 0,
        'total_actual_minutes': 0,
        'completed_tasks': []
    })
    
    for task in tasks:
        staff = task.get('assigned_to', '未割当')
        status = task.get('status')
        
        if status == 'completed':
            staff_stats[staff]['completed'] += 1
            staff_stats[staff]['total_actual_minutes'] += task.get('actual_minutes', 0)
            staff_stats[staff]['completed_tasks'].append(task)
        elif status == 'in_progress':
            staff_stats[staff]['in_progress'] += 1
        elif status == 'pending':
            staff_stats[staff]['pending'] += 1
    
    print("## 👥 スタッフ別実績")
    print()
    
    for staff in sorted(staff_stats.keys(), key=lambda x: (x is None, x)):
        stats = staff_stats[staff]
        total = stats['completed'] + stats['in_progress'] + stats['pending']
        actual_minutes = stats['total_actual_minutes']
        
        print(f"### {staff}")
        print(f"  完了: {stats['completed']}件 / 合計: {total}件")
        
        if stats['completed'] > 0:
            avg_time = actual_minutes / stats['completed']
            print(f"  実績時間: {actual_minutes}分（平均: {avg_time:.1f}分/件）")
        
        if stats['in_progress'] > 0:
            print(f"  ⚠️ 進行中タスク: {stats['in_progress']}件（要確認）")
        
        print()
    
    # 4. タスク種別別の実績
    type_stats = defaultdict(lambda: {
        'completed': 0,
        'total': 0,
        'total_actual_minutes': 0
    })
    
    for task in tasks:
        task_type = task.get('type', '不明')
        type_stats[task_type]['total'] += 1
        
        if task.get('status') == 'completed':
            type_stats[task_type]['completed'] += 1
            type_stats[task_type]['total_actual_minutes'] += task.get('actual_minutes', 0)
    
    print("## 📦 タスク種別別実績")
    print()
    
    for task_type in sorted(type_stats.keys()):
        stats = type_stats[task_type]
        completion_rate = stats['completed'] / stats['total'] * 100 if stats['total'] > 0 else 0
        
        print(f"### {task_type}")
        print(f"  完了: {stats['completed']}件 / 合計: {stats['total']}件 ({completion_rate:.1f}%)")
        
        if stats['completed'] > 0:
            avg_time = stats['total_actual_minutes'] / stats['completed']
            print(f"  平均処理時間: {avg_time:.1f}分/件")
        
        print()
    
    # 5. フィードバック履歴
    if feedbacks:
        print("## 💬 フィードバック履歴")
        print()
        
        for fb in feedbacks:
            timestamp = datetime.fromisoformat(fb['timestamp'].replace('+09:00', ''))
            print(f"- **{fb['staff']}** ({timestamp.strftime('%H:%M')})")
            print(f"  {fb['content']}")
            print()
    
    # 6. 未完了タスク（翌日引き継ぎ）
    carryover_tasks = [t for t in tasks if t.get('status') in ['pending', 'in_progress']]
    
    if carryover_tasks:
        print("## 📌 翌日引き継ぎ（未完了タスク）")
        print()
        
        # スタッフ別に集計
        carryover_by_staff = defaultdict(list)
        for task in carryover_tasks:
            staff = task.get('assigned_to', '未割当')
            carryover_by_staff[staff].append(task)
        
        for staff in sorted(carryover_by_staff.keys(), key=lambda x: (x is None, x)):
            staff_tasks = carryover_by_staff[staff]
            print(f"### {staff} ({len(staff_tasks)}件)")
            
            for task in staff_tasks[:5]:  # 最大5件まで表示
                status_icon = "🔄" if task.get('status') == 'in_progress' else "⏳"
                print(f"  {status_icon} {task.get('id')} - {task.get('description', '説明なし')}")
            
            if len(staff_tasks) > 5:
                print(f"  ... 他{len(staff_tasks) - 5}件")
            
            print()
    
    # 7. 所感・改善点
    print("## 📝 所感・改善点")
    print()
    
    # 自動分析
    issues = []
    
    # 完了率が低い
    if completion_rate < 50:
        issues.append(f"⚠️ 完了率が低い（{completion_rate:.1f}%）- タスク量の見直しが必要")
    
    # 進行中タスクが多い
    if len(in_progress_tasks) > 3:
        issues.append(f"⚠️ 進行中タスクが多い（{len(in_progress_tasks)}件）- タスクが滞留している可能性")
    
    # 未割当タスク
    unassigned = [t for t in tasks if not t.get('assigned_to') or t.get('assigned_to') == '未割当']
    if unassigned:
        issues.append(f"⚠️ 未割当タスクあり（{len(unassigned)}件）")
    
    if issues:
        for issue in issues:
            print(f"  {issue}")
        print()
    else:
        print("  ✅ 特に問題なし。順調に進んでいます。")
        print()
    
    # フッター
    print("=" * 70)
    print(f"作成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="日報を自動生成")
    parser.add_argument('--date', help='対象日 (YYYY-MM-DD形式、省略時は今日)')
    parser.add_argument('--output', help='出力ファイルパス（省略時は標準出力）')
    
    args = parser.parse_args()
    
    if args.output:
        # ファイルに出力
        import sys
        sys.stdout = open(args.output, 'w', encoding='utf-8')
    
    generate_daily_report(args.date)


if __name__ == "__main__":
    main()
