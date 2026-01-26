#!/bin/bash
# 新規ユーザーワークスペースを作成
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
TEMPLATE_DIR="$ROOT_DIR/workspaces/_template"

USERNAME="$1"

if [[ -z "$USERNAME" ]]; then
  echo "Usage: $0 <username>"
  exit 1
fi

WORKSPACE_DIR="$ROOT_DIR/workspaces/$USERNAME"

if [[ -d "$WORKSPACE_DIR" ]]; then
  echo "Error: Workspace already exists: $WORKSPACE_DIR"
  exit 1
fi

# テンプレートをコピー
cp -r "$TEMPLATE_DIR" "$WORKSPACE_DIR"

# CLAUDE.mdのプレースホルダーを置換
sed -i '' "s/{username}/$USERNAME/g" "$WORKSPACE_DIR/CLAUDE.md"

echo "Created workspace: $WORKSPACE_DIR"
echo "Next: cd $WORKSPACE_DIR && ../scripts/add-repo.sh <repo-url>"
