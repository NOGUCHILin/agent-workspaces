#!/bin/bash
set -e

PROJECT=$1
BRANCH=$2
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

# 引数チェック
if [ -z "$PROJECT" ] || [ -z "$BRANCH" ]; then
    echo "Usage: setup.sh <project-name> <branch-name>"
    exit 1
fi

PROJECT_DIR="$WORKSPACE_ROOT/projects/$PROJECT"
WORKTREE_DIR="$PROJECT_DIR/worktrees/$BRANCH"

# プロジェクトがなければ作成
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Creating project: $PROJECT"
    mkdir -p "$PROJECT_DIR/worktrees"
fi

# 既存ワークツリー確認
if [ -d "$WORKTREE_DIR" ]; then
    echo "Error: Worktree '$BRANCH' already exists in project '$PROJECT'"
    exit 1
fi

# ディレクトリ作成
echo "Creating worktree structure..."
mkdir -p "$WORKTREE_DIR"/{.claude,docs/specs,repo}

# CLAUDE.md作成
cat > "$WORKTREE_DIR/CLAUDE.md" << EOF
# $PROJECT - $BRANCH

ブランチ固有の設定をここに記載

## このブランチの目的

（記載してください）

## 作業メモ

（作業中のメモをここに）
EOF

# .mcp.json作成（Playwright MCP設定）
cat > "$WORKTREE_DIR/.mcp.json" << EOF
{
  "mcpServers": {
    "playwright": {
      "command": "bash",
      "args": [
        "$WORKSPACE_ROOT/.claude/scripts/playwright-mcp.sh"
      ]
    }
  }
}
EOF

# git worktree追加
echo "Adding git worktree..."
cd "$WORKTREE_DIR/repo"
if git worktree add . "$BRANCH" 2>/dev/null; then
    echo "Attached to existing branch: $BRANCH"
elif git worktree add -b "$BRANCH" . 2>/dev/null; then
    echo "Created new branch: $BRANCH"
else
    echo "Warning: git worktree add failed. Initialize manually if needed."
fi

# 構造検証
echo ""
echo "Validating structure..."
"$SCRIPT_DIR/validate.sh" "$PROJECT"

echo ""
echo "Done! Created: $WORKTREE_DIR"
