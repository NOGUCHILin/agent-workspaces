#!/bin/bash
# 既存worktreeに.mcp.jsonを追加
set -e

BRANCH="$1"

if [[ -z "$BRANCH" ]]; then
  echo "Usage: $0 <branch-name>"
  echo "Run from repos/<repo-name>/ directory"
  exit 1
fi

# 現在のディレクトリからリポジトリ名とユーザー名を取得
if [[ ! -d ".bare" ]]; then
  echo "Error: Must be run from repos/<repo-name>/ directory"
  exit 1
fi

REPO_NAME=$(basename "$(pwd)")
USERNAME=$(basename "$(dirname "$(dirname "$(pwd)")")")

WORKTREE_PATH="worktrees/$BRANCH"

if [[ ! -d "$WORKTREE_PATH" ]]; then
  echo "Error: Worktree does not exist: $WORKTREE_PATH"
  exit 1
fi

PROFILE_NAME="${USERNAME}-${REPO_NAME}-${BRANCH}"

cat > "$WORKTREE_PATH/.mcp.json" << EOF
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    },
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@0.0.54",
        "--user-data-dir=/Users/${USERNAME}/.playwright-profiles/${PROFILE_NAME}"
      ]
    }
  }
}
EOF

echo "Created: $WORKTREE_PATH/.mcp.json"
echo "Profile: /Users/${USERNAME}/.playwright-profiles/${PROFILE_NAME}"
