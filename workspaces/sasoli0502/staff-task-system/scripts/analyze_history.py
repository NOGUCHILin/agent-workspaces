#!/usr/bin/env python3
"""
作業履歴分析ツール

過去の日報データを集計して週次・月次のパフォーマンス分析を提供します。

使い方:
    # 直近1週間
    python analyze_history.py --period week

    # 直近1ヶ月
    python analyze_history.py --period month

    # カスタム期間
    python analyze_history.py --from 2025-10-01 --to 2025-10-15
"""

import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import yaml

# パス設定
BASE_DIR = Path(__file__).parent.parent
TASKS_DIR = BASE_DIR / "tasks" / "active"


def load_task_file(date_str):
    """指定日のタスクファイルを読み込み"""
    task_file = TASKS_DIR / f"{date_str}.yaml"
    if not task_file.exists():
        return None

    with open(task_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_date_range(args):
    """分析対象の日付範囲を取得"""
    today = datetime.now()

    if args.period == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
    elif args.period == 'month':
        start_date = today - timedelta(days=30)
        end_date = today
    else:
        # カスタム範囲
        start_date = datetime.strptime(args.from_date, "%Y-%m-%d")
        end_date = datetime.strptime(args.to_date, "%Y-%m-%d")

    return start_date, end_date


def analyze_period(start_date, end_date):
    """期間内の全タスクデータを分析"""

    # 集計用データ構造
    stats = {
        'total_days': 0,
        'total_tasks': 0,
        'completed_tasks': 0,
        'total_time_minutes': 0,
        'staff_stats': defaultdict(lambda: {
            'completed': 0,
            'total': 0,
            'time_minutes': 0,
            'by_type': defaultdict(lambda: {'completed': 0, 'total': 0, 'time': 0})
        }),
        'type_stats': defaultdict(lambda: {
            'completed': 0,
            'total': 0,
            'time_minutes': 0,
            'completion_rate': 0.0
        }),
        'daily_completion_rates': [],
        'feedback_count': 0,
        'absence_days': []
    }

    # 日付ごとにデータを集計
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        data = load_task_file(date_str)

        if data:
            stats['total_days'] += 1
            tasks = data.get('tasks', [])

            # 日次の完了率を計算
            completed_count = len([t for t in tasks if t.get('status') == 'completed'])
            total_count = len(tasks)
            if total_count > 0:
                daily_rate = (completed_count / total_count) * 100
                stats['daily_completion_rates'].append(daily_rate)

            # タスクごとに集計
            for task in tasks:
                task_type = task.get('type', '不明')
                assigned_to = task.get('assigned_to')
                status = task.get('status', 'pending')
                actual_minutes = task.get('actual_minutes', 0)

                stats['total_tasks'] += 1

                # 完了タスク
                if status == 'completed':
                    stats['completed_tasks'] += 1
                    stats['total_time_minutes'] += actual_minutes

                    # タスク種別別
                    stats['type_stats'][task_type]['completed'] += 1
                    stats['type_stats'][task_type]['time_minutes'] += actual_minutes

                # 全タスク（種別別）
                stats['type_stats'][task_type]['total'] += 1

                # スタッフ別
                if assigned_to:
                    staff = stats['staff_stats'][assigned_to]
                    staff['total'] += 1

                    if status == 'completed':
                        staff['completed'] += 1
                        staff['time_minutes'] += actual_minutes

                    # スタッフ×タスク種別
                    staff['by_type'][task_type]['total'] += 1
                    if status == 'completed':
                        staff['by_type'][task_type]['completed'] += 1
                        staff['by_type'][task_type]['time'] += actual_minutes

            # フィードバック件数
            feedback_history = data.get('feedback_history', [])
            stats['feedback_count'] += len(feedback_history)

            # 欠勤記録
            absences = data.get('absences', [])
            for absence in absences:
                stats['absence_days'].append({
                    'date': date_str,
                    'staff': absence.get('staff'),
                    'reason': absence.get('reason')
                })

        current_date += timedelta(days=1)

    # 完了率を計算
    for task_type, type_data in stats['type_stats'].items():
        if type_data['total'] > 0:
            type_data['completion_rate'] = (type_data['completed'] / type_data['total']) * 100

    return stats


def print_analysis(stats, start_date, end_date):
    """分析結果を表示"""

    print("=" * 70)
    print(f"📊 作業履歴分析レポート")
    print(f"期間: {start_date.strftime('%Y-%m-%d')} 〜 {end_date.strftime('%Y-%m-%d')}")
    print("=" * 70)

    # 全体サマリー
    print(f"\n## 📈 全体サマリー\n")
    print(f"  分析対象日数: {stats['total_days']}日")
    print(f"  総タスク数: {stats['total_tasks']}件")
    print(f"  完了タスク: {stats['completed_tasks']}件")

    if stats['total_tasks'] > 0:
        overall_rate = (stats['completed_tasks'] / stats['total_tasks']) * 100
        print(f"  全体完了率: {overall_rate:.1f}%")

    if stats['completed_tasks'] > 0:
        avg_time = stats['total_time_minutes'] / stats['completed_tasks']
        total_hours = stats['total_time_minutes'] / 60
        print(f"  総作業時間: {total_hours:.1f}時間（{stats['total_time_minutes']}分）")
        print(f"  平均処理時間: {avg_time:.1f}分/件")

    # 日次完了率のトレンド
    if stats['daily_completion_rates']:
        avg_daily_rate = sum(stats['daily_completion_rates']) / len(stats['daily_completion_rates'])
        min_rate = min(stats['daily_completion_rates'])
        max_rate = max(stats['daily_completion_rates'])
        print(f"\n  日次完了率: 平均{avg_daily_rate:.1f}% (最低{min_rate:.1f}% / 最高{max_rate:.1f}%)")

    # タスク種別別実績
    print(f"\n## 📦 タスク種別別実績\n")

    type_stats_sorted = sorted(
        stats['type_stats'].items(),
        key=lambda x: x[1]['completed'],
        reverse=True
    )

    for task_type, type_data in type_stats_sorted:
        print(f"### {task_type}")
        print(f"  完了: {type_data['completed']}件 / {type_data['total']}件 ({type_data['completion_rate']:.1f}%)")

        if type_data['completed'] > 0:
            avg_time = type_data['time_minutes'] / type_data['completed']
            print(f"  平均処理時間: {avg_time:.1f}分/件")
        print()

    # スタッフ別実績
    print(f"## 👥 スタッフ別実績\n")

    staff_stats_sorted = sorted(
        stats['staff_stats'].items(),
        key=lambda x: x[1]['completed'],
        reverse=True
    )

    for staff, staff_data in staff_stats_sorted:
        completion_rate = 0
        if staff_data['total'] > 0:
            completion_rate = (staff_data['completed'] / staff_data['total']) * 100

        print(f"### {staff}")
        print(f"  完了: {staff_data['completed']}件 / {staff_data['total']}件 ({completion_rate:.1f}%)")

        if staff_data['completed'] > 0:
            avg_time = staff_data['time_minutes'] / staff_data['completed']
            total_hours = staff_data['time_minutes'] / 60
            print(f"  総作業時間: {total_hours:.1f}時間")
            print(f"  平均処理時間: {avg_time:.1f}分/件")

        # タスク種別別の内訳
        print(f"  タスク種別別:")
        for task_type, type_data in staff_data['by_type'].items():
            if type_data['total'] > 0:
                type_rate = (type_data['completed'] / type_data['total']) * 100
                print(f"    - {task_type}: {type_data['completed']}/{type_data['total']}件 ({type_rate:.1f}%)", end="")

                if type_data['completed'] > 0:
                    type_avg_time = type_data['time'] / type_data['completed']
                    print(f" - 平均{type_avg_time:.1f}分")
                else:
                    print()
        print()

    # フィードバック統計
    print(f"## 💬 フィードバック統計\n")
    print(f"  総フィードバック数: {stats['feedback_count']}件")
    if stats['total_days'] > 0:
        fb_per_day = stats['feedback_count'] / stats['total_days']
        print(f"  平均: {fb_per_day:.1f}件/日")

    # 欠勤統計
    if stats['absence_days']:
        print(f"\n## 🏥 欠勤記録\n")
        print(f"  総欠勤日数: {len(stats['absence_days'])}日")

        for absence in stats['absence_days']:
            print(f"  - {absence['date']}: {absence['staff']} ({absence['reason']})")

    print("\n" + "=" * 70)
    print(f"作成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description='作業履歴分析ツール')
    parser.add_argument('--period', choices=['week', 'month'], help='分析期間（week=1週間, month=1ヶ月）')
    parser.add_argument('--from', dest='from_date', help='開始日（YYYY-MM-DD）')
    parser.add_argument('--to', dest='to_date', help='終了日（YYYY-MM-DD）')

    args = parser.parse_args()

    # 引数の検証
    if not args.period and not (args.from_date and args.to_date):
        parser.error("--period または --from と --to を指定してください")

    if args.period and (args.from_date or args.to_date):
        parser.error("--period と --from/--to は同時に指定できません")

    # 日付範囲を取得
    start_date, end_date = get_date_range(args)

    # 分析実行
    stats = analyze_period(start_date, end_date)

    # 結果表示
    print_analysis(stats, start_date, end_date)


if __name__ == "__main__":
    main()
