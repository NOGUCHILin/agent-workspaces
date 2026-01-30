#!/usr/bin/env python3
"""
CLAUDE.md のタスクをTodoistに同期するスクリプト

使い方:
1. 環境変数にTODOIST_API_TOKENを設定
2. uv run python work/misc-tasks/todoist-sync/sync_tasks.py
"""

import os
import re
import sys
from pathlib import Path
import requests
from typing import List, Dict
from dotenv import load_dotenv

# .envファイルを読み込み
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Todoist API設定
TODOIST_API_TOKEN = os.environ.get("TODOIST_API_TOKEN")
TODOIST_API_URL = "https://api.todoist.com/rest/v2"

# CLAUDE.mdのパス
CLAUDE_MD_PATH = Path(__file__).parent.parent.parent / "CLAUDE.md"

def get_todoist_headers() -> Dict[str, str]:
    """Todoist APIリクエストヘッダーを取得"""
    if not TODOIST_API_TOKEN:
        raise ValueError("環境変数 TODOIST_API_TOKEN が設定されていません")
    return {
        "Authorization": f"Bearer {TODOIST_API_TOKEN}",
        "Content-Type": "application/json"
    }

def parse_tasks_from_claude_md() -> List[Dict[str, str]]:
    """CLAUDE.mdから未完了タスクを抽出"""
    if not CLAUDE_MD_PATH.exists():
        raise FileNotFoundError(f"CLAUDE.md が見つかりません: {CLAUDE_MD_PATH}")

    with open(CLAUDE_MD_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # <pending-tasks>セクションを抽出
    match = re.search(r'<pending-tasks>(.*?)</pending-tasks>', content, re.DOTALL)
    if not match:
        print("⚠️  <pending-tasks>セクションが見つかりません")
        return []

    pending_section = match.group(1)

    # タスクを抽出（番号付きリストから）
    tasks = []
    current_category = None

    for line in pending_section.split('\n'):
        # カテゴリを検出
        if line.startswith('### '):
            current_category = line.replace('### ', '').strip()
            continue

        # タスクを検出（1. から始まる行）
        task_match = re.match(r'^\d+\.\s+\*\*(.*?)\*\*', line)
        if task_match and current_category and current_category != "（タスクなし）":
            task_text = task_match.group(1)

            # 優先度を判定
            priority = 1  # デフォルト（低優先度）
            if "【最優先】" in task_text:
                priority = 4  # 最優先
            elif "【優先】" in task_text:
                priority = 3  # 優先

            # タグを削除してタスク名を整形
            clean_task_text = re.sub(r'【.*?】', '', task_text).strip()

            tasks.append({
                "content": f"[{current_category}] {clean_task_text}",
                "priority": priority,
                "labels": [current_category.split('・')[0]]  # 最初の人名をラベルに
            })

    return tasks

def get_todoist_tasks() -> List[Dict]:
    """Todoistから既存タスクを取得"""
    headers = get_todoist_headers()
    response = requests.get(f"{TODOIST_API_URL}/tasks", headers=headers)
    response.raise_for_status()
    return response.json()

def create_todoist_task(task: Dict[str, str]) -> None:
    """Todoistにタスクを作成"""
    headers = get_todoist_headers()
    response = requests.post(
        f"{TODOIST_API_URL}/tasks",
        headers=headers,
        json=task
    )
    response.raise_for_status()
    print(f"✓ タスク作成: {task['content']}")

def delete_todoist_task(task_id: str) -> None:
    """Todoistからタスクを削除"""
    headers = get_todoist_headers()
    response = requests.delete(
        f"{TODOIST_API_URL}/tasks/{task_id}",
        headers=headers
    )
    response.raise_for_status()
    print(f"✓ タスク削除: {task_id}")

def sync_tasks() -> None:
    """CLAUDE.mdとTodoistを同期"""
    print("🔄 タスク同期を開始...")

    # CLAUDE.mdからタスクを取得
    claude_tasks = parse_tasks_from_claude_md()
    print(f"📋 CLAUDE.mdから {len(claude_tasks)} 件のタスクを検出")

    # Todoistから既存タスクを取得
    todoist_tasks = get_todoist_tasks()
    print(f"📱 Todoistに {len(todoist_tasks)} 件のタスクが存在")

    # タスク内容のセットを作成
    claude_task_contents = {task["content"] for task in claude_tasks}
    todoist_task_map = {task["content"]: task["id"] for task in todoist_tasks}

    # 新規タスクを作成
    for task in claude_tasks:
        if task["content"] not in todoist_task_map:
            create_todoist_task(task)

    # 削除されたタスクをTodoistから削除
    for content, task_id in todoist_task_map.items():
        if content not in claude_task_contents:
            delete_todoist_task(task_id)

    print("✅ 同期完了！")

if __name__ == "__main__":
    try:
        sync_tasks()
    except Exception as e:
        print(f"❌ エラー: {e}", file=sys.stderr)
        sys.exit(1)
