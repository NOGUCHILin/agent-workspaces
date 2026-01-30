#!/usr/bin/env python3
"""
フィードバック記録スクリプト

チェックポイント後のフィードバックを記録
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
import yaml

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent


def add_feedback(staff_name, feedback_text, date_str=None):
    """フィードバックを記録"""
    
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    task_file = project_root / "tasks" / "active" / f"{date_str}.yaml"
    
    if not task_file.exists():
        print(f"❌ エラー: タスクファイルが見つかりません: {task_file}")
        sys.exit(1)
    
    with open(task_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # feedbacksセクションがなければ作成
    if 'feedbacks' not in data:
        data['feedbacks'] = []
    
    feedback_entry = {
        'staff': staff_name,
        'timestamp': datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        'content': feedback_text
    }
    
    data['feedbacks'].append(feedback_entry)
    
    # YAMLファイルに保存
    with open(task_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    print("=" * 60)
    print("✅ フィードバックを記録しました")
    print("=" * 60)
    print()
    print(f"👤 {staff_name}")
    print(f"📝 {feedback_text}")
    print()
    
    # 過去のフィードバックを表示
    staff_feedbacks = [f for f in data['feedbacks'] if f['staff'] == staff_name]
    
    if len(staff_feedbacks) > 1:
        print("=" * 60)
        print(f"【フィードバック履歴 - {staff_name}】")
        print("=" * 60)
        for fb in staff_feedbacks:
            timestamp = datetime.fromisoformat(fb['timestamp'].replace('+09:00', ''))
            print(f"{timestamp.strftime('%H:%M')} - {fb['content']}")
        print()


def main():
    parser = argparse.ArgumentParser(description="フィードバックを記録")
    parser.add_argument('staff', help='スタッフ名')
    parser.add_argument('feedback', help='フィードバック内容')
    parser.add_argument('--date', help='対象日 (YYYY-MM-DD形式、省略時は今日)')
    
    args = parser.parse_args()
    
    add_feedback(args.staff, args.feedback, args.date)


if __name__ == "__main__":
    main()
