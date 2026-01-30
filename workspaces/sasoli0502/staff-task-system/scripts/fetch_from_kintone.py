#!/usr/bin/env python3
"""
Kintone連携ツール

Kintoneから朝の集計データ（査定待ち、修理必要、出品可能、未返信）を自動取得します。

前提条件:
    - 環境変数にKintone認証情報が設定されていること
      KINTONE_DOMAIN, KINTONE_APP_ID, KINTONE_API_TOKEN

使い方:
    # 今日のデータを取得
    python fetch_from_kintone.py

    # 指定日のデータを取得
    python fetch_from_kintone.py --date 2025-10-15

    # dry-runモード（データ取得のみ、保存しない）
    python fetch_from_kintone.py --dry-run
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


def get_kintone_credentials():
    """環境変数からKintone認証情報を取得"""
    domain = os.getenv('KINTONE_DOMAIN')
    app_id = os.getenv('KINTONE_APP_ID')
    api_token = os.getenv('KINTONE_API_TOKEN')

    if not all([domain, app_id, api_token]):
        raise ValueError(
            "Kintone認証情報が環境変数に設定されていません。\n"
            "以下の環境変数を設定してください:\n"
            "  - KINTONE_DOMAIN (例: example.cybozu.com)\n"
            "  - KINTONE_APP_ID (例: 123)\n"
            "  - KINTONE_API_TOKEN"
        )

    return {
        'domain': domain,
        'app_id': app_id,
        'api_token': api_token
    }


def fetch_daily_summary(date_str, credentials):
    """Kintoneから指定日の集計データを取得"""

    # Kintone REST API エンドポイント
    url = f"https://{credentials['domain']}/k/v1/records.json"

    # ヘッダー
    headers = {
        'X-Cybozu-API-Token': credentials['api_token'],
        'Content-Type': 'application/json'
    }

    # クエリ（指定日のレコードを取得）
    query = f'日付 = "{date_str}"'

    params = {
        'app': credentials['app_id'],
        'query': query
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        records = data.get('records', [])

        if not records:
            print(f"⚠️ {date_str}のデータがKintoneに見つかりませんでした")
            return None

        # 最初のレコードを使用（通常1日1レコード）
        record = records[0]

        # フィールドから値を抽出
        # NOTE: フィールド名は実際のKintoneアプリに合わせて調整してください
        summary = {
            'satei_waiting': int(record.get('査定待ち', {}).get('value', 0)),
            'shuri_needed': int(record.get('修理必要', {}).get('value', 0)),
            'shuppin_ready': int(record.get('出品可能', {}).get('value', 0)),
            'hensin_pending': int(record.get('未返信', {}).get('value', 0))
        }

        summary['total_workload'] = sum(summary.values())

        return summary

    except requests.exceptions.RequestException as e:
        print(f"❌ Kintone APIエラー: {e}")
        return None


def save_morning_summary(date_str, summary):
    """朝の集計データをYAMLファイルに保存"""

    task_file = TASKS_DIR / f"{date_str}.yaml"

    # 既存ファイルを読み込み
    if task_file.exists():
        with open(task_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
    else:
        # 新規作成
        data = {
            'date': date_str,
            'tasks': [],
            'feedback_history': []
        }

    # 朝の集計データを更新
    data['morning_summary'] = {
        'input_at': datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        'source': 'kintone',
        **summary
    }

    # ファイルに保存
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    with open(task_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

    return task_file


def main():
    parser = argparse.ArgumentParser(description='Kintoneから朝の集計データを取得')
    parser.add_argument('--date', help='取得する日付（YYYY-MM-DD形式）。省略時は今日')
    parser.add_argument('--dry-run', action='store_true', help='データ取得のみ（保存しない）')

    args = parser.parse_args()

    # 日付設定
    if args.date:
        date_str = args.date
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"📅 対象日: {date_str}")

    # 認証情報取得
    try:
        credentials = get_kintone_credentials()
    except ValueError as e:
        print(f"❌ {e}")
        return

    # データ取得
    print("🔄 Kintoneからデータを取得中...")
    summary = fetch_daily_summary(date_str, credentials)

    if not summary:
        return

    # 結果表示
    print("\n✅ データ取得成功")
    print(f"  査定待ち: {summary['satei_waiting']}台")
    print(f"  修理必要: {summary['shuri_needed']}台")
    print(f"  出品可能: {summary['shuppin_ready']}台")
    print(f"  未返信: {summary['hensin_pending']}件")
    print(f"  合計作業量: {summary['total_workload']}件")

    # dry-runモードでなければ保存
    if not args.dry_run:
        print("\n💾 タスクファイルに保存中...")
        task_file = save_morning_summary(date_str, summary)
        print(f"✅ 保存完了: {task_file}")
    else:
        print("\n⏭️  dry-runモードのため保存をスキップしました")


if __name__ == "__main__":
    main()
