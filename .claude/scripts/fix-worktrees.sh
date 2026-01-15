#!/bin/bash
set -e

# 既存worktreeのsymlink/設定を修正するスクリプト
# 使い方: .claude/scripts/fix-worktrees.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== Fixing existing worktrees ==="

for project_dir in "$WORKSPACE_ROOT"/projects/*/; do
    project=$(basename "$project_dir")

    # .bareディレクトリがあるプロジェクトのみ処理
    if [ ! -d "$project_dir/.bare" ]; then
        continue
    fi

    echo ""
    echo "Project: $project"

    for worktree_dir in "$project_dir"/worktrees/*/; do
        if [[ "$worktree_dir" == *".venv"* ]] || [[ "$worktree_dir" == *".bare"* ]]; then
            continue
        fi

        branch=$(basename "$worktree_dir")
        claude_dir="$worktree_dir/.claude"

        # .claudeディレクトリがなければ作成
        mkdir -p "$claude_dir"

        # symlinkを修正（正しいパス: ../../.claude/）
        # 既存のディレクトリも削除（-rf）
        rm -rf "$claude_dir/rules" "$claude_dir/skills" "$claude_dir/scripts" 2>/dev/null || true
        ln -sf "../../.claude/rules" "$claude_dir/rules"
        ln -sf "../../.claude/skills" "$claude_dir/skills"
        ln -sf "../../../../.claude/scripts" "$claude_dir/scripts"

        # settings.jsonがなければ作成
        if [ ! -f "$claude_dir/settings.json" ] || [ "$(cat "$claude_dir/settings.json" 2>/dev/null)" = "{}" ]; then
            echo '{"hooks": {}}' > "$claude_dir/settings.json"
        fi

        echo "  ✅ $branch"
    done
done

echo ""
echo "=== Done ==="
