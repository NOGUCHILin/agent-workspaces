#!/usr/bin/env python3
"""
朝の集計データ表示スクリプト
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
import yaml

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent


def show_morning_summary(date_str=None):
    """朝の集計データを表示"""
    
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    task_file = project_root / "tasks" / "active" / f"{date_str}.yaml"
    
    if not task_file.exists():
        print(f"❌ エラー: タスクファイルが見つかりません: {task_file}")
        sys.exit(1)
    
    with open(task_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if 'morning_summary' not in data:
        print("=" * 60)
        print(f"📅 {date_str}")
        print("=" * 60)
        print()
        print("⚠️ 朝の集計データが入力されていません")
        print()
        print("💡 入力するには:")
        print("   uv run python scripts/input_morning_summary.py")
        print()
        return
    
    summary = data['morning_summary']
    
    print("=" * 60)
    print(f"📊 朝の集計 - {date_str}")
    print("=" * 60)
    print()
    
    if 'input_at' in summary:
        input_time = datetime.fromisoformat(summary['input_at'].replace('+09:00', ''))
        print(f"📅 入力日時: {input_time.strftime('%Y年%m月%d日 %H:%M')}")
        print()
    
    print("📱 作業待ち状況:")
    print(f"  査定待ち: {summary.get('satei_waiting', 0)}台")
    print(f"  修理必要: {summary.get('shuri_needed', 0)}台")
    print(f"  出品可能: {summary.get('shuppin_ready', 0)}台")
    print(f"  未返信: {summary.get('hensin_pending', 0)}件")
    print()
    print(f"📊 合計作業量: {summary.get('total_workload', 0)}件")
    print()
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="朝の集計データを表示")
    parser.add_argument('--date', help='対象日 (YYYY-MM-DD形式、省略時は今日)')
    
    args = parser.parse_args()
    
    show_morning_summary(args.date)


if __name__ == "__main__":
    main()
