#!/bin/bash
set -e

# テンプレートリポジトリ同期スクリプト
# 使い方: .claude/skills/sync-template/sync-to-template.sh "コミットメッセージ"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
CLAUDE_WORKSPACE="$WORKSPACE_ROOT/claude-workspace"
TEMPLATE_REPO="https://github.com/NOGUCHILin/claude-code-worktrees.git"
TEMP_DIR=$(mktemp -d)

MESSAGE=${1:-"sync: update from my-claude-code-worktrees"}
FORCE=${2:-""}  # --force で確認スキップ

# クリーンアップ
cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

echo "=== Syncing to template repository ==="

# 1. テンプレートリポジトリをclone
echo "Cloning template repository..."
git clone --depth 1 "$TEMPLATE_REPO" "$TEMP_DIR"

# 2. 同期対象ファイル/ディレクトリ（claude-workspaceからコピー）
SYNC_TARGETS_FROM_CLAUDE_WORKSPACE=(
    ".claude/skills/manage-workspace"
    ".claude/skills/sync-template"
    ".claude/skills/check-status"
    ".claude/scripts"
    ".claude/rules"
    "CLAUDE.md"
    ".mcp.json"
)

# ワークスペースルートからコピー
SYNC_TARGETS_FROM_ROOT=(
    "docs"
    "_shared"
    ".mcp.json.example"
    ".gitignore"
    "package.json"
)

# 3. 既存ファイルを削除（同期対象のみ）
echo "Preparing sync targets..."
for target in "${SYNC_TARGETS_FROM_CLAUDE_WORKSPACE[@]}"; do
    rm -rf "$TEMP_DIR/$target"
done
for target in "${SYNC_TARGETS_FROM_ROOT[@]}"; do
    rm -rf "$TEMP_DIR/$target"
done

# 4. ファイルをコピー（claude-workspaceから）
echo "Copying files from claude-workspace..."
for target in "${SYNC_TARGETS_FROM_CLAUDE_WORKSPACE[@]}"; do
    if [ -e "$CLAUDE_WORKSPACE/$target" ]; then
        mkdir -p "$TEMP_DIR/$(dirname "$target")"
        cp -r "$CLAUDE_WORKSPACE/$target" "$TEMP_DIR/$target"
        echo "  Copied: $target"
    fi
done

# 5. ファイルをコピー（ワークスペースルートから）
echo "Copying files from workspace root..."
for target in "${SYNC_TARGETS_FROM_ROOT[@]}"; do
    if [ -e "$WORKSPACE_ROOT/$target" ]; then
        mkdir -p "$TEMP_DIR/$(dirname "$target")"
        cp -r "$WORKSPACE_ROOT/$target" "$TEMP_DIR/$target"
        echo "  Copied: $target"
    fi
done

# 6. projects/は含めない（空のREADMEのみ）
mkdir -p "$TEMP_DIR/projects"
cat > "$TEMP_DIR/projects/README.md" << 'EOF'
# Projects

このディレクトリにプロジェクトを作成します。

## 使い方

```bash
.claude/skills/manage-workspace/scripts/setup.sh <project-name> <branch> <repo-url>
```

詳細は [docs/SETUP.md](../docs/SETUP.md) を参照。
EOF

# 7. コミット＆プッシュ
cd "$TEMP_DIR"
git add -A

if git diff --cached --quiet; then
    echo "No changes to sync."
    exit 0
fi

git commit -m "$MESSAGE

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

echo ""
echo "Changes to be pushed:"
git log -1 --stat

echo ""
if [[ "$FORCE" == "--force" ]]; then
    git push origin master
    echo "✓ Pushed to template repository"
else
    read -p "Push to template repository? (y/N): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        git push origin master
        echo "✓ Pushed to template repository"
    else
        echo "Aborted. Changes are in: $TEMP_DIR"
        trap - EXIT  # クリーンアップを無効化
    fi
fi
