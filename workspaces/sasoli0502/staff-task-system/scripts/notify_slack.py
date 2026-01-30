#!/usr/bin/env python3
"""
Slack通知ツール

チェックポイント時の進捗遅延や重要なイベントをSlackに通知します。

前提条件:
    - 環境変数にSlack Webhook URLが設定されていること
      SLACK_WEBHOOK_URL

使い方:
    # チェックポイント結果を通知
    python notify_slack.py --checkpoint 14:00

    # カスタムメッセージを通知
    python notify_slack.py --message "【緊急】雜賀さんが欠勤のため、タスクを再割り当てしました"

    # dry-runモード（実際には送信しない）
    python notify_slack.py --checkpoint 14:00 --dry-run
"""

import os
import argparse
import requests
from pathlib import Path
from datetime import datetime
import yaml


# パス設定
BASE_DIR = Path(__file__).parent.parent
TASKS_DIR = BASE_DIR / "tasks" / "active"


def get_slack_webhook_url():
    """環境変数からSlack Webhook URLを取得"""
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')

    if not webhook_url:
        raise ValueError(
            "Slack Webhook URLが環境変数に設定されていません。\n"
            "SLACK_WEBHOOK_URL を設定してください。"
        )

    return webhook_url


def load_task_file(date_str):
    """指定日のタスクファイルを読み込み"""
    task_file = TASKS_DIR / f"{date_str}.yaml"

    if not task_file.exists():
        return None

    with open(task_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def analyze_checkpoint_for_notification(checkpoint_name, date_str):
    """チェックポイント結果を分析して通知用のメッセージを生成"""

    data = load_task_file(date_str)

    if not data:
        return None

    tasks = data.get('tasks', [])

    if not tasks:
        return None

    # スタッフ別進捗を集計
    staff_progress = {}

    for task in tasks:
        assigned_to = task.get('assigned_to')
        if not assigned_to:
            continue

        if assigned_to not in staff_progress:
            staff_progress[assigned_to] = {
                'total': 0,
                'completed': 0,
                'in_progress': 0,
                'pending': 0
            }

        staff_progress[assigned_to]['total'] += 1
        status = task.get('status', 'pending')
        staff_progress[assigned_to][status] = staff_progress[assigned_to].get(status, 0) + 1

    # 進捗率を計算し、遅延を検出
    expected_rate = 50 if checkpoint_name == "14:00" else 100
    alerts = []

    for staff, progress in staff_progress.items():
        if progress['total'] == 0:
            continue

        completed_rate = (progress['completed'] / progress['total']) * 100

        # 大幅遅延（期待値の30%未満）
        if completed_rate < expected_rate * 0.3:
            alerts.append({
                'staff': staff,
                'severity': 'high',
                'message': f"{staff}: 大幅遅延 ({completed_rate:.0f}% / 期待{expected_rate}%)"
            })
        # やや遅延（期待値の70%未満）
        elif completed_rate < expected_rate * 0.7:
            alerts.append({
                'staff': staff,
                'severity': 'medium',
                'message': f"{staff}: やや遅れ ({completed_rate:.0f}% / 期待{expected_rate}%)"
            })

    # 通知メッセージを構築
    if not alerts:
        return {
            'text': f"✅ {checkpoint_name} チェックポイント: 全体的に順調です",
            'color': 'good'
        }

    # 遅延がある場合
    high_alerts = [a for a in alerts if a['severity'] == 'high']
    medium_alerts = [a for a in alerts if a['severity'] == 'medium']

    message_lines = [f"⚠️ {checkpoint_name} チェックポイント - 遅延検出"]

    if high_alerts:
        message_lines.append("\n🚨 *大幅遅延*:")
        for alert in high_alerts:
            message_lines.append(f"  • {alert['message']}")

    if medium_alerts:
        message_lines.append("\n⚠️ *やや遅延*:")
        for alert in medium_alerts:
            message_lines.append(f"  • {alert['message']}")

    return {
        'text': '\n'.join(message_lines),
        'color': 'danger' if high_alerts else 'warning'
    }


def send_slack_notification(webhook_url, message, color='good', dry_run=False):
    """Slackに通知を送信"""

    payload = {
        'attachments': [
            {
                'text': message,
                'color': color,
                'footer': 'スタッフタスク管理システム',
                'ts': int(datetime.now().timestamp())
            }
        ]
    }

    if dry_run:
        print("\n📤 [DRY-RUN] 以下のメッセージを送信します:")
        print(f"  色: {color}")
        print(f"  内容:\n{message}")
        return True

    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Slack通知エラー: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Slack通知ツール')
    parser.add_argument('--checkpoint', choices=['14:00', '17:00'], help='チェックポイント時刻')
    parser.add_argument('--message', help='カスタムメッセージ')
    parser.add_argument('--date', help='対象日（YYYY-MM-DD）。省略時は今日')
    parser.add_argument('--dry-run', action='store_true', help='実際には送信しない')

    args = parser.parse_args()

    if not args.checkpoint and not args.message:
        parser.error("--checkpoint または --message を指定してください")

    # 日付設定
    date_str = args.date if args.date else datetime.now().strftime("%Y-%m-%d")

    # Webhook URL取得
    try:
        webhook_url = get_slack_webhook_url()
    except ValueError as e:
        print(f"❌ {e}")
        return

    # メッセージ生成
    if args.checkpoint:
        print(f"📊 {args.checkpoint} チェックポイント結果を分析中...")
        notification = analyze_checkpoint_for_notification(args.checkpoint, date_str)

        if not notification:
            print(f"⚠️ {date_str}のタスクデータが見つかりませんでした")
            return

        message = notification['text']
        color = notification['color']

    else:
        # カスタムメッセージ
        message = args.message
        color = 'good'

    # 通知送信
    if send_slack_notification(webhook_url, message, color, dry_run=args.dry_run):
        if not args.dry_run:
            print("✅ Slack通知を送信しました")
    else:
        print("❌ Slack通知の送信に失敗しました")


if __name__ == "__main__":
    main()
