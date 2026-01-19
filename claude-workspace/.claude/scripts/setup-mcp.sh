#!/bin/bash
set -e

# ワークツリーに.mcp.jsonを設定するスクリプト
# 使い方: .claude/scripts/setup-mcp.sh [worktree-path]
# 引数なしで全ワークツリーに設定

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TEMPLATE="$WORKSPACE_ROOT/claude-workspace/.claude/skills/manage-workspace/templates/.mcp.json"

setup_mcp() {
    local worktree_path="$1"
    local branch=$(basename "$worktree_path")
    local mcp_file="$worktree_path/.mcp.json"

    # 既存ファイルがあり、--isolatedが設定済みならスキップ
    if [ -f "$mcp_file" ] && grep -q '"--isolated"' "$mcp_file" 2>/dev/null; then
        echo "✅ $branch (設定済み)"
        return 0
    fi

    # テンプレートから生成
    sed -e "s|{{HOME}}|$HOME|g" -e "s|{{BRANCH}}|$branch|g" "$TEMPLATE" > "$mcp_file"
    echo "📝 $branch (設定完了)"
}

if [ -n "$1" ]; then
    # 特定のworktreeのみ
    setup_mcp "$1"
else
    # 全worktree
    echo "=== 全ワークツリーにMCP設定 ==="
    for dir in "$WORKSPACE_ROOT"/projects/*/worktrees/*/; do
        if [[ "$dir" != *".bare"* ]] && [[ "$dir" != *".venv"* ]] && [ -d "$dir" ]; then
            setup_mcp "$dir"
        fi
    done
    echo "=== 完了 ==="
fi
