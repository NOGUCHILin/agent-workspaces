#!/bin/bash
# ワークスペースにリポジトリを追加（worktree構造で）
set -e

REPO_URL="$1"
BRANCH="${2:-main}"

if [[ -z "$REPO_URL" ]]; then
  echo "Usage: $0 <repo-url> [branch]"
  exit 1
fi

# リポジトリ名を抽出
REPO_NAME=$(basename "$REPO_URL" .git)

# 現在のワークスペースディレクトリを確認
if [[ ! -d "repos" ]]; then
  echo "Error: Must be run from a workspace directory (workspaces/<username>/)"
  exit 1
fi

REPO_DIR="repos/$REPO_NAME"

if [[ -d "$REPO_DIR" ]]; then
  echo "Error: Repository already exists: $REPO_DIR"
  exit 1
fi

mkdir -p "$REPO_DIR"
cd "$REPO_DIR"

# bareリポジトリとしてclone
git clone --bare "$REPO_URL" .bare

# worktreesディレクトリ作成
mkdir -p worktrees

# デフォルトブランチのworktreeを作成
git --git-dir=.bare worktree add "worktrees/$BRANCH" "$BRANCH"

echo ""
echo "Repository added: $REPO_DIR"
echo "Worktree created: $REPO_DIR/worktrees/$BRANCH"
echo ""
echo "To create a new worktree:"
echo "  cd $REPO_DIR"
echo "  git --git-dir=.bare worktree add worktrees/<branch-name> -b <branch-name>"
