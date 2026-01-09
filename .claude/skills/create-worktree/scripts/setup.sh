#!/bin/bash
set -e

PROJECT=$1
BRANCH=$2
WORKSPACE_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

# 引数チェック
if [ -z "$PROJECT" ] || [ -z "$BRANCH" ]; then
    echo "Usage: setup.sh <project-name> <branch-name>"
    exit 1
fi

PROJECT_DIR="$WORKSPACE_ROOT/projects/$PROJECT"
WORKTREE_DIR="$PROJECT_DIR/worktrees/$BRANCH"

# プロジェクト存在確認
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: Project '$PROJECT' not found in projects/"
    exit 1
fi

# 既存ワークツリー確認
if [ -d "$WORKTREE_DIR" ]; then
    echo "Error: Worktree '$BRANCH' already exists"
    exit 1
fi

# ディレクトリ作成
mkdir -p "$WORKTREE_DIR"/{.claude,docs,repo}

# CLAUDE.md作成
cat > "$WORKTREE_DIR/CLAUDE.md" << EOF
# $PROJECT - $BRANCH

ブランチ固有の設定をここに記載
EOF

# git worktree追加
cd "$WORKTREE_DIR/repo"
git worktree add . "$BRANCH" 2>/dev/null || git worktree add -b "$BRANCH" .

echo "Created worktree: $WORKTREE_DIR"
echo "Structure:"
ls -la "$WORKTREE_DIR"
