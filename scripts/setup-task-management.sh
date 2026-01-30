#!/bin/bash
# ワークスペースにタスク管理ルールを追加するスクリプト
# Usage: ./scripts/setup-task-management.sh <username> <staff_name>
# Example: ./scripts/setup-task-management.sh eguchinatsu "江口那都"
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
TEMPLATE="$ROOT_DIR/_shared/templates/task-management.md"

USERNAME="$1"
STAFF_NAME="$2"

if [[ -z "$USERNAME" || -z "$STAFF_NAME" ]]; then
  echo "Usage: $0 <username> <staff_name>"
  echo "Example: $0 eguchinatsu \"江口那都\""
  exit 1
fi

CLAUDE_MD="$ROOT_DIR/workspaces/$USERNAME/CLAUDE.md"

if [[ ! -f "$CLAUDE_MD" ]]; then
  echo "Error: CLAUDE.md not found: $CLAUDE_MD"
  exit 1
fi

# 既にタスク管理ルールが存在する場合はスキップ
if grep -q '<task-reminder>' "$CLAUDE_MD"; then
  echo "Skip: task-reminder already exists in $CLAUDE_MD"
  exit 0
fi

# テンプレートを読み込み、プレースホルダーを置換して追記
echo "" >> "$CLAUDE_MD"
sed "s/{staff_name}/$STAFF_NAME/g" "$TEMPLATE" >> "$CLAUDE_MD"

echo "Done: Added task management to $CLAUDE_MD ($STAFF_NAME)"
