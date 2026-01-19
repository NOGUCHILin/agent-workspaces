#!/bin/bash
set -e

# テンプレートから更新を取り込むスクリプト
# 使い方: claude-workspace/.claude/scripts/sync-from-template.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TEMPLATE_REPO="https://github.com/NOGUCHILin/claude-code-worktrees.git"
TEMP_DIR=$(mktemp -d)

# クリーンアップ
cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

echo "=== Syncing from template repository ==="

# 1. テンプレートリポジトリをclone
echo "Fetching template..."
git clone --depth 1 "$TEMPLATE_REPO" "$TEMP_DIR"

# 2. 同期対象（projects/は除外）
SYNC_TARGETS=(
    "claude-workspace/.claude"
    "claude-workspace/CLAUDE.md"
    "docs"
    "_shared"
    ".mcp.json.example"
)

# 3. 各ファイルを同期
echo "Syncing files..."
for target in "${SYNC_TARGETS[@]}"; do
    if [ -e "$TEMP_DIR/$target" ]; then
        # 親ディレクトリを作成
        mkdir -p "$WORKSPACE_ROOT/$(dirname "$target")"
        # 既存を削除してコピー
        rm -rf "$WORKSPACE_ROOT/$target"
        cp -r "$TEMP_DIR/$target" "$WORKSPACE_ROOT/$target"
        echo "  ✓ $target"
    fi
done

# 4. .mcp.jsonは上書きしない（ユーザー設定を保持）
if [ ! -f "$WORKSPACE_ROOT/claude-workspace/.mcp.json" ]; then
    cp "$TEMP_DIR/claude-workspace/.mcp.json" "$WORKSPACE_ROOT/claude-workspace/.mcp.json"
    echo "  ✓ claude-workspace/.mcp.json (new)"
else
    echo "  - claude-workspace/.mcp.json (preserved)"
fi

echo ""
echo "=== Sync complete ==="
echo "Note: projects/ was not modified"
echo ""
echo "Review changes with: git status"
echo "Commit with: git add -A && git commit -m 'sync: update from template'"
