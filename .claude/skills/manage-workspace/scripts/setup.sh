#!/bin/bash
set -e

PROJECT=$1
BRANCH=$2
REPO_URL=$3
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

# 引数チェック
if [ -z "$PROJECT" ] || [ -z "$BRANCH" ]; then
    echo "Usage: setup.sh <project-name> <branch-name> [repo-url]"
    echo ""
    echo "Examples:"
    echo "  # 新規プロジェクト（clone）"
    echo "  setup.sh myproject master https://github.com/user/myproject.git"
    echo ""
    echo "  # 既存プロジェクトに worktree 追加"
    echo "  setup.sh myproject feature-x"
    exit 1
fi

PROJECT_DIR="$WORKSPACE_ROOT/projects/$PROJECT"
WORKTREE_DIR="$PROJECT_DIR/worktrees/$BRANCH"

# 既存ワークツリー確認
if [ -d "$WORKTREE_DIR" ]; then
    echo "Error: Worktree '$BRANCH' already exists in project '$PROJECT'"
    exit 1
fi

# プロジェクト内の既存worktreeを探す（.gitがあるディレクトリ）
find_main_repo() {
    for dir in "$PROJECT_DIR"/worktrees/*/repo; do
        if [ -d "$dir/.git" ] || [ -f "$dir/.git" ]; then
            echo "$dir"
            return 0
        fi
    done
    return 1
}

MAIN_REPO=$(find_main_repo || echo "")

# ディレクトリ作成
echo "Creating worktree structure..."
mkdir -p "$WORKTREE_DIR"/{.claude,docs/specs}

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

# Git操作
if [ -z "$MAIN_REPO" ]; then
    # 最初のworktree → clone必要
    if [ -z "$REPO_URL" ]; then
        echo ""
        echo "Error: This is the first worktree for project '$PROJECT'."
        echo "Please provide the repository URL:"
        echo ""
        echo "  setup.sh $PROJECT $BRANCH <repo-url>"
        echo ""
        # 作成したディレクトリを削除
        rm -rf "$WORKTREE_DIR"
        exit 1
    fi

    echo "Cloning repository..."
    git clone "$REPO_URL" "$WORKTREE_DIR/repo"

    # 指定ブランチに切り替え
    cd "$WORKTREE_DIR/repo"
    if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
        git checkout "$BRANCH"
    elif git show-ref --verify --quiet "refs/remotes/origin/$BRANCH"; then
        git checkout -b "$BRANCH" "origin/$BRANCH"
    else
        echo "Note: Branch '$BRANCH' not found, staying on default branch"
    fi
else
    # 既存repoからworktree作成
    echo "Creating worktree from: $MAIN_REPO"
    mkdir -p "$WORKTREE_DIR/repo"

    cd "$MAIN_REPO"

    # リモートから最新情報取得
    git fetch --all 2>/dev/null || true

    # worktree追加
    if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
        git worktree add "$WORKTREE_DIR/repo" "$BRANCH"
        echo "Attached to existing local branch: $BRANCH"
    elif git show-ref --verify --quiet "refs/remotes/origin/$BRANCH"; then
        git worktree add "$WORKTREE_DIR/repo" "$BRANCH"
        echo "Attached to remote branch: origin/$BRANCH"
    else
        git worktree add -b "$BRANCH" "$WORKTREE_DIR/repo"
        echo "Created new branch: $BRANCH"
    fi
fi

# 構造検証
echo ""
echo "Validating structure..."
"$SCRIPT_DIR/validate.sh" "$PROJECT"

echo ""
echo "Done! Created: $WORKTREE_DIR"
echo ""
echo "Next: cd $WORKTREE_DIR/repo"
